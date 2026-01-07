import React, { useState, useEffect } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import {
  useCreateCampaignFromCSVImportMutation,
  useGetCampaignDetailsQuery,
} from '../../store';

// Mock external API response for similar companies
// In production, this would be replaced with a real API call
interface SimilarCompanyResult {
  domain: string;
  name: string;
  similarityScore: number;
  industry?: string;
  location?: string;
  employeeCount?: string;
}

// Mock function simulating external "Similar Companies" API
const fetchSimilarCompaniesFromExternalAPI = async (
  _sourceDomain: string
): Promise<SimilarCompanyResult[]> => {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Mock response data - in production, this would be a real API call
  const mockSimilarCompanies: SimilarCompanyResult[] = [
    { domain: 'attentive.com', name: 'Attentive', similarityScore: 95, industry: 'Marketing Tech', location: 'New York, USA', employeeCount: '501-1000' },
    { domain: 'klaviyo.com', name: 'Klaviyo', similarityScore: 92, industry: 'E-commerce Marketing', location: 'Boston, USA', employeeCount: '1001-2000' },
    { domain: 'braze.com', name: 'Braze', similarityScore: 89, industry: 'Customer Engagement', location: 'New York, USA', employeeCount: '1001-2000' },
    { domain: 'iterable.com', name: 'Iterable', similarityScore: 87, industry: 'Marketing Automation', location: 'San Francisco, USA', employeeCount: '501-1000' },
    { domain: 'customer.io', name: 'Customer.io', similarityScore: 85, industry: 'Marketing Automation', location: 'Portland, USA', employeeCount: '201-500' },
    { domain: 'postscript.io', name: 'Postscript', similarityScore: 84, industry: 'SMS Marketing', location: 'Scottsdale, USA', employeeCount: '201-500' },
    { domain: 'yotpo.com', name: 'Yotpo', similarityScore: 82, industry: 'E-commerce Marketing', location: 'New York, USA', employeeCount: '501-1000' },
    { domain: 'gorgias.com', name: 'Gorgias', similarityScore: 80, industry: 'Customer Support', location: 'San Francisco, USA', employeeCount: '201-500' },
    { domain: 'rechargepayments.com', name: 'Recharge', similarityScore: 79, industry: 'Subscription Commerce', location: 'Santa Monica, USA', employeeCount: '501-1000' },
    { domain: 'sendlane.com', name: 'Sendlane', similarityScore: 78, industry: 'Email Marketing', location: 'San Diego, USA', employeeCount: '51-200' },
    { domain: 'omnisend.com', name: 'Omnisend', similarityScore: 77, industry: 'E-commerce Marketing', location: 'London, UK', employeeCount: '201-500' },
    { domain: 'drip.com', name: 'Drip', similarityScore: 76, industry: 'Marketing Automation', location: 'Minneapolis, USA', employeeCount: '51-200' },
    { domain: 'privy.com', name: 'Privy', similarityScore: 75, industry: 'E-commerce Conversion', location: 'Boston, USA', employeeCount: '51-200' },
    { domain: 'stamped.io', name: 'Stamped', similarityScore: 74, industry: 'Reviews & UGC', location: 'Toronto, Canada', employeeCount: '51-200' },
    { domain: 'smile.io', name: 'Smile.io', similarityScore: 73, industry: 'Loyalty & Rewards', location: 'Kitchener, Canada', employeeCount: '51-200' },
    { domain: 'loyaltylion.com', name: 'LoyaltyLion', similarityScore: 72, industry: 'Loyalty Platform', location: 'London, UK', employeeCount: '51-200' },
    { domain: 'rebuyengine.com', name: 'Rebuy', similarityScore: 71, industry: 'Personalization', location: 'Minneapolis, USA', employeeCount: '51-200' },
    { domain: 'nosto.com', name: 'Nosto', similarityScore: 70, industry: 'E-commerce Personalization', location: 'Helsinki, Finland', employeeCount: '201-500' },
    { domain: 'dynamicyield.com', name: 'Dynamic Yield', similarityScore: 69, industry: 'Personalization', location: 'Tel Aviv, Israel', employeeCount: '501-1000' },
    { domain: 'bloomreach.com', name: 'Bloomreach', similarityScore: 68, industry: 'Commerce Experience', location: 'Mountain View, USA', employeeCount: '501-1000' },
  ];

  // Shuffle and return random subset (15-20 companies)
  const shuffled = [...mockSimilarCompanies].sort(() => Math.random() - 0.5);
  const count = Math.floor(Math.random() * 6) + 15; // 15-20 companies
  return shuffled.slice(0, count).sort((a, b) => b.similarityScore - a.similarityScore);
};

