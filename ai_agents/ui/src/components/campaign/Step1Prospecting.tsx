import { useEffect, useState } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

import {
  WIZARD_EMPLOYEE_COUNTS as EMPLOYEE_COUNTS,
} from '../../store/api/wizardMockData';

// Regions list (from Wide Prospecting)
const REGIONS = [
  'North America',
  'South America', 
  'Europe',
  'APAC',
  'EMEA',
  'Africa',
  'LATAM',
];

// Countries list (from Wide Prospecting)
const COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", 
  "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", 
  "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", 
  "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", 
  "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", 
  "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", 
  "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", 
  "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", 
  "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", 
  "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", 
  "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", 
  "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", 
  "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", 
  "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", 
  "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", 
  "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", 
  "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", 
  "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", 
  "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", 
  "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", 
  "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", 
  "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", 
  "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
];
import { useCreateCampaignFromProspectingJobMutation, useGetCampaignStatusMinimalQuery } from '../../store';
import lushaIndustryConfig from '../../assets/lusha_industry_config.json';

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
  
  // Industry dropdown state
  const [industrySearchQuery, setIndustrySearchQuery] = useState('');
  const [collapsedIndustryGroups, setCollapsedIndustryGroups] = useState<Record<string, boolean>>(
    () => lushaIndustryConfig.reduce((acc, main) => {
      acc[main.main_industry] = true; // Start all collapsed
      return acc;
    }, {} as Record<string, boolean>)
  );
  const [isIndustryDropdownOpen, setIsIndustryDropdownOpen] = useState(false);
  
  // Location (country/region) dropdown state
  const [locationSearchQuery, setLocationSearchQuery] = useState('');
  const [isLocationDropdownOpen, setIsLocationDropdownOpen] = useState(false);

  // OPTIMIZED: Use minimal status API instead of heavy campaign_details_with_companies
  const { data: campaignStatusData } = useGetCampaignStatusMinimalQuery(
    createdCampaignId
      ? { campaign_id: createdCampaignId }
      : { campaign_id: '' },
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

  const handleSingleSelect = (field: 'currency' | 'locationType' | 'productName', value: string) => {
    setLocalFilters(prev => ({ ...prev, [field]: value }));
  };

  // Industry dropdown helpers
  const toggleIndustryCollapse = (mainIndustry: string) => {
    setCollapsedIndustryGroups(prev => ({ ...prev, [mainIndustry]: !prev[mainIndustry] }));
  };

  const toggleSubIndustry = (subValue: string) => {
    setLocalFilters(prev => ({
      ...prev,
      industry: prev.industry.includes(subValue)
        ? prev.industry.filter(v => v !== subValue)
        : [...prev.industry, subValue],
    }));
  };

  const toggleMainIndustry = (subValues: string[]) => {
    const allSelected = subValues.every(v => localFilters.industry.includes(v));
    setLocalFilters(prev => ({
      ...prev,
      industry: allSelected
        ? prev.industry.filter(v => !subValues.includes(v))
        : [...new Set([...prev.industry, ...subValues])],
    }));
  };

  const industryQuery = industrySearchQuery.trim().toLowerCase();
  const hasIndustryQuery = industryQuery.length > 0;
  
  const filteredIndustries = lushaIndustryConfig.filter(main => {
    if (!hasIndustryQuery) return true;
    const mainMatch = main.main_industry.toLowerCase().includes(industryQuery);
    const subMatch = main.sub_industries.some((s: { value: string }) => s.value.toLowerCase().includes(industryQuery));
    return mainMatch || subMatch;
  });

  // Location (country/region) dropdown helpers
  const locationQuery = locationSearchQuery.trim().toLowerCase();
  const hasLocationQuery = locationQuery.length > 0;
  
  // Get the list based on location type
  const locationList = localFilters.locationType === 'country' ? COUNTRIES : REGIONS;
  const filteredLocations = hasLocationQuery
    ? locationList.filter(loc => loc.toLowerCase().includes(locationQuery))
    : locationList;

  const toggleLocation = (location: string) => {
    setLocalFilters(prev => ({
      ...prev,
      region: prev.region.includes(location)
        ? prev.region.filter(v => v !== location)
        : [...prev.region, location],
    }));
  };

  // Clear region selections when location type changes
  const handleLocationTypeChange = (type: string) => {
    setLocalFilters(prev => ({
      ...prev,
      locationType: type,
      region: [], // Clear selections when switching type
    }));
  };

  const handleFetchProspects = async () => {
    setFilters(localFilters);
    setLoading(true, 'Creating campaign & finding prospects...');
    setShowResults(false);
    setIsRefining(false);
    setCurrentPage(1);

    try {
      // Use products selected in ProductSelection step (state.selectedProducts)
      const productNames = state.selectedProducts.join(',');
      
      const payload = {
        campaign_name: state.campaignName, // Required unique campaign name
        industry: localFilters.industry[0] || '',
        employee_count: localFilters.employeeCount.join(','),
        revenue_min: localFilters.revenueMin || '0',
        revenue_max: localFilters.revenueMax || '0',
        location_type: localFilters.locationType || 'country',
        location: localFilters.region[0] || '',
        currency: localFilters.currency || 'USD',
        product_name: productNames, // From ProductSelection step
        campaign_type: state.campaignType || 'wide_prospecting', // Store campaign type
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
    // OPTIMIZED: Read from minimal status API (not full campaign details)
    const lifecycleStatus = campaignStatusData?.data?.lifecycle?.status;
    const prospectingCycleStatus = campaignStatusData?.data?.prospecting_cycle?.status;

    if (!createdCampaignId || !isPolling) return;

    // Stop polling once the backend moved the campaign forward.
    if (lifecycleStatus === 'company_qualification' || (prospectingCycleStatus && prospectingCycleStatus !== 'prospecting')) {
      setIsPolling(false);
      setLoading(false);
      // Move to Step 2; Step 2 will load companies page-wise (100/page) from backend.
      nextStep();
    }
  }, [campaignStatusData, createdCampaignId, isPolling, nextStep, setLoading]);

  const handleRefineSearch = () => {
    setIsRefining(true); // Show filters but keep results visible below
  };

  return (
    <div className="step-container step-lead-generation">
      <div className="step-header">
        <h2>Prospect Companies</h2>
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
            {typeof campaignStatusData?.data?.company_runs_count === 'number' && (
              <p style={{ marginTop: 8, opacity: 0.85 }}>
                Companies fetched: {campaignStatusData.data.company_runs_count}
              </p>
            )}
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
            {/* Industry Dropdown */}
            <div className="filter-group">
              <label>Industry</label>
              <div className="industry-dropdown-container">
                <button
                  type="button"
                  className="industry-dropdown-trigger"
                  onClick={() => setIsIndustryDropdownOpen(!isIndustryDropdownOpen)}
                >
                  <span>
                    {localFilters.industry.length > 0
                      ? `${localFilters.industry.length} selected`
                      : 'Select industries...'}
                  </span>
                  <svg
                    className={`dropdown-arrow ${isIndustryDropdownOpen ? 'open' : ''}`}
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {isIndustryDropdownOpen && (
                  <div className="industry-dropdown-panel">
                    <input
                      type="text"
                      className="industry-search-input"
                      placeholder="Search industries..."
                      value={industrySearchQuery}
                      onChange={(e) => setIndustrySearchQuery(e.target.value)}
                      autoFocus
                    />

                    <div className="industry-tree">
                      {filteredIndustries.map(main => {
                        const mainMatches = hasIndustryQuery && main.main_industry.toLowerCase().includes(industryQuery);
                        const subs = hasIndustryQuery && !mainMatches
                          ? main.sub_industries.filter((s: { value: string }) => s.value.toLowerCase().includes(industryQuery))
                          : main.sub_industries;

                        const allSubValues = subs.map((s: { value: string }) => s.value);
                        const allSubsSelected = allSubValues.length > 0 && allSubValues.every((v: string) => localFilters.industry.includes(v));
                        const someSubsSelected = allSubValues.some((v: string) => localFilters.industry.includes(v)) && !allSubsSelected;
                        const isCollapsed = hasIndustryQuery ? false : !!collapsedIndustryGroups[main.main_industry];

                        return (
                          <div key={main.main_industry} className="industry-group">
                            <div
                              className="industry-main"
                              onClick={() => !hasIndustryQuery && toggleIndustryCollapse(main.main_industry)}
                            >
                              <span className={`collapse-icon ${isCollapsed ? 'collapsed' : ''}`}>▶</span>
                              <input
                                type="checkbox"
                                checked={allSubsSelected}
                                ref={(el) => { if (el) el.indeterminate = someSubsSelected; }}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  toggleMainIndustry(allSubValues);
                                }}
                                onClick={(e) => e.stopPropagation()}
                              />
                              <span>{main.main_industry}</span>
                            </div>

                            {!isCollapsed && (
                              <div className="industry-sub-list">
                                {subs.map((sub: { value: string; id: number }) => (
                                  <label key={sub.id} className="industry-sub">
                                    <input
                                      type="checkbox"
                                      checked={localFilters.industry.includes(sub.value)}
                                      onChange={() => toggleSubIndustry(sub.value)}
                                    />
                                    <span>{sub.value}</span>
                                  </label>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <div className="industry-dropdown-footer">
                      <button
                        type="button"
                        className="btn-small"
                        onClick={() => setIsIndustryDropdownOpen(false)}
                      >
                        Done
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Show selected industries as chips */}
              {localFilters.industry.length > 0 && (
                <div className="selected-industries-chips">
                  {localFilters.industry.slice(0, 5).map(ind => (
                    <span key={ind} className="chip selected small">
                      {ind}
                      <button
                        type="button"
                        className="chip-remove"
                        onClick={() => toggleSubIndustry(ind)}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {localFilters.industry.length > 5 && (
                    <span className="chip small">+{localFilters.industry.length - 5} more</span>
                  )}
                </div>
              )}
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
                    onClick={() => handleLocationTypeChange(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Region / Country Dropdown */}
            <div className="filter-group">
              <label>{localFilters.locationType === 'country' ? 'Country' : 'Region'}</label>
              <div className="location-dropdown-container">
                  <button
                    type="button"
                  className="location-dropdown-trigger"
                  onClick={() => setIsLocationDropdownOpen(!isLocationDropdownOpen)}
                >
                  <span>
                    {localFilters.region.length > 0
                      ? `${localFilters.region.length} selected`
                      : `Select ${localFilters.locationType === 'country' ? 'countries' : 'regions'}...`}
                  </span>
                  <svg
                    className={`dropdown-arrow ${isLocationDropdownOpen ? 'open' : ''}`}
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                  </button>

                {isLocationDropdownOpen && (
                  <div className="location-dropdown-panel">
                    <input
                      type="text"
                      className="location-search-input"
                      placeholder={`Search ${localFilters.locationType === 'country' ? 'countries' : 'regions'}...`}
                      value={locationSearchQuery}
                      onChange={(e) => setLocationSearchQuery(e.target.value)}
                      autoFocus
                    />

                    <div className="location-list">
                      {filteredLocations.map(loc => (
                        <label key={loc} className="location-item">
                          <input
                            type="checkbox"
                            checked={localFilters.region.includes(loc)}
                            onChange={() => toggleLocation(loc)}
                          />
                          <span>{loc}</span>
                        </label>
                      ))}
                      {filteredLocations.length === 0 && (
                        <div className="location-empty">No matches found</div>
                      )}
                    </div>

                    <div className="location-dropdown-footer">
                      <button
                        type="button"
                        className="btn-small"
                        onClick={() => {
                          setIsLocationDropdownOpen(false);
                          setLocationSearchQuery('');
                        }}
                      >
                        Done
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Show selected locations as chips */}
              {localFilters.region.length > 0 && (
                <div className="selected-locations-chips">
                  {localFilters.region.slice(0, 5).map(loc => (
                    <span key={loc} className="chip selected small">
                      {loc}
                      <button
                        type="button"
                        className="chip-remove"
                        onClick={() => toggleLocation(loc)}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {localFilters.region.length > 5 && (
                    <span className="chip small">+{localFilters.region.length - 5} more</span>
                  )}
                </div>
              )}
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
                <label>Min Revenue in millions ($)</label>
                <input
                  type="text"
                  placeholder="e.g., 1"
                  value={localFilters.revenueMin}
                  onChange={(e) => setLocalFilters(prev => ({ ...prev, revenueMin: e.target.value }))}
                />
              </div>
              <div className="input-group">
                <label>Max Revenue in millions ($)</label>
                <input
                  type="text"
                  placeholder="e.g., 50"
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
