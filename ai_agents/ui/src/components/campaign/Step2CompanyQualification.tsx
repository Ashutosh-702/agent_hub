import { skipToken } from '@reduxjs/toolkit/query';
import { useEffect, useMemo, useState } from 'react';
import {
  useGetApolloContactListMutation,
  useLazyGetCampaignContactListQuery,
  useGetCampaignDetailsQuery,
  useManualCompanyQualificationMutation,
  type CampaignContactListItem,
} from '../../store';
import { useCampaignWizard } from './NewCampaignWizard';

const PAGE_SIZE = 100;

const toLabel = (value: unknown): string => {
  if (Array.isArray(value)) return value.filter(Boolean).join(', ');
  if (typeof value === 'string') return value;
  if (value == null) return '';
  return String(value);
};

export const Step2CompanyQualification = () => {
  const { state, setCompanyQualificationMode, nextStep, prevStep, setLoading, setQualifiedContacts } = useCampaignWizard();
  const campaignId = state.campaignId;

  const [page, setPage] = useState(1);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<Set<string>>(new Set());
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isContactPolling, setIsContactPolling] = useState(false);

  const [manualCompanyQualification] = useManualCompanyQualificationMutation();
  const [queueApolloContactList] = useGetApolloContactListMutation();
  const [fetchCampaignContactList] = useLazyGetCampaignContactListQuery();

  const queryArgs = campaignId ? { campaign_id: campaignId, page, limit: PAGE_SIZE } : skipToken;
  const { data, isFetching, isError } = useGetCampaignDetailsQuery(queryArgs);

  const companies = data?.data?.companies ?? [];
  const pagination = data?.pagination;

  const companyIdsOnPage = useMemo(() => companies.map((c) => c.company_id), [companies]);

  // Initialize selections from backend (is_relevant) whenever page changes.
  useEffect(() => {
    const next = new Set<string>();
    for (const c of companies) {
      if (c.is_relevant) next.add(c.company_id);
    }
    setSelectedCompanyIds(next);
  }, [companies]);

  const allSelectedOnPage = companyIdsOnPage.length > 0 && companyIdsOnPage.every((id) => selectedCompanyIds.has(id));
  const someSelectedOnPage = companyIdsOnPage.some((id) => selectedCompanyIds.has(id)) && !allSelectedOnPage;

  const toggleCompany = (companyId: string) => {
    setSelectedCompanyIds((prev) => {
      const next = new Set(prev);
      if (next.has(companyId)) next.delete(companyId);
      else next.add(companyId);
      return next;
    });
  };

  const toggleSelectAllOnPage = () => {
    setSelectedCompanyIds((prev) => {
      const next = new Set(prev);
      const shouldSelectAll = !companyIdsOnPage.every((id) => next.has(id));
      if (shouldSelectAll) {
        companyIdsOnPage.forEach((id) => next.add(id));
      } else {
        companyIdsOnPage.forEach((id) => next.delete(id));
      }
      return next;
    });
  };

  const persistCurrentPage = async () => {
    if (!campaignId) return;
    setSaveError(null);

    // Requirement: if user didn't select any company on current page, don't call the API.
    if (selectedCompanyIds.size === 0) return;

    const selected = Array.from(selectedCompanyIds);
    const unselected = companyIdsOnPage.filter((id) => !selectedCompanyIds.has(id));

    try {
      setLoading(true, 'Saving company qualification…');

      // Persist TRUE for selected companies on this page
      if (selected.length > 0) {
        await manualCompanyQualification({
          campaign_id: campaignId,
          selection_type: 'selective',
          company_ids: selected,
          is_relevant: true,
        }).unwrap();
      }

      // Persist FALSE for unselected companies on this page
      if (unselected.length > 0) {
        await manualCompanyQualification({
          campaign_id: campaignId,
          selection_type: 'selective',
          company_ids: unselected,
          is_relevant: false,
        }).unwrap();
      }
    } catch (e: unknown) {
      const msg =
        typeof e === 'object' && e && 'data' in e
          ? JSON.stringify((e as any).data)
          : 'Failed to save qualification';
      setSaveError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const handleNextPage = async () => {
    if (!pagination?.has_next) return;
    await persistCurrentPage();
    setPage((p) => p + 1);
  };

  const handlePrevPage = async () => {
    if (page <= 1) return;
    await persistCurrentPage();
    setPage((p) => Math.max(1, p - 1));
  };

  const handleSelectAllCampaign = async () => {
    if (!campaignId) return;
    setSaveError(null);
    try {
      setLoading(true, 'Selecting all companies…');
      await manualCompanyQualification({
        campaign_id: campaignId,
        selection_type: 'all',
        is_relevant: true,
      }).unwrap();
    } catch (e: unknown) {
      const msg =
        typeof e === 'object' && e && 'data' in e
          ? JSON.stringify((e as any).data)
          : 'Failed to select all companies';
      setSaveError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = async () => {
    if (!campaignId) return;
    await persistCurrentPage();

    // Queue Apollo contact list fetch
    setSaveError(null);
    try {
      setLoading(true, 'Queueing Apollo contacts…');
      await queueApolloContactList({ campaign_id: campaignId, enrichment_status: false }).unwrap();
      setIsContactPolling(true);
    } catch (e: unknown) {
      const msg =
        typeof e === 'object' && e && 'data' in e
          ? JSON.stringify((e as any).data)
          : 'Failed to queue Apollo contact fetch';
      setSaveError(msg);
      setLoading(false);
    }
  };

  // Poll until campaign moves to contact_qualification, then load contacts and go to Step 3.
  useEffect(() => {
    if (!campaignId || !isContactPolling) return;

    let cancelled = false;
    setLoading(true, 'Fetching contacts from Apollo…');

    const poll = async () => {
      try {
        // Use a consistent page size for both polling and fetching to avoid pagination mismatches.
        const limit = 100;
        const first = await fetchCampaignContactList({ campaign_id: campaignId, page: 1, limit }).unwrap();
        const status = first?.data?.campaign?.prospecting_cycle?.status;

        // Keep polling until backend sets contact_qualification
        if (status !== 'contact_qualification') return;

        // Once ready, load contacts (all pages, with a safety cap)
        let page = 1;
        let hasNext = first.pagination?.has_next ?? false;
        const all: CampaignContactListItem[] = [];
        let pagesFetched = 0;
        const MAX_PAGES = 50; // safety cap

        // include first page contacts (if any) then continue paging
        all.push(...(first.data?.contacts || []));
        while (hasNext && pagesFetched < MAX_PAGES) {
          pagesFetched += 1;
          page += 1;
          const res = await fetchCampaignContactList({ campaign_id: campaignId, page, limit }).unwrap();
          all.push(...(res.data?.contacts || []));
          hasNext = res.pagination?.has_next ?? false;
        }

        if (cancelled) return;

        // Map API contacts into wizard contacts
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
        }));

        setQualifiedContacts(mapped);
        setIsContactPolling(false);
        setLoading(false);
        nextStep();
      } catch (e) {
        // ignore transient errors during polling; keep waiting
      }
    };

    const interval = window.setInterval(() => {
      void poll();
    }, 3000);

    // run immediately too
    void poll();

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [campaignId, fetchCampaignContactList, isContactPolling, nextStep, setLoading, setQualifiedContacts]);

  if (!campaignId) {
    return (
      <div className="step-container step-company-qualification">
        <div className="step-header">
          <h2>Company Qualification</h2>
          <p>Missing campaign id. Please go back and start prospecting again.</p>
        </div>
        <div className="wizard-navigation">
          <button className="btn secondary" onClick={prevStep}>
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="step-container step-company-qualification">
      <div className="step-header">
        <h2>Company Qualification</h2>
        <p>Review companies page-wise (100 per page). Changes are saved before paging.</p>
      </div>

      {/* Loading Overlay (queue + polling) */}
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

      {saveError && (
        <div className="error-banner" style={{ marginBottom: 12 }}>
          {saveError}
        </div>
      )}

      {/* Mode Selection */}
      {!state.companyQualificationMode && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div className="mode-card" onClick={() => setCompanyQualificationMode('manual')}>
              <div className="mode-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </div>
              <h4>Manual Qualification</h4>
              <p>Select relevant companies page by page.</p>
              <span className="mode-tag">Recommended</span>
            </div>

            <div className="mode-card" onClick={() => setCompanyQualificationMode('ai')}>
              <div className="mode-icon ai">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z" />
                  <path d="M12 8v8" />
                  <path d="M5 12h14" />
                  <circle cx="5" cy="12" r="2" />
                  <circle cx="19" cy="12" r="2" />
                  <circle cx="12" cy="19" r="2" />
                </svg>
              </div>
              <h4>AI Qualification</h4>
              <p>Coming soon.</p>
              <span className="mode-tag ai">Soon</span>
            </div>
          </div>
        </div>
      )}

      {state.companyQualificationMode === 'ai' && (
        <div className="manual-qualification">
          <div className="empty-state">
            <h3>AI Qualification</h3>
            <p>Coming soon. Please use Manual Qualification for now.</p>
          </div>
        </div>
      )}

      {/* Manual Qualification */}
      {state.companyQualificationMode === 'manual' && (
        <div className="manual-qualification">
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{pagination?.total_records ?? '—'}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">{selectedCompanyIds.size}</span>
              <span className="stat-label">Selected (this page)</span>
            </div>
            <div className="stat">
              <span className="stat-value">{page}</span>
              <span className="stat-label">Page</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
            <button className="btn secondary" onClick={handleSelectAllCampaign}>
              Select All (Campaign)
            </button>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              Sends only: campaign_id, selection_type=all, is_relevant=true
            </div>
          </div>

          {isFetching && (
            <div style={{ padding: 12, color: '#94a3b8' }}>
              Loading companies…
            </div>
          )}

          {isError && (
            <div className="error-banner" style={{ marginBottom: 12 }}>
              Failed to load companies for qualification.
            </div>
          )}

          {!isFetching && companies.length > 0 && (
            <div className="companies-qualification-list">
              <div className="select-all-header">
                <span className="select-all-text">
                  Select companies (click cards)
                  <span className="selected-count">
                    ({selectedCompanyIds.size} of {companies.length} selected)
                  </span>
                </span>
                <div style={{ flex: 1 }} />
                <button className="btn secondary" onClick={toggleSelectAllOnPage}>
                  {allSelectedOnPage ? 'Deselect All (Page)' : 'Select All (Page)'}
                </button>
                {someSelectedOnPage && !allSelectedOnPage ? (
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>Partial</span>
                ) : null}
              </div>

              <div className="companies-cards-grid">
                {companies.map((c) => {
                  const companyName = c.company?.identifiers?.name || c.company?.identifiers?.domain || c.company_id;
                  const companyDomain = c.company?.identifiers?.domain;
                  const industry = toLabel(c.company?.profile?.industry);
                  const employeeCount = toLabel(c.company?.profile?.employee_count);
                  const location = toLabel(c.company?.location?.name);
                  const revenueMin = toLabel(c.company?.profile?.revenue_min);
                  const revenueMax = toLabel(c.company?.profile?.revenue_max);
                  const isSelected = selectedCompanyIds.has(c.company_id);
                  return (
                  <div
                    key={c.company_id}
                    className={`company-card ${isSelected ? 'selected' : ''}`}
                    role="button"
                    tabIndex={0}
                    onClick={() => toggleCompany(c.company_id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleCompany(c.company_id);
                      }
                    }}
                  >
                    <div className="company-card-header">
                      <div className="company-card-title">
                        <div className="company-name">{companyName}</div>
                        {companyDomain && companyName !== companyDomain ? (
                          <div className="company-domain">{companyDomain}</div>
                        ) : null}
                      </div>
                      <div className="company-card-selected-indicator" aria-hidden="true">
                        {isSelected ? 'Selected' : 'Select'}
                      </div>
                    </div>
                    <div className="company-card-body">
                      <div className="company-kv-grid">
                        {industry ? (
                          <div className="company-kv">
                            <div className="company-k">Industry</div>
                            <div className="company-v">{industry}</div>
                          </div>
                        ) : null}
                        {employeeCount ? (
                          <div className="company-kv">
                            <div className="company-k">Employees</div>
                            <div className="company-v">{employeeCount}</div>
                          </div>
                        ) : null}
                        {location ? (
                          <div className="company-kv">
                            <div className="company-k">Location</div>
                            <div className="company-v">{location}</div>
                          </div>
                        ) : null}
                        {revenueMin || revenueMax ? (
                          <div className="company-kv">
                            <div className="company-k">Revenue</div>
                            <div className="company-v">
                              {revenueMin && revenueMax ? `${revenueMin} - ${revenueMax}` : revenueMin || revenueMax}
                            </div>
                          </div>
                        ) : null}
                      </div>
                      {c.metadata?.relevance_reason ? (
                        <div className="company-reason">{c.metadata.relevance_reason}</div>
                      ) : null}
                    </div>
                  </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="wizard-navigation">
            <button className="btn secondary" onClick={prevStep}>
              Back
            </button>

            <div style={{ flex: 1 }} />

            <button className="btn secondary" onClick={handlePrevPage} disabled={page <= 1 || isFetching}>
              Save & Prev Page
            </button>
            <button className="btn secondary" onClick={handleNextPage} disabled={!pagination?.has_next || isFetching}>
              Save & Next Page
            </button>

            <button className="btn primary" onClick={handleContinue} disabled={isFetching}>
              Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
};


