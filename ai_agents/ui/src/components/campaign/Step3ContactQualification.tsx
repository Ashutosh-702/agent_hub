import { useEffect, useState } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';
import {
  useEnrichApolloContactListMutation,
  useLazyGetCampaignContactListQuery,
  useUpdateApolloContactEnrichmentStatusMutation,
  useGetCampaignContactListQuery,
  type CampaignContactListItem,
} from '../../store';
import { skipToken } from '@reduxjs/toolkit/query';

// Check if campaign has already completed contact qualification based on prospecting_cycle.status
const isStepAlreadyCompleted = (cycleStatus?: string): boolean => {
  const completedStatuses = [
    'contact_enriched',
    'hubspot_sync_in_progress',
    'hubspot_sync_completed',
    'hubspot_sync_failed',
    'personalization_completed',
    'enrolled_to_sequence',
  ];
  return cycleStatus ? completedStatuses.includes(cycleStatus) : false;
};

export const Step3ContactQualification = () => {
  const { 
    state, 
    setContactQualificationMode, 
    qualifyContact, 
    bulkQualifyContacts, 
    nextStep, 
    prevStep,
    setLoading,
    setQualifiedContacts,
  } = useCampaignWizard();

  const campaignId = state.campaignId;
  const [isEnrichPolling, setIsEnrichPolling] = useState(false);
  const [enrichApolloContactList] = useEnrichApolloContactListMutation();
  const [updateApolloContactEnrichmentStatus] = useUpdateApolloContactEnrichmentStatusMutation();
  const [fetchCampaignContactList] = useLazyGetCampaignContactListQuery();

  // Query to check campaign status for detecting if step is already completed
  const { data: contactListData } = useGetCampaignContactListQuery(
    campaignId ? { campaign_id: campaignId, page: 1, limit: 100 } : skipToken
  );
  
  const campaignCycleStatus = contactListData?.data?.campaign?.prospecting_cycle?.status;
  const stepAlreadyCompleted = isStepAlreadyCompleted(campaignCycleStatus);
  const apiContacts = contactListData?.data?.contacts || [];

  const contacts = state.qualifiedContacts;
  const qualifiedCount = contacts.filter(c => c.qualificationStatus === 'qualified').length;

  // Get company name for a contact (prefer API-provided name)
  const getCompanyName = (contact: Contact) => {
    if (contact.companyName) return contact.companyName;
    const company = state.qualifiedCompanies.find(c => c.id === contact.companyId);
    return company?.name || 'Unknown Company';
  };

  // Toggle single contact qualification via checkbox
  const toggleContactQualification = (contactId: string) => {
    const contact = contacts.find(c => c.id === contactId);
    if (contact) {
      const isCurrentlyQualified = contact.qualificationStatus === 'qualified';
      qualifyContact(contactId, !isCurrentlyQualified);
    }
  };

  // Select/Deselect all contacts
  const handleSelectAll = () => {
    const allQualified = contacts.every(c => c.qualificationStatus === 'qualified');
    bulkQualifyContacts(contacts.map(c => c.id), !allQualified);
  };

  const allSelected = contacts.length > 0 && contacts.every(c => c.qualificationStatus === 'qualified');
  const someSelected = contacts.some(c => c.qualificationStatus === 'qualified') && !allSelected;

  const handleContinue = () => {
    // Before going to Step 4, queue contact enrichment and poll until campaign status becomes contact_enriched.
    if (!campaignId) {
      nextStep();
      return;
    }

    const selectedContactIds = contacts
      .filter((c) => c.qualificationStatus === 'qualified')
      .map((c) => c.id);

    if (selectedContactIds.length === 0) {
      // nothing selected; don't start enrichment chain
      return;
    }

    setLoading(true, 'Saving selected contacts…');
    void (async () => {
      try {
        // 1) Persist selected contact ids (is_relevant=true)
        await updateApolloContactEnrichmentStatus({
          campaign_id: campaignId,
          selection_type: 'selected',
          is_relevant: true,
          contact_ids: selectedContactIds,
        }).unwrap();

        // 2) Queue enrichment job
        await enrichApolloContactList({ campaign_id: campaignId, enrichment_status: true }).unwrap();
        setLoading(true, 'Enriching contacts from Apollo…');
        // 3) Start polling for contact_enriched
        setIsEnrichPolling(true);
      } catch (e) {
        setLoading(false);
        setIsEnrichPolling(false);
      }
    })();
  };

  // Poll get_campaign_contact_list until prospecting_cycle.status is contact_enriched,
  // then refresh contacts and advance to Step 4.
  useEffect(() => {
    if (!campaignId || !isEnrichPolling) return;

    let cancelled = false;
    const limit = 100;

    const poll = async () => {
      try {
        const first = await fetchCampaignContactList({ campaign_id: campaignId, page: 1, limit }).unwrap();
        const status = first?.data?.campaign?.prospecting_cycle?.status;
        if (status !== 'contact_enriched') return;

        // Fetch all contacts pages once enriched
        let page = 1;
        let hasNext = first.pagination?.has_next ?? false;
        const all: CampaignContactListItem[] = [];
        all.push(...(first.data?.contacts || []));

        let pagesFetched = 0;
        const MAX_PAGES = 50; // safety cap

        while (hasNext && pagesFetched < MAX_PAGES) {
          pagesFetched += 1;
          page += 1;
          const res = await fetchCampaignContactList({ campaign_id: campaignId, page, limit }).unwrap();
          all.push(...(res.data?.contacts || []));
          hasNext = res.pagination?.has_next ?? false;
        }

        if (cancelled) return;

        const mapped = all.map((c) => ({
          id: c.contact_id,
          companyId: c.company_id,
          companyName: c.contact_data?.company || undefined,
          firstName: c.contact_data?.firstname || '',
          lastName: c.contact_data?.lastname || '',
          email: (c.contact_data?.email && c.contact_data.email[0]) || '',
          phone: (c.contact_data?.phone && c.contact_data.phone[0]) || undefined,
          jobTitle: c.contact_data?.jobtitle || '',
          linkedinUrl: c.linkedin_data?.linkedin_url || undefined,
          qualificationStatus: 'pending' as const,
          syncStatus: 'not_synced' as const,
          personalization: {
            messageStatus: 'pending' as const,
            deckStatus: 'pending' as const,
          },
        })) as Contact[];

        setQualifiedContacts(mapped);
        setLoading(false);
        setIsEnrichPolling(false);
        nextStep();
      } catch (e) {
        // ignore transient errors during polling
      }
    };

    const interval = window.setInterval(() => {
      void poll();
    }, 3000);
    void poll();

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [campaignId, fetchCampaignContactList, isEnrichPolling, nextStep, setLoading, setQualifiedContacts]);

  return (
    <div className="step-container step-contact-qualification">
      <div className="step-header">
        <h2>Contact Qualification</h2>
        <p>Review and qualify contacts from your qualified companies</p>
      </div>

      {/* Loading Animation */}
      {state.isLoading && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation ai-animation">
              <div className="ai-brain">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div className="ai-pulse" />
            </div>
            <h3>{state.loadingMessage}</h3>
            <div className="loading-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill ai-progress" 
                  style={{ width: `${state.estimatedCount}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Selection - Show only if step not already completed and no mode selected */}
      {!state.contactQualificationMode && !stepAlreadyCompleted && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div 
              className="mode-card"
              onClick={() => setContactQualificationMode('manual')}
            >
              <div className="mode-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h4>Manual Qualification</h4>
              <p>Review each contact individually and decide if they qualify</p>
              <span className="mode-tag">Full Control</span>
            </div>
            <div 
              className="mode-card disabled"
            >
              <div className="mode-icon ai">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                  <path d="M12 8v8"/>
                  <path d="M5 12h14"/>
                  <circle cx="5" cy="12" r="2"/>
                  <circle cx="19" cy="12" r="2"/>
                  <circle cx="12" cy="19" r="2"/>
                </svg>
              </div>
              <h4>AI Qualification</h4>
              <p>Coming soon.</p>
              <span className="mode-tag ai">Soon</span>
            </div>
          </div>
        </div>
      )}

      {/* Step Already Completed - Show review mode */}
      {!state.contactQualificationMode && stepAlreadyCompleted && (
        <div className="step-completed-view">
          <div className="sync-success-banner" style={{ marginBottom: '24px' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>Contact Qualification Completed</span>
          </div>

          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{contactListData?.pagination?.total_records ?? apiContacts.length}</span>
              <span className="stat-label">Total Contacts</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">
                {apiContacts.filter(c => c.is_relevant).length}
              </span>
              <span className="stat-label">Qualified (this page)</span>
            </div>
          </div>

          {/* Show qualified contacts (read-only view) */}
          {apiContacts.length > 0 && (
            <div className="contacts-qualification-list">
              <div className="select-all-header">
                <span className="select-all-text">
                  Qualified Contacts (view only)
                </span>
              </div>

              {apiContacts.filter(c => c.is_relevant).slice(0, 10).map((c) => (
                <div key={c.contact_id} className="contact-qualification-card qualified" style={{ cursor: 'default' }}>
                  <div className="contact-avatar">
                    {c.contact_data?.firstname?.[0] || '?'}{c.contact_data?.lastname?.[0] || '?'}
                  </div>
                  <div className="contact-info">
                    <h4>{c.contact_data?.firstname || ''} {c.contact_data?.lastname || ''}</h4>
                    <div className="contact-meta">
                      <span className="job-title">{c.contact_data?.jobtitle || 'N/A'}</span>
                      <span className="company-name">{c.contact_data?.company || 'Unknown'}</span>
                    </div>
                    <span className="contact-email">{c.contact_data?.email?.[0] || 'No email'}</span>
                  </div>
                  <div className="qualified-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </div>
              ))}
              {apiContacts.filter(c => c.is_relevant).length > 10 && (
                <div style={{ padding: '12px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                  + {apiContacts.filter(c => c.is_relevant).length - 10} more contacts...
                </div>
              )}
            </div>
          )}

          <div className="step-navigation">
            <button className="btn-secondary" onClick={prevStep}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12 19 5 12 12 5"/>
              </svg>
              Back
            </button>
            <button className="btn-primary" onClick={nextStep}>
              Continue to Sync to HubSpot
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Manual Qualification */}
      {state.contactQualificationMode === 'manual' && (
        <div className="manual-qualification">
          {/* Stats Bar */}
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{contacts.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">{qualifiedCount}</span>
              <span className="stat-label">Selected</span>
            </div>
          </div>

          {/* Contacts List with Select All Header */}
          <div className="contacts-qualification-list">
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
                />
                <span className="checkmark"></span>
              </label>
              <span className="select-all-text">
                {allSelected ? 'Deselect All' : 'Select All'} 
                <span className="selected-count">({qualifiedCount} of {contacts.length} selected)</span>
              </span>
            </div>

            {/* Contacts */}
            {contacts.map((contact) => {
              const isQualified = contact.qualificationStatus === 'qualified';
              return (
                <div 
                  key={contact.id} 
                  className={`contact-qualification-card ${isQualified ? 'qualified' : ''}`}
                  onClick={() => toggleContactQualification(contact.id)}
                >
                  <div className="contact-select">
                    <label className="checkbox-container">
                      <input 
                        type="checkbox"
                        checked={isQualified}
                        onChange={() => toggleContactQualification(contact.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="checkmark"></span>
                    </label>
                  </div>
                  <div className="contact-avatar">
                    {contact.firstName[0]}{contact.lastName[0]}
                  </div>
                  <div className="contact-info">
                    <h4>{contact.firstName} {contact.lastName}</h4>
                    <div className="contact-meta">
                      <span className="job-title">{contact.jobTitle}</span>
                      <span className="company-name">{getCompanyName(contact)}</span>
                    </div>
                    <span className="contact-email">{contact.email || 'No email found'}</span>
                  </div>
                  {isQualified && (
                    <div className="qualified-badge">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Qualification (Coming soon) */}
      {state.contactQualificationMode === 'ai' && (
        <div className="manual-qualification">
          <div className="empty-state">
            <h3>AI Contact Qualification</h3>
            <p>Coming soon. Please use Manual Qualification for now.</p>
            <div className="wizard-navigation">
              <button className="btn secondary" onClick={() => setContactQualificationMode('manual')}>
                Switch to Manual
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="step-navigation">
        <button className="btn-secondary" onClick={() => {
          setContactQualificationMode(null);
          prevStep();
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        
        {state.contactQualificationMode && (
          <button className="btn-secondary" onClick={() => {
            setContactQualificationMode(null);
          }}>
            Change Method
          </button>
        )}

        {qualifiedCount > 0 && state.contactQualificationMode !== 'ai' && (
          <button className="btn-primary btn-large" onClick={handleContinue}>
            Continue with {qualifiedCount} Contacts
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

