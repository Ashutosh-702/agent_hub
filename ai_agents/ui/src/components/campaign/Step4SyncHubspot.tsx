import { useEffect, useMemo, useState } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';
import { useLazyGetCampaignContactListQuery, useLazyGetHubspotSyncCandidatesQuery } from '../../store';

// Feature flag to enable/disable selection functionality
const ENABLE_SELECTION = false;

interface CompanyWithContacts {
  id: string;
  name: string;
  industry: string;
  location: string;
  contacts: Contact[];
  isSelected: boolean;
  isSynced: boolean;
  isSyncing: boolean;
}

export const Step4SyncHubspot = () => {
  const { state, nextStep, prevStep, setQualifiedCompanies, setQualifiedContacts } = useCampaignWizard();

  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncComplete, setSyncComplete] = useState(false);
  const [didHydrateFromApi, setDidHydrateFromApi] = useState(false);

  const campaignId = state.campaignId;
  const [fetchHubspotSyncCandidates] = useLazyGetHubspotSyncCandidatesQuery();
  const [fetchCampaignContactList] = useLazyGetCampaignContactListQuery();

  const contacts = state.qualifiedContacts;

  // Hydrate Step 4 list from backend (enriched contacts source of truth).
  // We only do this once to avoid resetting selection state while user interacts.
  useEffect(() => {
    if (!campaignId || didHydrateFromApi) return;

    let cancelled = false;
    const limit = 100;

    const run = async () => {
      try {
        const fetchRelevantFromCampaignContactList = async () => {
          const allFromCampaignList: Array<{
            contact_id: string;
            company_id?: string | null;
            company_name: string;
            first_name: string;
            last_name: string;
            designation: string;
            is_relevant?: boolean;
            email: string | null;
            phone: string | null;
          }> = [];

          let p = 1;
          let has = true;
          let fetched = 0;
          const MAX = 100;

          while (has && fetched < MAX) {
            fetched += 1;
            const res = await fetchCampaignContactList({ campaign_id: campaignId, page: p, limit }).unwrap();
            const contacts = res.data?.contacts ?? [];

            // Strictly keep only relevant contacts.
            const relevant = contacts.filter((c) => c.is_relevant === true);

            allFromCampaignList.push(
              ...relevant.map((c) => ({
                contact_id: c.contact_id,
                company_id: c.company_id,
                company_name: c.contact_data?.company || 'Unknown Company',
                first_name: c.contact_data?.firstname || '',
                last_name: c.contact_data?.lastname || '',
                designation: c.contact_data?.jobtitle || '',
                is_relevant: c.is_relevant,
                email: (c.contact_data?.email && c.contact_data.email[0]) || null,
                phone: (c.contact_data?.phone && c.contact_data.phone[0]) || null,
              }))
            );

            has = res.pagination?.has_next ?? false;
            p += 1;
          }

          return allFromCampaignList;
        };

        const allContacts: Array<{
          contact_id: string;
          company_id?: string | null;
          company_name: string;
          first_name: string;
          last_name: string;
          designation: string;
          is_relevant?: boolean;
          email: string | null;
          phone: string | null;
        }> = [];

        let page = 1;
        let hasNext = true;
        let pagesFetched = 0;
        const MAX_PAGES = 100; // safety cap

        try {
          while (hasNext && pagesFetched < MAX_PAGES) {
            pagesFetched += 1;
            const res = await fetchHubspotSyncCandidates({ campaign_id: campaignId, page, limit }).unwrap();
            // Only keep contacts that are relevant (is_relevant=true).
            // Be tolerant if backend sends it as a string.
            allContacts.push(
              ...(res.data?.contacts ?? []).filter((c) => {
                const v = (c as { is_relevant?: unknown }).is_relevant;
                if (typeof v === 'string') return v.toLowerCase() === 'true';
                return v === true;
              })
            );
            hasNext = res.pagination?.has_next ?? false;
            page += 1;
          }
        } catch {
          // hubspot_sync_candidates is not implemented (or failed). Fall back to get_campaign_contact_list.
          const fallback = await fetchRelevantFromCampaignContactList();
          allContacts.push(...fallback);
        }

        // If the candidates endpoint is missing or returns nothing usable, fall back to
        // get_campaign_contact_list (which includes is_relevant) and filter is_relevant=true.
        if (allContacts.length === 0) {
          const fallback = await fetchRelevantFromCampaignContactList();
          allContacts.push(...fallback);
        }

        if (cancelled) return;

        // Preserve any existing syncStatus the user may have already set (if any)
        const existingStatus = new Map<string, Contact['syncStatus']>();
        state.qualifiedContacts.forEach((c) => {
          if (c.syncStatus) existingStatus.set(c.id, c.syncStatus);
        });

        // Ensure companies exist in wizard state so grouping works
        const existingCompaniesById = new Map(state.qualifiedCompanies.map((c) => [c.id, c]));
        const mergedCompanies: Company[] = [...state.qualifiedCompanies];

        for (const c of allContacts) {
          const resolvedCompanyId = c.company_id || c.company_name || 'unknown_company';
          if (!existingCompaniesById.has(resolvedCompanyId)) {
            const newCompany: Company = {
              id: resolvedCompanyId,
              name: c.company_name,
              industry: '',
              employeeCount: '',
              revenue: '',
              location: '',
              website: '',
              contacts: [],
              syncStatus: 'not_synced',
              isQualified: true,
              qualificationStatus: 'qualified',
            };
            existingCompaniesById.set(resolvedCompanyId, newCompany);
            mergedCompanies.push(newCompany);
          }
        }

        // All contacts are pre-selected by default (ready to sync)
        const mappedContacts: Contact[] = allContacts.map((c) => ({
          id: c.contact_id,
          companyId: c.company_id || c.company_name || 'unknown_company',
          companyName: c.company_name,
          firstName: c.first_name || '',
          lastName: c.last_name || '',
          jobTitle: c.designation || '',
          email: c.email || '',
          phone: c.phone || undefined,
          qualificationStatus: 'qualified',
          // Pre-select all contacts by default
          syncStatus: existingStatus.get(c.contact_id) ?? 'selected',
          personalization: {
            messageStatus: 'pending',
            deckStatus: 'pending',
          },
        }));

        setQualifiedCompanies(mergedCompanies);
        setQualifiedContacts(mappedContacts);
        setDidHydrateFromApi(true);
      } catch {
        // If everything fails, fall back to existing wizard state.
        setDidHydrateFromApi(true);
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [
    campaignId,
    didHydrateFromApi,
    fetchCampaignContactList,
    fetchHubspotSyncCandidates,
    setQualifiedCompanies,
    setQualifiedContacts,
    state.qualifiedCompanies,
    state.qualifiedContacts,
  ]);

  // Group contacts by company
  const companiesWithContacts = useMemo(() => {
    const companyMap = new Map<string, CompanyWithContacts>();
    
    contacts.forEach(contact => {
      // Step4 used to depend on qualifiedCompanies being populated; if it isn't,
      // we still want to render by grouping contacts using contact-level companyName/companyId.
      const companyFromState = state.qualifiedCompanies.find(c => c.id === contact.companyId);
      const companyId = companyFromState?.id || contact.companyId || contact.companyName || 'unknown_company';
      const companyName = companyFromState?.name || contact.companyName || 'Unknown Company';
      const companyIndustry = companyFromState?.industry || '';
      const companyLocation = companyFromState?.location || '';

      if (!companyMap.has(companyId)) {
        companyMap.set(companyId, {
          id: companyId,
          name: companyName,
          industry: companyIndustry,
          location: companyLocation,
          contacts: [],
          isSelected: false,
          isSynced: false,
          isSyncing: false,
        });
      }
      companyMap.get(companyId)!.contacts.push(contact);
    });

    // Calculate selection/sync status for each company
    companyMap.forEach((company) => {
      const allSynced = company.contacts.every(c => c.syncStatus === 'synced');
      const allSelected = company.contacts.every(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
      const anySyncing = company.contacts.some(c => c.syncStatus === 'syncing');
      
      company.isSynced = allSynced;
      company.isSelected = allSelected && !allSynced;
      company.isSyncing = anySyncing;
    });

    return Array.from(companyMap.values());
  }, [contacts, state.qualifiedCompanies]);

  const totalCompanies = companiesWithContacts.length;
  const totalContacts = contacts.length;
  const selectedCompaniesCount = companiesWithContacts.filter(c => c.isSelected || c.isSynced).length;
  const selectedContactsCount = contacts.filter(c => c.syncStatus === 'selected' || c.syncStatus === 'synced').length;
  const syncedCompaniesCount = companiesWithContacts.filter(c => c.isSynced).length;
  const syncedContactsCount = contacts.filter(c => c.syncStatus === 'synced').length;

  // Toggle company expansion
  const toggleExpandCompany = (companyId: string) => {
    setExpandedCompanies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(companyId)) {
        newSet.delete(companyId);
      } else {
        newSet.add(companyId);
      }
      return newSet;
    });
  };

  // Toggle company selection (selects all contacts in company)
  // Only works when ENABLE_SELECTION is true
  const toggleCompanySelection = (companyId: string) => {
    if (!ENABLE_SELECTION) return;
    
    const company = companiesWithContacts.find(c => c.id === companyId);
    if (!company || company.isSynced) return;

    const contactIds = company.contacts.map(c => c.id);
    const newStatus: Contact['syncStatus'] = company.isSelected ? 'not_synced' : 'selected';

    setQualifiedContacts(contacts.map(c => 
      contactIds.includes(c.id) 
        ? { ...c, syncStatus: newStatus }
        : c
    ));
  };

  // Select/Deselect all companies
  // Only works when ENABLE_SELECTION is true
  const handleSelectAll = () => {
    if (!ENABLE_SELECTION) return;
    
    const allSelected = companiesWithContacts.every(c => c.isSelected || c.isSynced);
    const newStatus: Contact['syncStatus'] = allSelected ? 'not_synced' : 'selected';
    
    setQualifiedContacts(contacts.map(c => ({
      ...c,
      syncStatus: c.syncStatus === 'synced' ? 'synced' : newStatus,
    })));
  };

  const allSelected = companiesWithContacts.length > 0 && companiesWithContacts.every(c => c.isSelected || c.isSynced);
  const someSelected = companiesWithContacts.some(c => c.isSelected || c.isSynced) && !allSelected;

  const handleSyncSelected = async () => {
    const selectedContactIds = contacts.filter(c => c.syncStatus === 'selected').map(c => c.id);
    if (selectedContactIds.length === 0) return;

    setIsSyncing(true);
    
    // Set syncing status
    setQualifiedContacts(contacts.map(c => 
      selectedContactIds.includes(c.id) 
        ? { ...c, syncStatus: 'syncing' as const }
        : c
    ));

    // Simulate sync completion
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setQualifiedContacts(contacts.map(c => 
      selectedContactIds.includes(c.id) 
        ? { ...c, syncStatus: 'synced' as const }
        : c
    ));
    
    setIsSyncing(false);
    setSyncComplete(true);
  };

  const handleContinue = () => {
    // Keep only synced contacts for next step
    const synced = contacts.filter(c => c.syncStatus === 'synced');
    setQualifiedContacts(synced);
    nextStep();
  };

  return (
    <div className="step-container step-sync-hubspot">
      <div className="step-header">
        <h2>Review & Sync to HubSpot</h2>
        <p>Review the qualified contacts before syncing to your CRM</p>
      </div>

      {/* Stats Bar */}
      <div className="sync-stats">
        <div className="stat">
          <span className="stat-value">{totalCompanies}</span>
          <span className="stat-label">Companies</span>
        </div>
        <div className="stat">
          <span className="stat-value">{totalContacts}</span>
          <span className="stat-label">Contacts</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{selectedCompaniesCount}</span>
          <span className="stat-label">Companies Selected</span>
        </div>
        {syncedContactsCount > 0 && (
          <div className="stat success">
            <span className="stat-value">{syncedContactsCount}</span>
            <span className="stat-label">Contacts Synced</span>
          </div>
        )}
      </div>

      {/* Sync Success Message */}
      {syncComplete && syncedContactsCount > 0 && (
        <div className="sync-success-banner">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>{syncedCompaniesCount} companies ({syncedContactsCount} contacts) successfully synced to HubSpot</span>
        </div>
      )}

      {/* Companies List with Select All Header */}
      <div className="sync-companies-list">
        {/* Select All Header */}
        <div className="select-all-header">
          <label className="checkbox-container">
            <input 
              type="checkbox" 
              checked={allSelected}
              ref={(el) => {
                if (el) el.indeterminate = someSelected;
              }}
              onChange={handleSelectAll}
              disabled={!ENABLE_SELECTION || syncComplete}
            />
            <span className="checkmark"></span>
          </label>
          <span className="select-all-text">
            {allSelected ? 'All Selected' : 'Select All'} 
            <span className="selected-count">({selectedCompaniesCount} of {totalCompanies} companies)</span>
          </span>
        </div>

        {/* Companies with Contacts */}
        {companiesWithContacts.map((company) => {
          const isExpanded = expandedCompanies.has(company.id);
          
          return (
            <div 
              key={company.id} 
              className={`sync-company-card ${company.isSelected ? 'selected' : ''} ${company.isSynced ? 'synced' : ''}`}
            >
              <div className="company-row" onClick={() => toggleExpandCompany(company.id)}>
                <div className="company-select">
                  <label className="checkbox-container" onClick={(e) => e.stopPropagation()}>
                    <input 
                      type="checkbox"
                      checked={company.isSelected || company.isSynced}
                      onChange={() => toggleCompanySelection(company.id)}
                      disabled={!ENABLE_SELECTION || company.isSynced}
                    />
                    <span className="checkmark"></span>
                  </label>
                </div>
                <div className="company-info">
                  <h4>{company.name}</h4>
                  <div className="company-meta">
                    {company.industry && <span className="tag">{company.industry}</span>}
                    {company.location && <span className="tag">{company.location}</span>}
                    <span className="contacts-count">{company.contacts.length} contacts</span>
                  </div>
                </div>
                {company.isSyncing && (
                  <div className="syncing-badge">
                    <div className="spinner small" />
                    Syncing...
                  </div>
                )}
                {company.isSynced && (
                  <div className="synced-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Synced
                  </div>
                )}
                {company.isSelected && !company.isSynced && !company.isSyncing && (
                  <div className="qualified-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                )}
                <button 
                  className="btn-icon expand-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleExpandCompany(company.id);
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>

              {/* Expanded Contacts */}
              {isExpanded && (
                <div className="company-contacts" onClick={(e) => e.stopPropagation()}>
                  <div className="contacts-header">
                    <h5>Contacts ({company.contacts.length})</h5>
                  </div>
                  <div className="contacts-list">
                    {company.contacts.map((contact) => (
                      <div key={contact.id} className={`contact-card ${contact.syncStatus === 'synced' ? 'synced' : ''}`}>
                        <div className="contact-avatar">
                          {contact.firstName[0] || '?'}{contact.lastName[0] || '?'}
                        </div>
                        <div className="contact-info">
                          <span className="contact-name">{contact.firstName} {contact.lastName}</span>
                          <span className="contact-title">{contact.jobTitle}</span>
                          <span className="contact-email">{contact.email}</span>
                        {contact.phone ? <span className="contact-phone">{contact.phone}</span> : null}
                        </div>
                        {contact.syncStatus === 'synced' && (
                          <span className="contact-synced-badge">✓</span>
                        )}
                        {contact.syncStatus === 'syncing' && (
                          <div className="spinner small" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="step-navigation">
        <button className="btn-secondary" onClick={prevStep}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>

        {!syncComplete ? (
          <button
            className="btn-primary btn-large"
            onClick={handleSyncSelected}
            disabled={selectedContactsCount === 0 || isSyncing}
          >
            {isSyncing ? (
              <>
                <div className="spinner" />
                Syncing to HubSpot...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/>
                </svg>
                Sync {selectedCompaniesCount} Companies ({selectedContactsCount} Contacts) to HubSpot
              </>
            )}
          </button>
        ) : (
          <button
            className="btn-primary btn-large"
            onClick={handleContinue}
          >
            Continue with {syncedCompaniesCount} Companies ({syncedContactsCount} Contacts)
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
