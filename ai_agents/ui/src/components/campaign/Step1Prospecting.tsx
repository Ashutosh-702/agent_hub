import { useEffect, useState } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

import {
  WIZARD_EMPLOYEE_COUNTS as EMPLOYEE_COUNTS,
  WIZARD_INDUSTRIES as INDUSTRIES,
  WIZARD_REGIONS as REGIONS,
} from '../../store/api/wizardMockData';
import { useCreateCampaignFromProspectingJobMutation, useGetCampaignDetailsQuery } from '../../store';

const ITEMS_PER_PAGE = 10;
const CURRENCIES = ['USD', 'INR'] as const;
const LOCATION_TYPES = ['country', 'region'] as const;

export const Step1Prospecting = () => {
  const { state, setFilters, setCampaignId, nextStep, setLoading } = useCampaignWizard();
  const [createCampaignFromProspectingJob, { isLoading: isCreating }] = useCreateCampaignFromProspectingJobMutation();
  
  const [localFilters, setLocalFilters] = useState(state.filters);
  const [showResults, setShowResults] = useState(false);
  const [isRefining, setIsRefining] = useState(false); // Show filters while keeping results below
  const [currentPage, setCurrentPage] = useState(1);
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const { data: campaignDetailsData } = useGetCampaignDetailsQuery(
    createdCampaignId
      ? { campaign_id: createdCampaignId, page: 1, limit: 10 }
      : // dummy (skip below)
        ({ campaign_id: '' as string, page: 1, limit: 10 } as any),
    {
      skip: !createdCampaignId || !isPolling,
      pollingInterval: createdCampaignId && isPolling ? 2000 : 0,
    }
  );

  // Pagination calculations
  const totalItems = state.qualifiedCompanies.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedCompanies = state.qualifiedCompanies.slice(startIndex, endIndex);

  const handleMultiSelect = (field: 'industry' | 'region' | 'employeeCount', value: string) => {
    setLocalFilters(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value],
    }));
  };

  const handleSingleSelect = (field: 'currency' | 'locationType', value: string) => {
    setLocalFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleFetchProspects = async () => {
    setFilters(localFilters);
    setLoading(true, 'Creating campaign & finding prospects...');
    setShowResults(false);
    setIsRefining(false);
    setCurrentPage(1);

    try {
      const payload = {
        industry: localFilters.industry[0] || '',
        employee_count: localFilters.employeeCount.join(','),
        revenue_min: localFilters.revenueMin || '0',
        revenue_max: localFilters.revenueMax || '0',
        location_type: localFilters.locationType || 'country',
        location: localFilters.region[0] || '',
        currency: localFilters.currency || 'USD',
        prospecting_cycle_status: 'prospecting',
      };

      const res = await createCampaignFromProspectingJob(payload).unwrap();
      const newCampaignId = res?.data?.campaign_id;
      if (!newCampaignId) {
        throw new Error('campaign_id missing in response');
      }

      setCreatedCampaignId(newCampaignId);
      setCampaignId(newCampaignId);
      setIsPolling(true);
      setLoading(true, 'Prospecting in progress… waiting for company qualification…');
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    const lifecycleStatus = campaignDetailsData?.data?.campaign?.lifecycle?.status;
    const prospectingCycleStatus = campaignDetailsData?.data?.campaign?.prospecting_cycle?.status;

    if (!createdCampaignId || !isPolling) return;

    // Stop polling once the backend moved the campaign forward.
    if (lifecycleStatus === 'company_qualification' || (prospectingCycleStatus && prospectingCycleStatus !== 'prospecting')) {
      setIsPolling(false);
      setLoading(false);
      // Move to Step 2; Step 2 will load companies page-wise (100/page) from backend.
      nextStep();
    }
  }, [campaignDetailsData, createdCampaignId, isPolling, nextStep, setLoading]);

  const handleRefineSearch = () => {
    setIsRefining(true); // Show filters but keep results visible below
  };

  return (
    <div className="step-container step-lead-generation">
      <div className="step-header">
        <h2>Lead Generation</h2>
        <p>
          {!showResults 
            ? 'Define your target criteria to find potential prospects'
            : isRefining 
              ? 'Adjust your filters and search again' 
              : 'Review the prospects found based on your criteria'}
        </p>
      </div>

      {/* Loading Overlay (no progress bar) */}
      {(state.isLoading || isCreating || isPolling) && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>{state.loadingMessage || 'Working…'}</h3>
            {createdCampaignId && (
              <p style={{ marginTop: 8, opacity: 0.85 }}>Campaign ID: {createdCampaignId}</p>
            )}
          </div>
        </div>
      )}

      {/* Show Filters when: no results yet OR refining search */}
      {(!showResults || isRefining) && (
        <>
          {/* Filters Form */}
          <div className="filters-grid">
            {/* Industry */}
            <div className="filter-group">
              <label>Industry</label>
              <div className="chip-select">
                {INDUSTRIES.map(industry => (
                  <button
                    key={industry}
                    type="button"
                    className={`chip ${localFilters.industry.includes(industry) ? 'selected' : ''}`}
                    onClick={() => handleMultiSelect('industry', industry)}
                  >
                    {industry}
                  </button>
                ))}
              </div>
            </div>

            {/* Region */}
            <div className="filter-group">
              <label>Region / Country</label>
              <div className="chip-select">
                {REGIONS.map(region => (
                  <button
                    key={region}
                    type="button"
                    className={`chip ${localFilters.region.includes(region) ? 'selected' : ''}`}
                    onClick={() => handleMultiSelect('region', region)}
                  >
                    {region}
                  </button>
                ))}
              </div>
            </div>

            {/* Location Type */}
            <div className="filter-group">
              <label>Location Type</label>
              <div className="chip-select">
                {LOCATION_TYPES.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`chip ${localFilters.locationType === t ? 'selected' : ''}`}
                    onClick={() => handleSingleSelect('locationType', t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Employee Count */}
            <div className="filter-group">
              <label>Employee Count</label>
              <div className="chip-select">
                {EMPLOYEE_COUNTS.map(count => (
                  <button
                    key={count}
                    type="button"
                    className={`chip ${localFilters.employeeCount.includes(count) ? 'selected' : ''}`}
                    onClick={() => handleMultiSelect('employeeCount', count)}
                  >
                    {count}
                  </button>
                ))}
              </div>
            </div>

            {/* Currency */}
            <div className="filter-group">
              <label>Currency</label>
              <div className="chip-select">
                {CURRENCIES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`chip ${localFilters.currency === c ? 'selected' : ''}`}
                    onClick={() => handleSingleSelect('currency', c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            {/* Revenue Range */}
            <div className="filter-group filter-row">
              <div className="input-group">
                <label>Min Revenue ($)</label>
                <input
                  type="text"
                  placeholder="e.g., 1000000"
                  value={localFilters.revenueMin}
                  onChange={(e) => setLocalFilters(prev => ({ ...prev, revenueMin: e.target.value }))}
                />
              </div>
              <div className="input-group">
                <label>Max Revenue ($)</label>
                <input
                  type="text"
                  placeholder="e.g., 50000000"
                  value={localFilters.revenueMax}
                  onChange={(e) => setLocalFilters(prev => ({ ...prev, revenueMax: e.target.value }))}
                />
              </div>
            </div>
          </div>

          {/* Fetch Button */}
          <div className="step-actions">
            <button 
              className="btn-primary btn-large"
              onClick={handleFetchProspects}
              disabled={state.isLoading}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              {isRefining ? 'Update Search' : 'Find Prospects'}
            </button>
          </div>
        </>
      )}

      {/* Results View - shown when we have results */}
      {showResults && state.qualifiedCompanies.length > 0 && (
        <div className="results-preview">
          <div className="results-header">
            <h3>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {state.qualifiedCompanies.length} Prospects Found
            </h3>
            <p>Review the prospects and continue to qualification</p>
          </div>

          {/* Pagination info */}
          <div className="pagination-info">
            Showing {startIndex + 1}-{Math.min(endIndex, totalItems)} of {totalItems} prospects
          </div>

          <div className="prospects-preview-list">
            {paginatedCompanies.map((company, index) => (
              <div 
                key={company.id} 
                className="prospect-preview-card"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="prospect-info">
                  <h4>{company.name}</h4>
                  <div className="prospect-meta">
                    <span className="tag">{company.industry}</span>
                    <span className="tag">{company.location}</span>
                    <span className="tag">{company.employeeCount} employees</span>
                  </div>
                </div>
                <div className="prospect-contacts">
                  <span>{company.contacts.length} contacts</span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="pagination-controls">
              <button 
                className="pagination-btn"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                title="First page"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="11 17 6 12 11 7"/>
                  <polyline points="18 17 13 12 18 7"/>
                </svg>
              </button>
              <button 
                className="pagination-btn"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                title="Previous page"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
              </button>

              <div className="pagination-pages">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(page => {
                    // Show first, last, current, and adjacent pages
                    if (page === 1 || page === totalPages) return true;
                    if (Math.abs(page - currentPage) <= 1) return true;
                    return false;
                  })
                  .map((page, idx, arr) => (
                    <span key={page}>
                      {idx > 0 && arr[idx - 1] !== page - 1 && (
                        <span className="pagination-ellipsis">...</span>
                      )}
                      <button
                        className={`pagination-page ${currentPage === page ? 'active' : ''}`}
                        onClick={() => setCurrentPage(page)}
                      >
                        {page}
                      </button>
                    </span>
                  ))}
              </div>

              <button 
                className="pagination-btn"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                title="Next page"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
              <button 
                className="pagination-btn"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                title="Last page"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="13 17 18 12 13 7"/>
                  <polyline points="6 17 11 12 6 7"/>
                </svg>
              </button>
            </div>
          )}

          {/* Continue Button - only show Refine Search when not already refining */}
          <div className="step-actions">
            {!isRefining && (
              <button className="btn-secondary" onClick={handleRefineSearch}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Refine Search
              </button>
            )}
            <button className="btn-primary btn-large" onClick={nextStep}>
              Continue to Qualification
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

