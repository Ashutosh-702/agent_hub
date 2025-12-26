import { useState } from 'react';
import { useCampaignWizard, type Prospect, type Company, type Contact } from './NewCampaignWizard';

// Mock data for dropdowns
const INDUSTRIES = [
  'Software & Technology',
  'Healthcare & Medical',
  'Financial Services',
  'E-commerce & Retail',
  'Manufacturing',
  'Professional Services',
  'Education',
  'Media & Entertainment',
];

const REGIONS = [
  'North America',
  'Europe',
  'Asia Pacific',
  'Latin America',
  'Middle East & Africa',
  'United States',
  'United Kingdom',
  'Germany',
  'India',
  'Australia',
];

const EMPLOYEE_COUNTS = [
  '1-10',
  '11-50',
  '51-200',
  '201-500',
  '501-1000',
  '1001-5000',
  '5000+',
];

// Mock prospects data
const generateMockProspects = (filters: { industry: string[]; region: string[] }): Prospect[] => {
  const companies = [
    { name: 'TechFlow Solutions', industry: 'Software & Technology', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
    { name: 'MedCore Systems', industry: 'Healthcare & Medical', location: 'United Kingdom', revenue: '$10M - $25M', employeeCount: '201-500' },
    { name: 'FinanceHub Inc', industry: 'Financial Services', location: 'Germany', revenue: '$25M - $50M', employeeCount: '501-1000' },
    { name: 'CloudScale Pro', industry: 'Software & Technology', location: 'United States', revenue: '$2M - $5M', employeeCount: '11-50' },
    { name: 'DataDriven Analytics', industry: 'Software & Technology', location: 'India', revenue: '$1M - $2M', employeeCount: '51-200' },
    { name: 'HealthBridge Tech', industry: 'Healthcare & Medical', location: 'Australia', revenue: '$5M - $10M', employeeCount: '201-500' },
    { name: 'RetailGenius', industry: 'E-commerce & Retail', location: 'United States', revenue: '$10M - $25M', employeeCount: '201-500' },
    { name: 'ManufactPro', industry: 'Manufacturing', location: 'Germany', revenue: '$50M - $100M', employeeCount: '1001-5000' },
    { name: 'EduLearn Platform', industry: 'Education', location: 'United Kingdom', revenue: '$2M - $5M', employeeCount: '51-200' },
    { name: 'MediaStream Co', industry: 'Media & Entertainment', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
    { name: 'ConsultPro Services', industry: 'Professional Services', location: 'North America', revenue: '$1M - $2M', employeeCount: '11-50' },
    { name: 'InnovateTech Labs', industry: 'Software & Technology', location: 'Europe', revenue: '$10M - $25M', employeeCount: '201-500' },
  ];

  return companies
    .filter(c => {
      const industryMatch = filters.industry.length === 0 || filters.industry.some(i => c.industry.includes(i));
      const regionMatch = filters.region.length === 0 || filters.region.some(r => c.location.includes(r) || r.includes(c.location));
      return industryMatch && regionMatch;
    })
    .map((c, index) => ({
      id: `prospect-${index + 1}`,
      name: c.name,
      industry: c.industry,
      employeeCount: c.employeeCount,
      revenue: c.revenue,
      location: c.location,
      website: `https://${c.name.toLowerCase().replace(/\s+/g, '')}.com`,
      linkedinUrl: `https://linkedin.com/company/${c.name.toLowerCase().replace(/\s+/g, '-')}`,
      isQualified: undefined,
      qualificationStatus: 'pending' as const,
    }));
};

// Generate mock contacts for each company
const generateMockContacts = (companyId: string, companyName: string): Contact[] => {
  const titles = ['CEO', 'CTO', 'VP of Sales', 'Head of Marketing', 'Director of Operations'];
  const firstNames = ['John', 'Sarah', 'Michael', 'Emily', 'David'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'];
  
  const numContacts = Math.floor(Math.random() * 4) + 2; // 2-5 contacts
  return Array.from({ length: numContacts }, (_, i) => ({
    id: `${companyId}-contact-${i + 1}`,
    companyId,
    firstName: firstNames[i % firstNames.length],
    lastName: lastNames[i % lastNames.length],
    email: `${firstNames[i % firstNames.length].toLowerCase()}.${lastNames[i % lastNames.length].toLowerCase()}@${companyName.toLowerCase().replace(/\s+/g, '')}.com`,
    phone: `+1-555-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    jobTitle: titles[i % titles.length],
    linkedinUrl: `https://linkedin.com/in/${firstNames[i % firstNames.length].toLowerCase()}${lastNames[i % lastNames.length].toLowerCase()}`,
    isSynced: false,
  }));
};

export const Step1LeadGeneration = () => {
  const { state, setFilters, setProspects, setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  
  const [localFilters, setLocalFilters] = useState(state.filters);
  const [showResults, setShowResults] = useState(false);
  const [isRefining, setIsRefining] = useState(false); // Show filters while keeping results below
  const [animationProgress, setAnimationProgress] = useState(0);

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
    
    const prospects = generateMockProspects(localFilters);
    setProspects(prospects);
    
    // Convert prospects to companies with contacts
    const companies: Company[] = prospects.map(p => ({
      ...p,
      contacts: generateMockContacts(p.id, p.name),
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

          <div className="prospects-preview-list">
            {state.qualifiedCompanies.slice(0, 5).map((company, index) => (
              <div 
                key={company.id} 
                className="prospect-preview-card"
                style={{ animationDelay: `${index * 0.1}s` }}
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
            {state.qualifiedCompanies.length > 5 && (
              <div className="more-prospects">
                +{state.qualifiedCompanies.length - 5} more prospects
              </div>
            )}
          </div>

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

