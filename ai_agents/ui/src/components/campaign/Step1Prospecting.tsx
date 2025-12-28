import { useState } from 'react';
import { useCampaignWizard, type Company } from './NewCampaignWizard';

import {
  getMockContacts,
  getMockProspects,
  WIZARD_EMPLOYEE_COUNTS as EMPLOYEE_COUNTS,
  WIZARD_INDUSTRIES as INDUSTRIES,
  WIZARD_REGIONS as REGIONS,
} from '../../store/api/wizardMockData';

const ITEMS_PER_PAGE = 10;

export const Step1Prospecting = () => {
  const { state, setFilters, setProspects, setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  
  const [localFilters, setLocalFilters] = useState(state.filters);
  const [showResults, setShowResults] = useState(false);
  const [isRefining, setIsRefining] = useState(false); // Show filters while keeping results below
  const [animationProgress, setAnimationProgress] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

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

  const handleFetchProspects = async () => {
    setFilters(localFilters);
    setLoading(true, 'Searching for prospects...', 0);
    setShowResults(false);
    setIsRefining(false);
    setAnimationProgress(0);
    setCurrentPage(1); // Reset to first page on new search

    // Simulate progressive loading animation
    const estimatedTotal = Math.floor(Math.random() * 50) + 30;
    let progress = 0;
    
    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 15) + 5;
      if (progress >= estimatedTotal) {
        progress = estimatedTotal;
        clearInterval(interval);
      }
      setAnimationProgress(progress);
      setLoading(true, 'Fetching prospects from Apollo...', progress);
    }, 300);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    clearInterval(interval);
    
    const prospects = getMockProspects(localFilters);
    setProspects(prospects);
    
    // Convert prospects to companies with contacts
    const companies: Company[] = prospects.map(p => ({
      ...p,
      contacts: getMockContacts(p.id, p.name),
      syncStatus: 'not_synced' as const,
      personalization: {
        messageStatus: 'pending' as const,
        deckStatus: 'pending' as const,
      },
    }));
    setQualifiedCompanies(companies);
    
    setLoading(false);
    setShowResults(true);
  };

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

      {/* Loading Animation */}
      {state.isLoading && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="pulse-ring" />
              <div className="pulse-ring delay-1" />
              <div className="pulse-ring delay-2" />
              <div className="loading-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
            </div>
            <h3>{state.loadingMessage}</h3>
            <div className="loading-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${Math.min((animationProgress / 80) * 100, 100)}%` }}
                />
              </div>
              <span className="progress-count">
                {animationProgress} prospects found...
              </span>
            </div>
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

