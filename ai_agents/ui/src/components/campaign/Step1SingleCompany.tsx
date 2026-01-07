import React, { useState, useEffect } from 'react';
import { useCampaignWizard, type Company } from './NewCampaignWizard';
import {
  useCreateCampaignFromSingleCompanyMutation,
  useGetCampaignDetailsQuery,
  useGetApolloContactListMutation,
} from '../../store';

export const Step1SingleCompany: React.FC = () => {
  const { state, setCampaignId, setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  const [createCampaignFromSingleCompany, { isLoading: isCreating }] = useCreateCampaignFromSingleCompanyMutation();
  const [getApolloContactList] = useGetApolloContactListMutation();
  
  const [companyUrl, setCompanyUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [companyInfo, setCompanyInfo] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Polling for campaign status
  const { data: campaignDetailsData } = useGetCampaignDetailsQuery(
    createdCampaignId
      ? { campaign_id: createdCampaignId, page: 1, limit: 1 }
      : { campaign_id: '', page: 1, limit: 1 },
    {
      skip: !createdCampaignId || !isPolling,
      pollingInterval: createdCampaignId && isPolling ? 2000 : 0,
    }
  );

  // Effect to handle polling result
  useEffect(() => {
    if (!createdCampaignId || !isPolling) return;

    const campaign = campaignDetailsData?.data?.campaign;
    const singleCompanyStatus = campaign?.single_company?.status;
    const prospectingCycleStatus = campaign?.prospecting_cycle?.status;

    // Check if single company search is completed
    if (singleCompanyStatus === 'completed' || prospectingCycleStatus === 'contact_qualification') {
      setIsPolling(false);
      setLoading(false);
      setIsValidating(false);

      // Get company data from campaign
      const companies = campaignDetailsData?.data?.companies || [];
      if (companies.length > 0) {
        const companyData = companies[0];
        // Support both new format (company.identifiers) and legacy format (company_details)
        const companyDoc = companyData.company || {};
        const identifiers = companyDoc.identifiers || {};
        const profile = companyDoc.profile || {};
        const location = companyDoc.location || {};
        
        // Transform to Company type
        const company: Company = {
          id: companyData.company_id || companyData._id,
          name: identifiers.name || campaign?.single_company?.company_name || 'Unknown Company',
          website: identifiers.website_url || `https://${identifiers.source_domain || campaign?.single_company?.domain || companyUrl}`,
          industry: Array.isArray(profile.industry) ? profile.industry.join(', ') : String(profile.industry || ''),
          employeeCount: Array.isArray(profile.employee_count) ? profile.employee_count.join(', ') : (profile.employee_count ? String(profile.employee_count) : 'Unknown'),
          revenue: profile.revenue_max ? `$${profile.revenue_min || '0'}M - $${profile.revenue_max}M` : 'Unknown',
          location: location.name || 'Unknown',
          linkedinUrl: (companyDoc.metadata?.api_response?.linkedin_url as string) || '',
          isQualified: true,
          qualificationStatus: 'qualified' as const,
          contacts: [],
          syncStatus: 'not_synced' as const,
          personalization: {
            messageStatus: 'pending' as const,
            deckStatus: 'pending' as const,
          },
        };
        
        setCompanyInfo(company);
      } else {
        // Use data from campaign single_company field
        const company: Company = {
          id: 'single-company-1',
          name: campaign?.single_company?.company_name || 'Company',
          website: `https://${campaign?.single_company?.domain || companyUrl}`,
          industry: '',
          employeeCount: 'Unknown',
          revenue: 'Unknown',
          location: 'Unknown',
          linkedinUrl: '',
          isQualified: true,
          qualificationStatus: 'qualified' as const,
          contacts: [],
          syncStatus: 'not_synced' as const,
          personalization: {
            messageStatus: 'pending' as const,
            deckStatus: 'pending' as const,
          },
        };
        setCompanyInfo(company);
      }
    } else if (singleCompanyStatus === 'failed' || singleCompanyStatus === 'not_found') {
      setIsPolling(false);
      setLoading(false);
      setIsValidating(false);
      setError(campaign?.single_company?.error || 'Failed to find company. Please try a different URL.');
    }
  }, [campaignDetailsData, createdCampaignId, isPolling, setLoading, companyUrl]);

  const extractDomain = (url: string): string => {
    try {
      const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
      return parsed.hostname.replace('www.', '');
    } catch {
      return url.replace('www.', '');
    }
  };

  const handleValidateCompany = async () => {
    if (!companyUrl.trim()) {
      setError('Please enter a company URL');
      return;
    }

    setIsValidating(true);
    setError(null);
    setLoading(true, 'Creating campaign & searching for company...', 0);

    try {
      const domain = extractDomain(companyUrl);
      
      // Use products selected in ProductSelection step
      const productNames = state.selectedProducts.join(',');

      const payload = {
        campaign_name: state.campaignName, // Required unique campaign name
        company_domain: domain,
        product_name: productNames,
        campaign_type: 'single_company',
        prospecting_cycle_status: 'prospecting',
      };

      const res = await createCampaignFromSingleCompany(payload).unwrap();
      const newCampaignId = res?.data?.campaign_id;
      const companyExists = res?.data?.company_exists;
      
      if (!newCampaignId) {
        throw new Error('campaign_id missing in response');
      }

      setCreatedCampaignId(newCampaignId);
      setCampaignId(newCampaignId);
      
      if (companyExists) {
        // Company already exists in DB - no need to poll, status is already contact_qualification
        setLoading(true, 'Company found in database! Loading details...');
        setIsPolling(true); // Still poll once to get company details
      } else {
        // New company - need to wait for Apollo search
        setIsPolling(true);
        setLoading(true, 'Searching Apollo for company... Please wait...');
      }
    } catch (e: unknown) {
      console.error(e);
      const errorMessage = e instanceof Error ? e.message : 'Failed to create campaign';
      setError(errorMessage);
      setLoading(false);
      setIsValidating(false);
    }
  };

  const handleContinue = async () => {
    if (!companyInfo) return;
    
    const campaignId = createdCampaignId || state.campaignId;
    if (!campaignId) {
      setError('Campaign ID not found');
      return;
    }
    
    try {
      setLoading(true, 'Queueing contact fetch from Apollo...');
      
      // Call Apollo contact LIST API (queues contact fetching from Apollo)
      // This is the same as wide prospecting flow - NOT the enrich API
      // NOTE: This just queues the job - contacts will be fetched async via Kafka
      await getApolloContactList({
        campaign_id: campaignId,
        enrichment_status: false, // false = just fetch contacts, not enrich
      }).unwrap();
      
      setQualifiedCompanies([companyInfo]);
      // DON'T clear loading here - Step 3 (Contact Qualification) will poll and show loader
      // until contacts are actually fetched
      nextStep();
    } catch (e) {
      console.error('Failed to queue contact fetch:', e);
      setError('Failed to fetch contacts. Please try again.');
      setLoading(false);
    }
  };

  const handleClear = () => {
    setCompanyUrl('');
    setCompanyInfo(null);
    setError(null);
    setCreatedCampaignId(null);
    setIsPolling(false);
  };

  const isProcessing = isValidating || isCreating || isPolling;

  return (
    <div className="step-container step-single-company">
      <div className="step-header">
        <h2>Single Company URL</h2>
        <p>Enter the company URL to fetch information and contacts directly</p>
      </div>

      {/* Loading Overlay */}
      {(state.isLoading || isProcessing) && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>{state.loadingMessage || 'Processing...'}</h3>
            {createdCampaignId && (
              <p style={{ marginTop: 8, opacity: 0.85 }}>Campaign ID: {createdCampaignId}</p>
            )}
          </div>
        </div>
      )}

      {/* URL Input */}
      <div className="single-company-input">
        <div className="input-group-large">
          <label htmlFor="company-url">Company Website URL</label>
          <div className="url-input-wrapper">
            <div className="url-prefix">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <input
              id="company-url"
              type="text"
              placeholder="e.g., acme.com or https://acme.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isProcessing && handleValidateCompany()}
              disabled={isProcessing || !!companyInfo}
            />
            {companyInfo && (
              <button className="clear-input-btn" onClick={handleClear}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>
          {error && <span className="input-error">{error}</span>}
        </div>

        {!companyInfo && !isProcessing && (
          <button
            className="btn-primary validate-btn"
            onClick={handleValidateCompany}
            disabled={isProcessing || !companyUrl.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Fetch Company
          </button>
        )}
      </div>

      {/* Company Info Card */}
      {companyInfo && (
        <div className="company-info-card">
          <div className="company-card-header">
            <div className="company-avatar">
              {companyInfo.name.charAt(0).toUpperCase()}
            </div>
            <div className="company-main-info">
              <h3>{companyInfo.name}</h3>
              <a href={companyInfo.website} target="_blank" rel="noopener noreferrer" className="company-website">
                {companyInfo.website}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              </a>
            </div>
            <div className="company-qualified-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Pre-qualified
            </div>
          </div>

          <div className="company-details-grid">
            <div className="detail-item">
              <span className="detail-label">Industry</span>
              <span className="detail-value">{companyInfo.industry || 'Unknown'}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Employees</span>
              <span className="detail-value">{companyInfo.employeeCount}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Revenue</span>
              <span className="detail-value">{companyInfo.revenue}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Location</span>
              <span className="detail-value">{companyInfo.location}</span>
            </div>
          </div>

          {companyInfo.linkedinUrl && (
            <div className="company-linkedin">
              <a href={companyInfo.linkedinUrl} target="_blank" rel="noopener noreferrer">
                View on LinkedIn
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              </a>
            </div>
          )}
        </div>
      )}

      {/* Info Banner */}
      <div className="info-banner">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <p>
          <strong>Single Company Flow:</strong> This company will skip the Company Qualification step 
          and proceed directly to Contact Qualification.
        </p>
      </div>

      {/* Actions */}
      <div className="step-actions">
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={!companyInfo || isProcessing}
        >
          Continue to Contact Qualification
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Step1SingleCompany;