export const Step1SimilarCompanies: React.FC = () => {
  const { state, setCampaignId, nextStep, setLoading } = useCampaignWizard();
  
  const [companyUrl, setCompanyUrl] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [sourceCompany, setSourceCompany] = useState<{ name: string; domain: string } | null>(null);
  const [similarCompanies, setSimilarCompanies] = useState<SimilarCompanyResult[]>([]);
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
      setError(csvImportStatus?.error || 'Failed to process similar companies');
    }
  }, [campaignDetailsData, createdCampaignId, isPolling, nextStep, setLoading]);

  const extractDomain = (url: string): string => {
    try {
      const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
      return parsed.hostname.replace('www.', '');
    } catch {
      return url.replace('www.', '');
    }
  };

  const handleFindSimilar = async () => {
    if (!companyUrl.trim()) {
      setError('Please enter a company URL');
      return;
    }

    setIsSearching(true);
    setError(null);
    setSimilarCompanies([]);
    setLoading(true, 'Finding similar companies...', 0);

    try {
      const domain = extractDomain(companyUrl);
      const companyName = domain.split('.')[0].charAt(0).toUpperCase() + domain.split('.')[0].slice(1);

      setSourceCompany({ name: companyName, domain });

      // Call mock external API to get similar companies
      const companies = await fetchSimilarCompaniesFromExternalAPI(domain);
      setSimilarCompanies(companies);
      
      setIsSearching(false);
      setLoading(false);
    } catch (err) {
      setError('Failed to find similar companies. Please try again.');
      setIsSearching(false);
      setLoading(false);
    }
  };

  const handleContinue = async () => {
    if (similarCompanies.length === 0) return;

    setError(null);
    setLoading(true, 'Creating campaign and processing companies...', 0);

    try {
      // Extract domains from similar companies
      const domains = similarCompanies.map(c => c.domain);
      
      // Use products selected in ProductSelection step
      const productNames = state.selectedProducts.join(',');

      // Use same API as CSV import, but with different campaign_type
      const payload = {
        campaign_name: state.campaignName, // Required unique campaign name
        company_domains: domains,
        product_name: productNames || undefined,
        campaign_type: 'similar_companies',  // Different campaign type
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
      setLoading(true, `Processing ${totalCompanies} similar companies... (0/${totalCompanies})`, 0);
      setIsPolling(true);
    } catch (e: unknown) {
      console.error(e);
      const errorMessage = e instanceof Error ? e.message : 'Failed to create campaign';
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCompanyUrl('');
    setSourceCompany(null);
    setSimilarCompanies([]);
    setError(null);
    setCreatedCampaignId(null);
    setIsPolling(false);
  };

  const isProcessing = isCreating || isPolling;

  return (
    <div className="step-container step-similar-companies">
      <div className="step-header">
        <h2>Similar Companies Search</h2>
        <p>Enter a company URL to find similar companies you can target</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem', padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* URL Input */}
      <div className="similar-company-input">
        <div className="input-group-large">
          <label htmlFor="source-company-url">Reference Company URL</label>
          <div className="url-input-wrapper">
            <div className="url-prefix">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <input
              id="source-company-url"
              type="text"
              placeholder="e.g., salesforce.com or https://hubspot.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isSearching && !isProcessing && handleFindSimilar()}
              disabled={isSearching || similarCompanies.length > 0 || isProcessing}
            />
            {similarCompanies.length > 0 && !isProcessing && (
              <button className="clear-input-btn" onClick={handleReset}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>
        </div>

        {similarCompanies.length === 0 && !isProcessing && (
          <button
            className="btn-primary search-btn"
            onClick={handleFindSimilar}
            disabled={isSearching || !companyUrl.trim()}
          >
            {isSearching ? (
              <>
                <span className="spinner-small" />
                Searching...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Find Similar Companies
              </>
            )}
          </button>
        )}
      </div>

      {/* Source Company Info */}
      {sourceCompany && (
        <div className="source-company-banner">
          <div className="source-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
          </div>
          <div className="source-info">
            <span className="source-label">Finding companies similar to</span>
            <span className="source-name">{sourceCompany.name}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {similarCompanies.length > 0 && (
        <div className="similar-results">
          <div className="results-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {similarCompanies.length} Similar Companies Found
            </h3>
            <p>Companies are ranked by similarity score</p>
          </div>

          <div className="similar-companies-list">
            {similarCompanies.slice(0, 10).map((company, index) => (
              <div 
                key={company.domain} 
                className="similar-company-card"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="similarity-badge">
                  {company.similarityScore}%
                </div>
                <div className="company-info">
                  <h4>{company.name}</h4>
                  <div className="company-meta">
                    <span className="tag">{company.industry}</span>
                    <span className="tag">{company.location}</span>
                    <span className="tag">{company.employeeCount}</span>
                  </div>
                  <span className="domain-text">{company.domain}</span>
                </div>
              </div>
            ))}
            {similarCompanies.length > 10 && (
              <div className="more-companies-indicator">
                +{similarCompanies.length - 10} more similar companies
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        {similarCompanies.length > 0 && !isProcessing && (
          <button className="btn-secondary" onClick={handleReset}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2.5 2v6h6"/>
              <path d="M21.5 22v-6h-6"/>
              <path d="M22 11.5A10 10 0 0 0 3.2 7.2"/>
              <path d="M2 12.5a10 10 0 0 0 18.8 4.2"/>
            </svg>
            Search Again
          </button>
        )}
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={similarCompanies.length === 0 || isProcessing}
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

export default Step1SimilarCompanies;
