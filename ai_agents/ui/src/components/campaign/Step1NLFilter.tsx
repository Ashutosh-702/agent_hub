import React, { useState, useEffect } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import {
  useCreateCampaignFromCSVImportMutation,
  useGetCampaignDetailsQuery,
} from '../../store';

// Mock external NL API response
interface NLCompanyResult {
  domain: string;
  name: string;
  industry?: string;
  location?: string;
  employeeCount?: string;
  revenue?: string;
  relevanceScore?: number;
}

// Mock function simulating external "NL to Companies" API
const fetchCompaniesFromNLAPI = async (
  _query: string
): Promise<NLCompanyResult[]> => {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Mock response data - in production, this would be a real API call
  const mockCompanies: NLCompanyResult[] = [
    { domain: 'acmecorp.com', name: 'Acme Corp', industry: 'Enterprise Software', location: 'San Francisco, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 95 },
    { domain: 'technova.io', name: 'TechNova', industry: 'Cloud Infrastructure', location: 'Seattle, USA', employeeCount: '501-1000', revenue: '$50M - $100M', relevanceScore: 93 },
    { domain: 'datasphere.ai', name: 'DataSphere', industry: 'Data Analytics', location: 'Boston, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 91 },
    { domain: 'cloudfirst.com', name: 'CloudFirst', industry: 'SaaS', location: 'Austin, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 89 },
    { domain: 'pixelcraft.design', name: 'PixelCraft', industry: 'Design Tech', location: 'Los Angeles, USA', employeeCount: '51-200', revenue: '$5M - $10M', relevanceScore: 88 },
    { domain: 'quantixlabs.ai', name: 'Quantix Labs', industry: 'AI/ML', location: 'Palo Alto, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 87 },
    { domain: 'nexgensystems.com', name: 'NexGen Systems', industry: 'Enterprise Software', location: 'Chicago, USA', employeeCount: '501-1000', revenue: '$50M - $100M', relevanceScore: 86 },
    { domain: 'zenithai.com', name: 'Zenith AI', industry: 'Artificial Intelligence', location: 'New York, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 85 },
    { domain: 'pulseanalytics.io', name: 'Pulse Analytics', industry: 'Business Intelligence', location: 'Denver, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 84 },
    { domain: 'velocify.com', name: 'Velocify', industry: 'Sales Tech', location: 'San Diego, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 83 },
    { domain: 'streamline.io', name: 'Streamline.io', industry: 'Workflow Automation', location: 'Portland, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 82 },
    { domain: 'clearpath.dev', name: 'ClearPath', industry: 'DevOps Tools', location: 'Atlanta, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 81 },
    { domain: 'beaconlabs.io', name: 'Beacon Labs', industry: 'IoT Platform', location: 'Miami, USA', employeeCount: '51-200', revenue: '$5M - $10M', relevanceScore: 80 },
    { domain: 'quantumedge.ai', name: 'Quantum Edge', industry: 'Edge Computing', location: 'Phoenix, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 79 },
    { domain: 'infinitystack.com', name: 'Infinity Stack', industry: 'Infrastructure', location: 'Dallas, USA', employeeCount: '501-1000', revenue: '$50M - $100M', relevanceScore: 78 },
    { domain: 'novasystems.io', name: 'Nova Systems', industry: 'Cybersecurity', location: 'Washington DC, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 77 },
    { domain: 'pinnacletech.com', name: 'Pinnacle Tech', industry: 'FinTech', location: 'Charlotte, USA', employeeCount: '501-1000', revenue: '$50M - $100M', relevanceScore: 76 },
    { domain: 'horizonai.co', name: 'Horizon AI', industry: 'Computer Vision', location: 'Pittsburgh, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 75 },
    { domain: 'summitcloud.io', name: 'Summit Cloud', industry: 'Cloud Services', location: 'Salt Lake City, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 74 },
    { domain: 'vertexlabs.ai', name: 'Vertex Labs', industry: 'ML Platform', location: 'San Jose, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 73 },
    { domain: 'prismanalytics.com', name: 'Prism Analytics', industry: 'Marketing Analytics', location: 'Minneapolis, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 72 },
    { domain: 'catalystai.io', name: 'Catalyst AI', industry: 'AI Platform', location: 'Nashville, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 71 },
    { domain: 'forgesystems.dev', name: 'Forge Systems', industry: 'Developer Tools', location: 'Raleigh, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 70 },
    { domain: 'axionlabs.com', name: 'Axion Labs', industry: 'Data Platform', location: 'Columbus, USA', employeeCount: '51-200', revenue: '$10M - $25M', relevanceScore: 69 },
    { domain: 'solsticetech.io', name: 'Solstice Tech', industry: 'HR Tech', location: 'Indianapolis, USA', employeeCount: '201-500', revenue: '$25M - $50M', relevanceScore: 68 },
  ];

  // Shuffle and return random subset (18-25 companies)
  const shuffled = [...mockCompanies].sort(() => Math.random() - 0.5);
  const count = Math.floor(Math.random() * 8) + 18; // 18-25 companies
  return shuffled.slice(0, count).sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
};

const EXAMPLE_QUERIES = [
  "SaaS companies in the US with 50-500 employees that have raised Series A or B funding",
  "E-commerce companies in Europe with revenue between $5M and $50M",
  "Healthcare tech startups in North America using modern tech stack",
  "B2B software companies with remote-first culture and growing engineering teams",
];

export const Step1NLFilter: React.FC = () => {
  const { state, setCampaignId, nextStep, setLoading } = useCampaignWizard();
  
  const [nlQuery, setNlQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [companies, setCompanies] = useState<NLCompanyResult[]>([]);
  const [parsedIntent, setParsedIntent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Backend API integration
  const [createCampaignFromCSVImport, { isLoading: isCreating }] = useCreateCampaignFromCSVImportMutation();
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Poll for campaign status
  const { data: campaignDetailsData } = useGetCampaignDetailsQuery(
    createdCampaignId
      ? { campaign_id: createdCampaignId, page: 1, limit: 1 }
      : { campaign_id: '', page: 1, limit: 1 },
    {
      skip: !createdCampaignId || !isPolling,
      pollingInterval: createdCampaignId && isPolling ? 3000 : 0,
    }
  );

  // Handle polling result
  useEffect(() => {
    if (!createdCampaignId || !isPolling) return;

    const campaign = campaignDetailsData?.data?.campaign;
    const csvImportStatus = campaign?.csv_import;
    const prospectingCycleStatus = campaign?.prospecting_cycle?.status;

    // Update progress
    if (csvImportStatus?.processed_count !== undefined && csvImportStatus?.total_count) {
      const progress = Math.round((csvImportStatus.processed_count / csvImportStatus.total_count) * 100);
      setLoading(true, `Enriching companies... (${csvImportStatus.processed_count}/${csvImportStatus.total_count})`, progress);
    }

    // Check if completed
    if (csvImportStatus?.status === 'completed' || prospectingCycleStatus === 'company_qualification') {
      setIsPolling(false);
      setLoading(false);
      nextStep();
    } else if (csvImportStatus?.status === 'failed') {
      setIsPolling(false);
      setLoading(false);
      setError(csvImportStatus?.error || 'Failed to process companies');
    }
  }, [campaignDetailsData, createdCampaignId, isPolling, nextStep, setLoading]);

  const handleSearch = async () => {
    if (!nlQuery.trim()) {
      setError('Please describe your target companies');
      return;
    }

    setIsSearching(true);
    setError(null);
    setCompanies([]);
    setLoading(true, 'Understanding your query...', 0);

    try {
      // Mock parsed intent
      setParsedIntent(`Searching for: ${nlQuery.slice(0, 100)}${nlQuery.length > 100 ? '...' : ''}`);
      
      // Call mock external NL API
      const results = await fetchCompaniesFromNLAPI(nlQuery);
      setCompanies(results);
      
      setIsSearching(false);
      setLoading(false);
    } catch (err) {
      setError('Failed to process your query. Please try again.');
      setIsSearching(false);
      setLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setNlQuery(example);
  };

  const handleContinue = async () => {
    if (companies.length === 0) return;

    setError(null);
    setLoading(true, 'Creating campaign and processing companies...', 0);

    try {
      // Extract domains from NL results
      const domains = companies.map(c => c.domain);
      
      // Use products selected in ProductSelection step
      const productNames = state.selectedProducts.join(',');

      // Use same API as CSV import, but with different campaign_type
      const payload = {
        campaign_name: state.campaignName, // Required unique campaign name
        company_domains: domains,
        product_name: productNames || undefined,
        campaign_type: 'nl_filter',  // NL Filter campaign type
        prospecting_cycle_status: 'prospecting',
      };

      const response = await createCampaignFromCSVImport(payload).unwrap();
      const newCampaignId = response?.data?.campaign_id;
      const totalCompanies = response?.data?.total_companies || domains.length;

      if (!newCampaignId) {
        throw new Error('campaign_id missing in response');
      }

      setCreatedCampaignId(newCampaignId);
      setCampaignId(newCampaignId);

      // Start polling for processing completion
      setLoading(true, `Processing ${totalCompanies} companies... (0/${totalCompanies})`, 0);
      setIsPolling(true);
    } catch (e: unknown) {
      console.error(e);
      const errorMessage = e instanceof Error ? e.message : 'Failed to create campaign';
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setNlQuery('');
    setCompanies([]);
    setParsedIntent(null);
    setError(null);
    setCreatedCampaignId(null);
    setIsPolling(false);
  };

  const isProcessing = isCreating || isPolling;

  return (
    <div className="step-container step-nl-filter">
      <div className="step-header">
        <h2>Find All - Natural Language</h2>
        <p>Describe your ideal target companies in plain English</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem', padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* NL Input */}
      <div className="nl-input-section">
        <div className="nl-input-wrapper">
          <textarea
            placeholder="Describe the companies you want to target...&#10;&#10;Example: SaaS companies in the US with 50-500 employees that have raised Series A funding"
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            disabled={isSearching || companies.length > 0 || isProcessing}
            rows={4}
          />
          {companies.length > 0 && !isProcessing && (
            <button className="clear-input-btn" onClick={handleReset}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
        </div>

        {/* Example Queries */}
        {companies.length === 0 && !isSearching && !isProcessing && (
          <div className="example-queries">
            <span className="examples-label">Try an example:</span>
            <div className="examples-list">
              {EXAMPLE_QUERIES.map((example, i) => (
                <button
                  key={i}
                  className="example-chip"
                  onClick={() => handleExampleClick(example)}
                >
                  {example.slice(0, 40)}...
                </button>
              ))}
            </div>
          </div>
        )}

        {companies.length === 0 && !isProcessing && (
          <button
            className="btn-primary search-btn"
            onClick={handleSearch}
            disabled={isSearching || !nlQuery.trim()}
          >
            {isSearching ? (
              <>
                <span className="spinner-small" />
                Processing...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Find Companies
              </>
            )}
          </button>
        )}
      </div>

      {/* Processing Animation */}
      {isSearching && (
        <div className="nl-processing">
          <div className="processing-steps">
            <div className="processing-step active">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </span>
              <span>Understanding intent</span>
            </div>
            <div className="processing-step">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                </svg>
              </span>
              <span>Building query</span>
            </div>
            <div className="processing-step">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </span>
              <span>Searching</span>
            </div>
          </div>
        </div>
      )}

      {/* Parsed Intent */}
      {parsedIntent && companies.length > 0 && (
        <div className="parsed-intent-banner">
          <div className="intent-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
            </svg>
          </div>
          <span>{parsedIntent}</span>
        </div>
      )}

      {/* Results */}
      {companies.length > 0 && (
        <div className="nl-results">
          <div className="results-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {companies.length} Companies Found
            </h3>
            <p>Based on your natural language query</p>
          </div>

          <div className="companies-preview-grid">
            {companies.slice(0, 8).map((company, index) => (
              <div 
                key={company.domain} 
                className="company-preview-card"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="relevance-badge">{company.relevanceScore}%</div>
                <h4>{company.name}</h4>
                <div className="company-meta">
                  <span className="tag">{company.industry}</span>
                  <span className="tag">{company.location}</span>
                </div>
                <div className="company-stats">
                  <span>{company.employeeCount} employees</span>
                  <span className="domain-text">{company.domain}</span>
                </div>
              </div>
            ))}
          </div>
          
          {companies.length > 8 && (
            <div className="more-results">
              +{companies.length - 8} more companies match your criteria
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        {companies.length > 0 && !isProcessing && (
          <button className="btn-secondary" onClick={handleReset}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2.5 2v6h6"/>
              <path d="M21.5 22v-6h-6"/>
              <path d="M22 11.5A10 10 0 0 0 3.2 7.2"/>
              <path d="M2 12.5a10 10 0 0 0 18.8 4.2"/>
            </svg>
            New Search
          </button>
        )}
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={companies.length === 0 || isProcessing}
        >
          {isProcessing ? (
            <>
              <span className="spinner-small" />
              Processing...
            </>
          ) : (
            <>
              Continue to Company Qualification
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Step1NLFilter;
