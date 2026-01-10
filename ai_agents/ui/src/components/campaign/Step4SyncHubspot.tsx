import { useEffect, useMemo, useState, useRef, useCallback } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';
import { useLazyGetContactListMinimalQuery, useLazyGetHubspotSyncCandidatesQuery, useSyncToHubspotMutation, useLazyGetHubspotSyncProgressQuery } from '../../store';
import { ExportContactsModal } from './ExportContactsModal';

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

// Maximum pages to fetch from backend - limits memory usage
const MAX_BACKEND_PAGES = 2;
// Items per page in UI - for pagination display  
const UI_PAGE_SIZE = 20;

export const Step4SyncHubspot = () => {
  const { state, nextStep, prevStep, setQualifiedCompanies, setQualifiedContacts } = useCampaignWizard();

  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncComplete, setSyncComplete] = useState(false);
  const [didHydrateFromApi, setDidHydrateFromApi] = useState(false);
  const [syncProgress, setSyncProgress] = useState<{ total: number; synced: number; status: string } | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const selectedContactIdsRef = useRef<string[]>([]);
  
  // UI Pagination state - to avoid rendering too many items at once
  const [currentPage, setCurrentPage] = useState(1);
  
  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);

  const campaignId = state.campaignId;
  const [fetchHubspotSyncCandidates] = useLazyGetHubspotSyncCandidatesQuery();
  // OPTIMIZED: Use minimal contact list API instead of heavy full contact list
  const [fetchContactListMinimal] = useLazyGetContactListMinimalQuery();
  const [syncToHubspot] = useSyncToHubspotMutation();
  const [fetchHubspotSyncProgress] = useLazyGetHubspotSyncProgressQuery();

  const contacts = state.qualifiedContacts;

  // Hydrate Step 4 list from backend (enriched contacts source of truth).
  // We only do this once to avoid resetting selection state while user interacts.
  useEffect(() => {
    if (!campaignId || didHydrateFromApi) return;

    let cancelled = false;
    const limit = 100;

    const run = async () => {
      try {
        // OPTIMIZED: Use minimal contact list API - much smaller payload
        const fetchRelevantFromContactListMinimal = async () => {
          const allFromContactList: Array<{
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

          // Limit to MAX_BACKEND_PAGES to prevent memory bloat
          while (has && fetched < MAX_BACKEND_PAGES) {
            fetched += 1;
            // Use minimal API - returns only essential fields
            const res = await fetchContactListMinimal({ campaign_id: campaignId, page: p, limit }).unwrap();
            const contacts = res.data?.contacts ?? [];

            // Strictly keep only relevant contacts.
            const relevant = contacts.filter((c) => c.is_relevant === true);

            // Map from minimal API structure (flat fields, not nested contact_data)
            allFromContactList.push(
              ...relevant.map((c) => ({
                contact_id: c.contact_id,
                company_id: c.company_id,
                company_name: c.company || 'Unknown Company',
                first_name: c.firstname || '',
                last_name: c.lastname || '',
                designation: c.jobtitle || '',
                is_relevant: c.is_relevant,
                email: c.email || null,
                phone: c.phone || null,
              }))
            );

            has = res.pagination?.has_next ?? false;
            p += 1;
          }

          return allFromContactList;
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

        try {
          // Limit to MAX_BACKEND_PAGES to prevent memory bloat
          while (hasNext && pagesFetched < MAX_BACKEND_PAGES) {
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
          // hubspot_sync_candidates is not implemented (or failed). Fall back to contact_list_minimal.
          const fallback = await fetchRelevantFromContactListMinimal();
          allContacts.push(...fallback);
        }

        // If the candidates endpoint is missing or returns nothing usable, fall back to
        // contact_list_minimal (which includes is_relevant) and filter is_relevant=true.
        if (allContacts.length === 0) {
          const fallback = await fetchRelevantFromContactListMinimal();
          allContacts.push(...fallback);
        }

        if (cancelled) return;

        // Only preserve 'synced' status - all other contacts should be pre-selected
        const existingStatus = new Map<string, Contact['syncStatus']>();
        state.qualifiedContacts.forEach((c) => {
          // Only keep 'synced' status, reset others to 'selected'
          if (c.syncStatus === 'synced') {
            existingStatus.set(c.id, 'synced');
          }
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
    fetchContactListMinimal,
    fetchHubspotSyncCandidates,
    setQualifiedCompanies,
    setQualifiedContacts,
    state.qualifiedCompanies,
    state.qualifiedContacts,
  ]);

  // Pre-build company lookup map for O(1) access (avoid O(n²))
  const companyLookup = useMemo(() => {
    const map = new Map<string, typeof state.qualifiedCompanies[0]>();
    state.qualifiedCompanies.forEach(c => map.set(c.id, c));
    return map;
  }, [state.qualifiedCompanies]);

  // Group contacts by company - optimized with O(1) lookups
  const companiesWithContacts = useMemo(() => {
    const companyMap = new Map<string, CompanyWithContacts>();
    
    contacts.forEach(contact => {
      // Use O(1) lookup instead of O(n) find
      const companyFromState = contact.companyId ? companyLookup.get(contact.companyId) : undefined;
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
  }, [contacts, companyLookup]);

  // Memoize stats to avoid recalculating on every render
  const { totalCompanies, totalContacts, selectedCompaniesCount, selectedContactsCount, syncedCompaniesCount, syncedContactsCount } = useMemo(() => {
    let selectedCompanies = 0, syncedCompanies = 0, selectedContacts = 0, syncedContacts = 0;
    
    companiesWithContacts.forEach(c => {
      if (c.isSelected || c.isSynced) selectedCompanies++;
      if (c.isSynced) syncedCompanies++;
    });
    
    contacts.forEach(c => {
      if (c.syncStatus === 'selected' || c.syncStatus === 'synced') selectedContacts++;
      if (c.syncStatus === 'synced') syncedContacts++;
    });
    
    return {
      totalCompanies: companiesWithContacts.length,
      totalContacts: contacts.length,
      selectedCompaniesCount: selectedCompanies,
      selectedContactsCount: selectedContacts,
      syncedCompaniesCount: syncedCompanies,
      syncedContactsCount: syncedContacts,
    };
  }, [companiesWithContacts, contacts]);

  // Paginate companies for UI display - prevents rendering too many items
  const totalPages = Math.ceil(companiesWithContacts.length / UI_PAGE_SIZE);
  const paginatedCompanies = useMemo(() => {
    const start = (currentPage - 1) * UI_PAGE_SIZE;
    return companiesWithContacts.slice(start, start + UI_PAGE_SIZE);
  }, [companiesWithContacts, currentPage]);

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

  // Pre-build company-with-contacts lookup for O(1) access
  const companyWithContactsLookup = useMemo(() => {
    const map = new Map<string, CompanyWithContacts>();
    companiesWithContacts.forEach(c => map.set(c.id, c));
    return map;
  }, [companiesWithContacts]);

  // Toggle company selection (selects all contacts in company)
  // Only works when ENABLE_SELECTION is true
  const toggleCompanySelection = (companyId: string) => {
    if (!ENABLE_SELECTION) return;
    
    // Use O(1) lookup instead of O(n) find
    const company = companyWithContactsLookup.get(companyId);
    if (!company || company.isSynced) return;

    // Use Set for O(1) lookup instead of O(n) includes
    const contactIdSet = new Set(company.contacts.map(c => c.id));
    const newStatus: Contact['syncStatus'] = company.isSelected ? 'not_synced' : 'selected';

    setQualifiedContacts(contacts.map(c => 
      contactIdSet.has(c.id) 
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

  // Track if initial status check has been done to prevent re-running
  const initialStatusCheckedRef = useRef(false);
  // Keep current contacts in ref to avoid dependency issues in callbacks
  const contactsRef = useRef(contacts);
  contactsRef.current = contacts;

  // Poll campaign status to check sync progress
  // Uses refs to avoid re-creating callback on every contacts change
  const pollCampaignStatus = useCallback(async () => {
    if (!campaignId) return;

    try {
      const res = await fetchHubspotSyncProgress({ campaign_id: campaignId }).unwrap();
      const data = res.data;
      const status = data?.prospecting_cycle?.status;
      const syncedCount = data?.synced_hubspot_companies_count ?? 0;
      const totalCount = data?.total_hubspot_companies_count ?? totalCompanies;

      if (status === 'hubspot_sync_completed') {
        // Sync completed successfully
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsSyncing(false);
        setSyncComplete(true);
        setSyncProgress({ total: totalCount, synced: totalCount, status: 'Completed' });
        
        // Mark all selected contacts as synced (use ref for current contacts)
        setQualifiedContacts(contactsRef.current.map(c => 
          selectedContactIdsRef.current.includes(c.id) 
            ? { ...c, syncStatus: 'synced' as const }
            : c
        ));
      } else if (status === 'hubspot_sync_failed') {
        // Sync failed
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setSyncError('HubSpot sync failed. Please try again.');
        setIsSyncing(false);
        setSyncProgress(null);
        
        // Reset to selected status (use ref for current contacts)
        setQualifiedContacts(contactsRef.current.map(c => 
          selectedContactIdsRef.current.includes(c.id) 
            ? { ...c, syncStatus: 'selected' as const }
            : c
        ));
      } else if (status === 'hubspot_sync_in_progress') {
        // Still syncing - update progress display with actual counts
        setSyncProgress({ 
          total: totalCount, 
          synced: syncedCount, 
          status: 'Syncing to HubSpot...' 
        });
      }
    } catch (error) {
      console.error('Failed to poll campaign status:', error);
      // Continue polling on error
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, fetchHubspotSyncProgress, setQualifiedContacts, totalCompanies]); // Removed contacts from deps

  // Check campaign sync status on mount - resume polling if sync is in progress
  // NOTE: Minimal dependencies to prevent infinite loops
  useEffect(() => {
    if (!campaignId || !didHydrateFromApi) return;
    // Only run once after hydration
    if (initialStatusCheckedRef.current) return;
    initialStatusCheckedRef.current = true;

    let cancelled = false;

    const checkInitialStatus = async () => {
      try {
        const res = await fetchHubspotSyncProgress({ campaign_id: campaignId }).unwrap();
        const data = res.data;
        const status = data?.prospecting_cycle?.status;
        const syncedCount = data?.synced_hubspot_companies_count ?? 0;
        const totalCount = data?.total_hubspot_companies_count ?? 0;

        if (cancelled) return;

        if (status === 'hubspot_sync_in_progress') {
          // Sync is in progress - start polling
          setIsSyncing(true);
          setSyncProgress({ 
            total: totalCount, 
            synced: syncedCount, 
            status: 'Syncing to HubSpot...' 
          });
          
          // Store all contact IDs as selected for when sync completes (use ref)
          selectedContactIdsRef.current = contactsRef.current.map(c => c.id);
          
          // Set contacts to syncing status
          setQualifiedContacts(contactsRef.current.map(c => ({ ...c, syncStatus: 'syncing' as const })));
          
          // Start polling - only if not already polling
          if (!pollIntervalRef.current) {
            pollIntervalRef.current = setInterval(() => {
              pollCampaignStatus();
            }, 3000);
          }
        } else if (status === 'hubspot_sync_completed') {
          // Sync already completed
          setSyncComplete(true);
          setSyncProgress({ total: totalCount, synced: totalCount, status: 'Completed' });
          setQualifiedContacts(contactsRef.current.map(c => ({ ...c, syncStatus: 'synced' as const })));
        } else if (status === 'hubspot_sync_failed') {
          // Sync failed
          setSyncError('HubSpot sync failed. Please try again.');
        }
      } catch (error) {
        console.error('Failed to check initial sync status:', error);
      }
    };

    checkInitialStatus();

    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, didHydrateFromApi]); // Minimal deps - runs once after hydration

  const handleSyncSelected = async () => {
    if (!campaignId || totalCompanies === 0) return;

    const selectedContactIds = contacts.filter(c => c.syncStatus === 'selected').map(c => c.id);
    if (selectedContactIds.length === 0) return;

    // Store selected contact IDs in ref for use in polling callback
    selectedContactIdsRef.current = selectedContactIds;

    setIsSyncing(true);
    setSyncError(null);
    setSyncProgress({ total: totalCompanies, synced: 0, status: 'Starting sync...' });
    
    // Set syncing status
    setQualifiedContacts(contacts.map(c => 
      selectedContactIds.includes(c.id) 
        ? { ...c, syncStatus: 'syncing' as const }
        : c
    ));

    try {
      // Call real API to initiate sync
      await syncToHubspot({ campaign_id: campaignId }).unwrap();

      // Start polling for campaign status
      setSyncProgress({ total: totalCompanies, synced: 0, status: 'Syncing to HubSpot...' });
      
      // Poll every 3 seconds
      pollIntervalRef.current = setInterval(() => {
        pollCampaignStatus();
      }, 3000);

      // Also do an immediate poll
      pollCampaignStatus();
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncError('Failed to initiate HubSpot sync. Please try again.');
      setIsSyncing(false);
      setSyncProgress(null);
      
      // Reset to selected status
    setQualifiedContacts(contacts.map(c => 
      selectedContactIds.includes(c.id) 
          ? { ...c, syncStatus: 'selected' as const }
        : c
    ));
    }
  };

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleContinue = () => {
    // Keep only synced contacts for next step
    const synced = contacts.filter(c => c.syncStatus === 'synced');
    setQualifiedContacts(synced);
    nextStep();
  };

  return (
    <div className="step-container step-sync-hubspot">
      <div className="step-header">
        <div className="step-header-content">
          <h2>Review & Sync to HubSpot</h2>
          <p>Review the qualified contacts before syncing to your CRM</p>
        </div>
        <button
          className="btn-secondary export-btn"
          onClick={() => setShowExportModal(true)}
          disabled={!campaignId || totalContacts === 0}
          title="Export contacts to CSV"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export CSV
        </button>
      </div>

      {/* Export Modal */}
      <ExportContactsModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        campaignId={campaignId || ''}
      />

      {/* Sync Progress Bar */}
      {syncProgress && (
        <div className="sync-progress-container">
          <div className="sync-progress-header">
            <span className="sync-progress-status">
              {!syncComplete && <div className="spinner small" />}
              {syncProgress.status || 'Syncing to HubSpot...'}
            </span>
            <span>{syncProgress.synced} / {syncProgress.total} companies synced</span>
          </div>
          <div className="sync-progress-bar">
            <div 
              className={`sync-progress-fill ${syncProgress.total > 0 && syncProgress.synced > 0 ? '' : 'sync-progress-indeterminate'}`}
              style={syncProgress.total > 0 && syncProgress.synced > 0 ? { width: `${(syncProgress.synced / syncProgress.total) * 100}%` } : undefined}
            />
          </div>
        </div>
      )}

      {/* Sync Error Message */}
      {syncError && (
        <div className="sync-error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>{syncError}</span>
          <button className="btn-text" onClick={() => setSyncError(null)}>Dismiss</button>
        </div>
      )}

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

        {/* Companies with Contacts - paginated for performance */}
        {paginatedCompanies.map((company) => {
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
                          <span className="contact-syncing-badge">Syncing</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="pagination-controls" style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '16px', 
            padding: '16px',
            marginTop: '16px'
          }}>
            <button 
              className="btn-secondary"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              style={{ minWidth: '100px' }}
            >
              Previous
            </button>
            <span style={{ color: 'var(--color-gray-600)' }}>
              Page {currentPage} of {totalPages} ({totalCompanies} companies total)
            </span>
            <button 
              className="btn-secondary"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              style={{ minWidth: '100px' }}
            >
              Next
            </button>
          </div>
        )}
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
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/>
                </svg>
            {isSyncing ? 'Syncing to HubSpot...' : `Sync ${selectedCompaniesCount} Companies (${selectedContactsCount} Contacts) to HubSpot`}
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
