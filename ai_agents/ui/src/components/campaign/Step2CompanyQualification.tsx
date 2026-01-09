import { skipToken } from '@reduxjs/toolkit/query';
import { useEffect, useMemo, useState } from 'react';
import {
  useGetApolloContactListMutation,
  useAiCompanyQualificationMutation,
  useCompanyQualificationProgressQuery,
  useGetCompanyListMinimalQuery,
  useGetCampaignStatusMinimalQuery,
  useManualCompanyQualificationMutation,
  type CompanyMinimal,
} from '../../store';
import { useCampaignWizard } from './NewCampaignWizard';
import productIcpOptions from '../../assets/product_icp_options.json';

// Type for Product ICP options
interface IcpOption {
  id: string;
  label: string;
  value: string;
}

interface IcpQuestion {
  label: string;
  options: IcpOption[];
}

interface ProductIcpConfig {
  description: string;
  questions: Record<string, IcpQuestion>;
}

interface ProductIcpOptionsJson {
  products: Record<string, ProductIcpConfig>;
}

const PAGE_SIZE = 100;

const toLabel = (value: unknown): string => {
  if (Array.isArray(value)) return value.filter(Boolean).join(', ');
  if (typeof value === 'string') return value;
  if (value == null) return '';
  return String(value);
};

// Check if campaign has already completed company qualification based on prospecting_cycle.status
// Step is completed if status has moved past company_qualification_* to contact_qualification_* or later
const isStepAlreadyCompleted = (cycleStatus?: string): boolean => {
  const completedStatuses = [
    // All contact qualification statuses (means company qualification is done)
    'contact_qualification_select',
    'contact_qualification',
    'contact_qualification_ai_started',
    'contact_enrichment_in_progress',
    // Later stages
    'contact_enriched',
    'hubspot_sync_in_progress',
    'hubspot_sync_completed',
    'hubspot_sync_failed',
    'personalization_completed',
    'enrolled_to_sequence',
  ];
  return cycleStatus ? completedStatuses.includes(cycleStatus) : false;
};

// Check if we should show mode selection (status is company_qualification_select)
const shouldShowModeSelection = (cycleStatus?: string): boolean => {
  return cycleStatus === 'company_qualification_select';
};

// Check if AI is actively running (status is company_qualification_ai_started)
const isAiInProgress = (cycleStatus?: string): boolean => {
  return cycleStatus === 'company_qualification_ai_started';
};

