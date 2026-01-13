import React, { useState, useEffect, useRef } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import {
  useCreateCampaignFromSimilarSearchMutation,
  useGetCampaignStatusMinimalQuery,
} from '../../store';

export const Step1SimilarCompanies: React.FC = () => {
  const { state, setCampaignId, nextStep, setLoading } = useCampaignWizard();
  
  const [companyUrl, setCompanyUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isCheckingResume, setIsCheckingResume] = useState(false);
  const hasCheckedResume = useRef(false);
  
  // Backend API integration
  const [createCampaignFromSimilarSearch, { isLoading: isCreating }] = useCreateCampaignFromSimilarSearchMutation();

  // Determine which campaign ID to poll - either newly created or resumed from state
  const activeCampaignId = createdCampaignId || (isPolling || isCheckingResume ? state.campaignId : null);

  // Poll for campaign status change from 'started' to 'company_qualification_select'
  // Also used for initial resume check
  const { data: campaignStatusData } = useGetCampaignStatusMinimalQuery(
    activeCampaignId
      ? { campaign_id: activeCampaignId }
      : { campaign_id: '' },
    {
      skip: !activeCampaignId,
      pollingInterval: activeCampaignId && isPolling ? 3000 : 0,
    }
  );

  // Check if we're resuming a campaign with 'started' status (only for similar_companies type)
  useEffect(() => {
    if (hasCheckedResume.current) return;
    if (!state.campaignId || state.campaignType !== 'similar_companies') return;
    
    // Trigger a status check to see if we need to resume polling
    setIsCheckingResume(true);
  }, [state.campaignId, state.campaignType]);

  // Handle resume check result
  useEffect(() => {
    if (!isCheckingResume || hasCheckedResume.current) return;
    if (!campaignStatusData) return;
    
    hasCheckedResume.current = true;
    setIsCheckingResume(false);
    
    const prospectingCycleStatus = campaignStatusData?.data?.prospecting_cycle?.status;
    
    // If campaign is in 'started' status, resume polling with loader
    if (prospectingCycleStatus === 'started') {
      setLoading(true, 'Fetching similar companies...', 0);
      setIsPolling(true);
    }
  }, [campaignStatusData, isCheckingResume, setLoading]);

  // Handle polling result
  useEffect(() => {
    if (!activeCampaignId || !isPolling) return;

    const prospectingCycleStatus = campaignStatusData?.data?.prospecting_cycle?.status;
    const aiProspectingStatus = campaignStatusData?.data?.ai_prospecting?.status;

    // Update progress message based on status
    if (aiProspectingStatus === 'processing') {
      const processed = campaignStatusData?.data?.ai_prospecting?.processed_count || 0;
      const total = campaignStatusData?.data?.ai_prospecting?.total_count || 0;
      if (total > 0) {
        setLoading(true, `Enriching similar companies... (${processed}/${total})`, Math.round((processed / total) * 100));
      }
    }

    // Check if processing is complete - status changed to 'company_qualification_select'
    if (prospectingCycleStatus === 'company_qualification_select' || prospectingCycleStatus === 'company_qualification') {
      setIsPolling(false);
      setLoading(false);
      nextStep();
    } else if (aiProspectingStatus === 'failed') {
      setIsPolling(false);
      setLoading(false);
      setError(campaignStatusData?.data?.ai_prospecting?.error || 'Failed to find similar companies');
    }
  }, [campaignStatusData, activeCampaignId, isPolling, nextStep, setLoading]);

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

    setError(null);
    setLoading(true, 'Creating campaign and finding similar companies...', 0);

    try {
      const domain = extractDomain(companyUrl);
      
      // Use products selected in ProductSelection step
      const productNames = state.selectedProducts.join(',');

      const payload = {
        campaign_name: state.campaignName,
        source_domain: domain,
        product_name: productNames || undefined,
        campaign_type: 'similar_companies',
        prospecting_cycle_status: 'started',
      };

      const response = await createCampaignFromSimilarSearch(payload).unwrap();
      const newCampaignId = response?.data?.campaign_id;

      if (!newCampaignId) {
        throw new Error('campaign_id missing in response');
      }

      setCreatedCampaignId(newCampaignId);
      setCampaignId(newCampaignId);

      // Start polling for status change
      setLoading(true, 'Fetching similar companies...', 0);
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
    setError(null);
    setCreatedCampaignId(null);
    setIsPolling(false);
    setLoading(false);
  };

  const isProcessing = isCreating || isPolling || isCheckingResume;

  return (
    <div className="step-container step-similar-companies">
      <div className="step-header">
        <h2>Similar Companies Search</h2>
        <p>Enter a company URL to find similar companies you can target</p>
      </div>

      {/* Loading Overlay */}
      {(state.isLoading || isProcessing) && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>{state.loadingMessage || 'Processing...'}</h3>
            {(activeCampaignId || state.campaignId) && (
              <p style={{ marginTop: 8, opacity: 0.85 }}>Campaign ID: {activeCampaignId || state.campaignId}</p>
            )}
          </div>
        </div>
      )}

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
              onKeyDown={(e) => e.key === 'Enter' && !isProcessing && handleFindSimilar()}
              disabled={isProcessing}
            />
            {createdCampaignId && !isProcessing && (
              <button className="clear-input-btn" onClick={handleReset}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>
        </div>

        {!isProcessing && (
          <button
            className="btn-primary search-btn"
            onClick={handleFindSimilar}
            disabled={isProcessing || !companyUrl.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            Find Similar Companies
          </button>
        )}
      </div>

      {/* Info Banner */}
      <div className="info-banner">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <p>
          <strong>Similar Companies Flow:</strong> We'll find companies similar to the one you enter, 
          enrich them with Apollo data, and then you can qualify them in the next step.
        </p>
      </div>

      {/* Actions */}
      <div className="step-actions">
        <button
          className="btn-primary btn-large"
          onClick={handleFindSimilar}
          disabled={!companyUrl.trim() || isProcessing}
        >
          {isProcessing ? (
            <>
              <span className="spinner-small" />
              Fetching companies...
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