export const Step2CompanyQualification = () => {
  const { state, setCompanyQualificationMode, nextStep, prevStep, setLoading } = useCampaignWizard();
  const campaignId = state.campaignId;
  
  // Check if selected product has predefined ICP options
  const selectedProductName = state.filters.productName;
  const icpOptionsData = productIcpOptions as ProductIcpOptionsJson;
  const productConfig = selectedProductName ? icpOptionsData.products[selectedProductName] : undefined;
  const hasProductIcp = !!productConfig;
  const productQuestions = productConfig?.questions ?? {};

  const [page, setPage] = useState(1);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<Set<string>>(new Set());
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isContactPolling, setIsContactPolling] = useState(false);
  const [aiView, setAiView] = useState<'setup' | 'verify'>('setup');

  const [aiSetup, setAiSetup] = useState({
    comprehensiveCriteria: '',
    mandatoryCriteria: '',
    businessModels: '',
    positiveIndicators: '',
    exclusionCriteria: '',
    referenceCompanies: '',
    additionalValidations: '',
  });
  const [aiSetupSaved, setAiSetupSaved] = useState(false);
  const [aiSetupTouched, setAiSetupTouched] = useState(false);
  const [aiStopPolling, setAiStopPolling] = useState(false);

  const isAiSetupValid =
    aiSetup.comprehensiveCriteria.trim().length > 0 &&
    aiSetup.mandatoryCriteria.trim().length > 0 &&
    aiSetup.businessModels.trim().length > 0 &&
    aiSetup.positiveIndicators.trim().length > 0 &&
    aiSetup.exclusionCriteria.trim().length > 0 &&
    aiSetup.referenceCompanies.trim().length > 0 &&
    aiSetup.additionalValidations.trim().length > 0;

  const [manualCompanyQualification] = useManualCompanyQualificationMutation();
  const [queueApolloContactList] = useGetApolloContactListMutation();
  const [aiCompanyQualification] = useAiCompanyQualificationMutation();
  
  // OPTIMIZED: Use minimal status API for polling (no contact data fetched)
  const { data: statusPollingData } = useGetCampaignStatusMinimalQuery(
    campaignId && isContactPolling ? { campaign_id: campaignId } : skipToken,
    { pollingInterval: isContactPolling ? 3000 : 0 }
  );

  // ALWAYS fetch AI job progress on mount (for resume support), then poll if AI mode is active
  // This ensures we detect in-progress/completed AI jobs when resuming a campaign
  const shouldPollAiProgress = Boolean(campaignId && state.companyQualificationMode === 'ai' && !aiStopPolling);
  const { data: aiProgressData } = useCompanyQualificationProgressQuery(
    campaignId ? { campaign_id: campaignId } : skipToken,
    {
      // Always fetch once (for resume), then poll only if AI mode is active
      pollingInterval: shouldPollAiProgress ? 15000 : 0,
    }
  );

  // Once we observe a terminal status, stop polling (prevents continued network spam).
  useEffect(() => {
    const status = aiProgressData?.data?.status;
    if (status === 'completed' || status === 'failed') {
      setAiStopPolling(true);
    }
  }, [aiProgressData?.data?.status]);

  // Auto-switch to Verify view once backend marks AI qualification as completed.
  useEffect(() => {
    if (state.companyQualificationMode !== 'ai') return;
    const status = aiProgressData?.data?.status;
    if (status === 'completed' && aiView === 'setup') {
      setAiView('verify');
    }
  }, [aiProgressData?.data?.status, aiView, state.companyQualificationMode]);

  const companyStatusFilter =
    state.companyQualificationMode === 'ai' && aiView === 'verify' ? true : undefined;
  const queryArgs = campaignId
    ? { campaign_id: campaignId, page, limit: PAGE_SIZE, company_status: companyStatusFilter }
    : skipToken;
  // Use optimized minimal API instead of full campaign details
  const { data, isFetching, isError } = useGetCompanyListMinimalQuery(queryArgs);

  // Check campaign status to determine what to show
  const campaignCycleStatus = data?.data?.campaign_status?.prospecting_cycle?.status;
  const aiJobStatus = aiProgressData?.data?.status;
  
  // Derive state from backend status (source of truth)
  const showModeSelection = shouldShowModeSelection(campaignCycleStatus) && !state.companyQualificationMode;
  const aiActiveFromStatus = isAiInProgress(campaignCycleStatus);
  
  // Step is "already completed" if campaign has moved past company qualification
  const stepAlreadyCompleted = isStepAlreadyCompleted(campaignCycleStatus);
  
  // Log for debugging
  console.log('[Step2] cycleStatus:', campaignCycleStatus, 'mode:', state.companyQualificationMode, 
    'showModeSelection:', showModeSelection, 'aiActiveFromStatus:', aiActiveFromStatus, 
    'stepAlreadyCompleted:', stepAlreadyCompleted, 'aiJobStatus:', aiJobStatus);

  // AUTO-DETECT MODE based on backend status - ONLY when resuming a campaign
  // When status is company_qualification_select, user MUST choose mode (don't auto-set)
  useEffect(() => {
    if (!campaignId) return;
    
    // IMPORTANT: When status is company_qualification_select, user should choose mode
    // Don't auto-set any mode - let them see the mode selection
    if (campaignCycleStatus === 'company_qualification_select') {
      console.log('[Step2] Status is company_qualification_select - waiting for user to choose mode');
      return; // Exit early - don't auto-detect
    }
    
    // If backend status indicates AI is actively running, set AI mode
    if (campaignCycleStatus === 'company_qualification_ai_started' && !state.companyQualificationMode) {
      console.log('[Step2] Auto-detected AI in progress from status');
      setCompanyQualificationMode('ai');
      setAiView('setup');
      return;
    }
    
    // If backend status is company_qualification and AI job completed, set AI mode for review
    if (campaignCycleStatus === 'company_qualification' && aiJobStatus === 'completed' && !state.companyQualificationMode) {
      console.log('[Step2] Auto-detected completed AI job for review');
      setCompanyQualificationMode('ai');
      setAiView('verify');
      setAiStopPolling(true);
      return;
    }
    
    // Fallback: only check AI job status when NOT in mode selection state
    // This is for resuming campaigns where AI was started
    if (!state.companyQualificationMode && aiJobStatus && aiJobStatus !== 'not_started' && 
        campaignCycleStatus !== 'company_qualification_select') {
      console.log('[Step2] Auto-detected AI mode from job status:', aiJobStatus);
      setCompanyQualificationMode('ai');
      
      if (aiJobStatus === 'completed') {
        setAiView('verify');
        setAiStopPolling(true);
      } else if (aiJobStatus === 'failed') {
        setAiView('setup');
        setAiStopPolling(true);
      } else {
        setAiView('setup');
      }
    }
  }, [campaignId, campaignCycleStatus, aiJobStatus, state.companyQualificationMode, setCompanyQualificationMode]);

  const companies: CompanyMinimal[] = data?.data?.companies ?? [];
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

  const handleAiVerifyContinue = async () => {
    if (!campaignId) return;
    await persistCurrentPage();

    // Explicitly queue contacts (AI flow should behave like manual before Step 3)
    setSaveError(null);
    try {
      setLoading(true, 'Fetching contacts from Apollo…');
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

  // OPTIMIZED: Watch status via minimal API - when contacts are ready, just proceed to next step
  // No more fetching ALL contacts and storing in wizard state!
  useEffect(() => {
    if (!campaignId || !isContactPolling) return;
    
    setLoading(true, 'Fetching contacts from Apollo…');
    
    const status = statusPollingData?.data?.prospecting_cycle?.status;
    
    console.log('[Step2 Contact Polling] status:', status, 'isContactPolling:', isContactPolling);
    
    // When status becomes contact_qualification_select or contact_qualification, contacts are ready - proceed to Step 3
    // contact_qualification_select = ready for mode selection (new status)
    // contact_qualification = manual mode or AI completed
    if (status === 'contact_qualification_select' || status === 'contact_qualification') {
      console.log('[Step2] Contacts ready, advancing to Step 3');
      setIsContactPolling(false);
      setLoading(false);
      // Don't store contacts in wizard state - Step 3 will fetch its own paginated data
      nextStep();
    }
  }, [campaignId, isContactPolling, statusPollingData?.data?.prospecting_cycle?.status, nextStep, setLoading]);

  if (!campaignId) {
    return (
      <div className="step-container step-company-qualification">
        <div className="step-header">
          <h2>Company Qualification</h2>
          <p>Missing campaign id. Please go back and start prospecting again.</p>
        </div>
        <div className="step-navigation">
          <button className="btn-secondary" onClick={prevStep}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
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

      {/* Mode Selection - Show only if step not already completed, mode not selected, and status is company_qualification_select */}
      {(showModeSelection || (!state.companyQualificationMode && !stepAlreadyCompleted && !aiActiveFromStatus)) && (
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
              <p>Answer a few prompts to define relevance criteria for AI.</p>
              <span className="mode-tag ai">Setup</span>
            </div>
          </div>
        </div>
      )}

      {/* Step Already Completed - Show review mode */}
      {!state.companyQualificationMode && stepAlreadyCompleted && (
        <div className="step-completed-view">
          <div className="sync-success-banner" style={{ marginBottom: '24px' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>Company Qualification Completed</span>
          </div>

          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{pagination?.total_records ?? '—'}</span>
              <span className="stat-label">Total Companies</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">
                {companies.filter(c => c.is_relevant).length}
              </span>
              <span className="stat-label">Qualified (this page)</span>
            </div>
          </div>

          {/* Show qualified companies (read-only view) */}
          {!isFetching && companies.length > 0 && (
            <div className="companies-qualification-list">
              <div className="select-all-header">
                <span className="select-all-text">
                  Qualified Companies (view only)
                  <span className="selected-count">
                    (Page {page} of {Math.ceil((pagination?.total_records || 0) / PAGE_SIZE)})
                  </span>
                </span>
              </div>

              <div className="companies-cards-grid">
                {companies.filter(c => c.is_relevant).map((c) => {
                  const companyName = c.name || c.source_domain || c.domain || c.company_id;
                  const companyDomain = c.source_domain || c.domain;
                  const industry = toLabel(c.industry);
                  const employeeCount = toLabel(c.employee_count);
                  return (
                    <div key={c.company_id} className="company-card selected" style={{ cursor: 'default' }}>
                      <div className="company-card-header">
                        <div className="company-card-title">
                          <div className="company-name">{companyName}</div>
                          {companyDomain && companyName !== companyDomain && (
                            <div className="company-domain">{companyDomain}</div>
                          )}
                        </div>
                        <div className="company-card-selected-indicator">Qualified ✓</div>
                      </div>
                      <div className="company-card-body">
                        <div className="company-kv-grid">
                          {industry && (
                            <div className="company-kv">
                              <div className="company-k">Industry</div>
                              <div className="company-v">{industry}</div>
                            </div>
                          )}
                          {employeeCount && (
                            <div className="company-kv">
                              <div className="company-k">Employees</div>
                              <div className="company-v">{employeeCount}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
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
              Continue to Contact Qualification
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </button>
          </div>
        </div>
      )}

      {state.companyQualificationMode === 'ai' && (
        <div className="manual-qualification">
          <div className="ai-qualification-setup">
            <div className="ai-setup-header">
              <h3>AI Qualification Setup</h3>
              <p>Fill in the relevance criteria. More detail = better company prioritization.</p>
            </div>

            {aiProgressData?.data && aiProgressData.data.status !== 'not_started' ? (
              <div style={{ marginTop: 16, padding: 12, borderRadius: 12, border: '1px solid #e4e7ed', background: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
                  <div style={{ fontWeight: 700, color: '#111827' }}>
                    AI Qualification: {aiProgressData.data.status}{' '}
                    {/* Show a persistent spinner while polling is active (requests can be too fast to notice isFetching). */}
                    {!aiStopPolling &&
                    (aiProgressData.data.status === 'queued' || aiProgressData.data.status === 'running') ? (
                      <span className="ai-progress-spinner" aria-label="Loading" />
                    ) : null}
                  </div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>
                    Relevant: {aiProgressData.data.progress.relevant} / {aiProgressData.data.progress.total} (Processed: {aiProgressData.data.progress.processed})
                  </div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ height: 8, borderRadius: 999, background: '#e5e7eb', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width:
                          aiProgressData.data.progress.total > 0
                            ? `${Math.min(
                                100,
                                Math.round((aiProgressData.data.progress.processed / aiProgressData.data.progress.total) * 100)
                              )}%`
                            : '0%',
                        background: 'rgba(46, 49, 190, 0.9)',
                      }}
                    />
                  </div>
                </div>
                {aiProgressData.data.error ? (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#dc2626' }}>{aiProgressData.data.error}</div>
                ) : null}
                {aiProgressData.data.status === 'completed' ? (
                  <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
                    <button className="btn-secondary" onClick={() => setAiView('verify')}>
                      Verify Qualified Companies
                    </button>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>
                      Review & adjust AI-selected companies before moving to contacts.
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}

            {aiView === 'setup' ? (
              <>
              {hasProductIcp && (
                <div className="product-icp-banner">
                  <span className="product-icp-badge">{selectedProductName} ICP</span>
                  <span>Select a predefined template from the dropdown, then edit if needed.</span>
                </div>
              )}
              <div className="ai-setup-grid">
              <div className="ai-setup-field">
                <label>
                  Comprehensive relevance criteria <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, comprehensiveCriteria: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.comprehensiveCriteria?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.comprehensiveCriteria}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, comprehensiveCriteria: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.comprehensiveCriteria.trim() ? 'invalid' : undefined}
                  placeholder="Example: A relevant company must be a retailer that specializes in or has significant operations in selling or renting furniture, mattresses, or other heavy/bulky home goods items."
                />
                {aiSetupTouched && !aiSetup.comprehensiveCriteria.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Mandatory criteria (must-have) <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, mandatoryCriteria: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.mandatoryCriteria?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.mandatoryCriteria}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, mandatoryCriteria: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.mandatoryCriteria.trim() ? 'invalid' : undefined}
                  placeholder="Example: Primary business must involve furniture/mattresses/heavy home goods. Must have e-commerce OR physical stores. Must be B2C."
                />
                {aiSetupTouched && !aiSetup.mandatoryCriteria.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Qualifying business models <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, businessModels: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.businessModels?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.businessModels}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, businessModels: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.businessModels.trim() ? 'invalid' : undefined}
                  placeholder="Example: Direct sales (online/in-store), rental services, made-to-order/custom furniture, hybrid sales+rental."
                />
                {aiSetupTouched && !aiSetup.businessModels.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Positive indicators (signals a strong fit) <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, positiveIndicators: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.positiveIndicators?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.positiveIndicators}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, positiveIndicators: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.positiveIndicators.trim() ? 'invalid' : undefined}
                  placeholder="Example: Multiple store locations, strong e-commerce + logistics, customizable options, white-glove delivery, financing/rental plans, metro coverage."
                />
                {aiSetupTouched && !aiSetup.positiveIndicators.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Exclusion criteria (immediate disqualifiers) <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, exclusionCriteria: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.exclusionCriteria?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.exclusionCriteria}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, exclusionCriteria: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.exclusionCriteria.trim() ? 'invalid' : undefined}
                  placeholder="Example: Pure B2B suppliers, interior design services only, marketplaces without own inventory, only small decor items, office-only furniture."
                />
                {aiSetupTouched && !aiSetup.exclusionCriteria.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Reference companies + why they're relevant <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, referenceCompanies: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.referenceCompanies?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.referenceCompanies}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, referenceCompanies: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.referenceCompanies.trim() ? 'invalid' : undefined}
                  placeholder="Example: The Sleep Company (mattress specialist, e-commerce). West Elm/Pottery Barn (multi-location + strong online). CityFurnish (rental)."
                />
                {aiSetupTouched && !aiSetup.referenceCompanies.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>

              <div className="ai-setup-field">
                <label>
                  Additional validations <span className="ai-required">*</span>
                </label>
                {hasProductIcp && (
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setAiSetupSaved(false);
                        setAiSetup((p) => ({ ...p, additionalValidations: e.target.value }));
                      }
                    }}
                    className="product-icp-select"
                  >
                    <option value="">-- Select a template --</option>
                    {productQuestions.additionalValidations?.options.map((opt) => (
                      <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                <textarea
                  value={aiSetup.additionalValidations}
                  onChange={(e) => {
                    setAiSetupSaved(false);
                    setAiSetup((p) => ({ ...p, additionalValidations: e.target.value }));
                  }}
                  required
                  className={aiSetupTouched && !aiSetup.additionalValidations.trim() ? 'invalid' : undefined}
                  placeholder="Example: Must meet ALL mandatory criteria AND at least 2 positive indicators, and must avoid ALL exclusion criteria."
                />
                {aiSetupTouched && !aiSetup.additionalValidations.trim() ? (
                  <div className="ai-field-error">This field is required.</div>
                ) : null}
              </div>
            </div>

            <div className="ai-setup-actions">
              <button
                className="btn-secondary"
                onClick={() => setCompanyQualificationMode(null)}
              >
                Back
              </button>
              <div style={{ flex: 1 }} />
              {aiSetupSaved ? <span className="ai-setup-saved">Saved</span> : null}
              <button
                className="btn-primary"
                onClick={() => {
                  setAiSetupTouched(true);
                  if (!isAiSetupValid) {
                    setSaveError('Please fill all required fields before saving.');
                    return;
                  }
                  if (!campaignId) {
                    setSaveError('Missing campaign id. Please restart prospecting.');
                    return;
                  }

                  const web_prompt =
                    `Comprehensive Outline: ${aiSetup.comprehensiveCriteria}\n\n` +
                    `Mandatory Criteria: ${aiSetup.mandatoryCriteria}\n\n` +
                    `Relevant Business Models: ${aiSetup.businessModels}\n\n` +
                    `Positive Indicators: ${aiSetup.positiveIndicators}\n\n` +
                    `Exclusion Criteria: ${aiSetup.exclusionCriteria}\n\n` +
                    `Reference Companies: ${aiSetup.referenceCompanies}\n\n` +
                    `Other Validations by user: ${aiSetup.additionalValidations}`;

                  setLoading(true, 'Saving AI criteria…');
                  void (async () => {
                    try {
                      setSaveError(null);
                      await aiCompanyQualification({ campaign_id: campaignId, web_prompt }).unwrap();
                      setAiSetupSaved(true);
                      setLoading(false);
                    } catch (e) {
                      const msg =
                        typeof e === 'object' && e && 'data' in e
                          ? JSON.stringify((e as any).data)
                          : 'Failed to save AI criteria';
                      setSaveError(msg);
                      setLoading(false);
                    }
                  })();
                }}
              >
                Save Setup
              </button>
            </div>
              </>
            ) : (
              <div style={{ marginTop: 16 }}>
                <div className="step-header" style={{ marginBottom: 12 }}>
                  <h3 style={{ margin: 0 }}>Verify AI Qualified Companies</h3>
                  <p style={{ margin: '6px 0 0 0' }}>
                    This list shows companies marked relevant by AI. Click cards to deselect companies you don’t want.
                  </p>
                </div>

                {/* Reuse the same manual list UI but filtered to is_relevant=true */}
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
                      <button className="btn-secondary" onClick={toggleSelectAllOnPage}>
                        {allSelectedOnPage ? 'Deselect All (Page)' : 'Select All (Page)'}
                      </button>
                    </div>

                    <div className="companies-cards-grid">
                      {companies.map((c) => {
                        const companyName = c.name || c.domain || c.company_id;
                        const companyDomain = c.domain;
                        const industry = toLabel(c.industry);
                        const employeeCount = toLabel(c.employee_count);
                        const location = toLabel(c.location);
                        const revenueMin = toLabel(c.revenue_min);
                        const revenueMax = toLabel(c.revenue_max);
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
                              {c.relevance_reason ? (
                                <div className="company-reason">{c.relevance_reason}</div>
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="step-navigation">
                  <button className="btn-secondary" onClick={() => setAiView('setup')}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="19" y1="12" x2="5" y2="12"/>
                      <polyline points="12 19 5 12 12 5"/>
                    </svg>
                    Back to Setup
                  </button>
                  <div style={{ flex: 1 }} />
                  <button className="btn-secondary" onClick={handlePrevPage} disabled={page <= 1 || isFetching}>
                    Save & Prev Page
                  </button>
                  <button className="btn-secondary" onClick={handleNextPage} disabled={!pagination?.has_next || isFetching}>
                    Save & Next Page
                  </button>
                  <button className="btn-primary" onClick={handleAiVerifyContinue} disabled={isFetching}>
                    Continue to Contacts
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="5" y1="12" x2="19" y2="12"/>
                      <polyline points="12 5 19 12 12 19"/>
                    </svg>
                  </button>
                </div>
              </div>
            )}
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
            <button className="btn-secondary" onClick={handleSelectAllCampaign}>
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
                <button className="btn-secondary" onClick={toggleSelectAllOnPage}>
                  {allSelectedOnPage ? 'Deselect All (Page)' : 'Select All (Page)'}
                </button>
                {someSelectedOnPage && !allSelectedOnPage ? (
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>Partial</span>
                ) : null}
              </div>

              <div className="companies-cards-grid">
                {companies.map((c) => {
                  const companyName = c.name || c.source_domain || c.domain || c.company_id;
                  const companyDomain = c.source_domain || c.domain;
                  const industry = toLabel(c.industry);
                  const employeeCount = toLabel(c.employee_count);
                  const location = toLabel(c.location);
                  const revenueMin = toLabel(c.revenue_min);
                  const revenueMax = toLabel(c.revenue_max);
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
                      {c.relevance_reason ? (
                        <div className="company-reason">{c.relevance_reason}</div>
                      ) : null}
                    </div>
                  </div>
                  );
                })}
              </div>
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

            <div style={{ flex: 1 }} />

            <button className="btn-secondary" onClick={handlePrevPage} disabled={page <= 1 || isFetching}>
              Save & Prev Page
            </button>
            <button className="btn-secondary" onClick={handleNextPage} disabled={!pagination?.has_next || isFetching}>
              Save & Next Page
            </button>

            <button className="btn-primary" onClick={handleContinue} disabled={isFetching}>
              Continue
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

