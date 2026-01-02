import React, { useState, useEffect } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

interface EnrichmentStatus {
  companyId: string;
  status: 'pending' | 'enriching' | 'enriched' | 'failed';
  enrichedData?: {
    industry?: string;
    employeeCount?: string;
    revenue?: string;
    description?: string;
    technologies?: string[];
    fundingStage?: string;
  };
}

export const StepCompanyEnrichment: React.FC = () => {
  const { state, setQualifiedCompanies, nextStep, prevStep, setLoading } = useCampaignWizard();
  const [enrichmentStatuses, setEnrichmentStatuses] = useState<EnrichmentStatus[]>([]);
  const [isEnriching, setIsEnriching] = useState(false);
  const [enrichmentComplete, setEnrichmentComplete] = useState(false);

  // Initialize enrichment statuses
  useEffect(() => {
    if (state.qualifiedCompanies.length > 0 && enrichmentStatuses.length === 0) {
      setEnrichmentStatuses(
        state.qualifiedCompanies.map((company) => ({
          companyId: company.id,
          status: 'pending',
        }))
      );
    }
  }, [state.qualifiedCompanies, enrichmentStatuses.length]);

  const handleStartEnrichment = async () => {
    setIsEnriching(true);
    setLoading(true, 'Enriching company data...', 0);

    // Simulate enrichment process with staggered updates
    const totalCompanies = state.qualifiedCompanies.length;
    
    for (let i = 0; i < totalCompanies; i++) {
      const company = state.qualifiedCompanies[i];
      
      // Update status to enriching
      setEnrichmentStatuses((prev) =>
        prev.map((s) =>
          s.companyId === company.id ? { ...s, status: 'enriching' } : s
        )
      );

      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 300 + Math.random() * 200));

      // Mock enriched data with realistic variations
      const techStacks = [
        ['React', 'Node.js', 'AWS', 'PostgreSQL'],
        ['Vue.js', 'Python', 'GCP', 'MongoDB'],
        ['Angular', 'Java', 'Azure', 'MySQL'],
        ['Next.js', 'Go', 'AWS', 'Redis'],
        ['Svelte', 'Rust', 'Cloudflare', 'DynamoDB'],
      ];
      const descriptions = [
        `${company.name} is a market leader in ${company.industry || 'technology'}, serving Fortune 500 companies with innovative solutions.`,
        `${company.name} provides cutting-edge ${company.industry || 'software'} solutions that help businesses scale efficiently.`,
        `Founded to transform the ${company.industry || 'industry'} sector, ${company.name} has rapidly grown to become a trusted partner for enterprise clients.`,
        `${company.name} specializes in next-generation ${company.industry || 'technology'} products that drive digital transformation.`,
      ];
      const enrichedData = {
        industry: company.industry || 'Technology',
        employeeCount: company.employeeCount || '51-200',
        revenue: company.revenue || '$5M - $10M',
        description: descriptions[Math.floor(Math.random() * descriptions.length)],
        technologies: techStacks[Math.floor(Math.random() * techStacks.length)],
        fundingStage: ['Seed', 'Series A', 'Series B', 'Series C', 'Growth', 'Public'][Math.floor(Math.random() * 6)],
        linkedinFollowers: `${Math.floor(Math.random() * 50 + 5)}K`,
        yearFounded: 2010 + Math.floor(Math.random() * 14),
      };

      // Update status to enriched
      setEnrichmentStatuses((prev) =>
        prev.map((s) =>
          s.companyId === company.id
            ? { ...s, status: 'enriched', enrichedData }
            : s
        )
      );

      // Update loading progress
      setLoading(true, `Enriching companies... (${i + 1}/${totalCompanies})`, i + 1);
    }

    // Update qualified companies with enriched data
    setQualifiedCompanies(
      state.qualifiedCompanies.map((company) => {
        const enrichment = enrichmentStatuses.find((s) => s.companyId === company.id);
        return {
          ...company,
          ...(enrichment?.enrichedData || {}),
        };
      })
    );

    setIsEnriching(false);
    setEnrichmentComplete(true);
    setLoading(false);
  };

  const enrichedCount = enrichmentStatuses.filter((s) => s.status === 'enriched').length;
  const totalCount = enrichmentStatuses.length;
  const progressPercent = totalCount > 0 ? (enrichedCount / totalCount) * 100 : 0;

  return (
    <div className="step-container step-enrichment">
      <div className="step-header">
        <h2>Company Enrichment</h2>
        <p>
          {!enrichmentComplete
            ? 'Enrich company profiles with additional data for better qualification'
            : 'Company data has been enriched successfully'}
        </p>
      </div>

      {/* Enrichment Status Overview */}
      <div className="enrichment-overview">
        <div className="enrichment-stats">
          <div className="stat-card">
            <div className="stat-value">{totalCount}</div>
            <div className="stat-label">Total Companies</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{enrichedCount}</div>
            <div className="stat-label">Enriched</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{totalCount - enrichedCount}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>

        {/* Progress Bar */}
        {(isEnriching || enrichmentComplete) && (
          <div className="enrichment-progress">
            <div className="progress-bar-container">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="progress-text">
              {enrichedCount} / {totalCount} companies enriched
            </span>
          </div>
        )}
      </div>

      {/* Company List with Enrichment Status */}
      <div className="enrichment-company-list">
        <div className="list-header">
          <h3>Companies</h3>
        </div>
        <div className="company-enrichment-items">
          {state.qualifiedCompanies.slice(0, 10).map((company) => {
            const status = enrichmentStatuses.find((s) => s.companyId === company.id);
            return (
              <div key={company.id} className={`enrichment-item ${status?.status || 'pending'}`}>
                <div className="company-info">
                  <span className="company-name">{company.name}</span>
                  <span className="company-industry">{company.industry}</span>
                </div>
                <div className="enrichment-status">
                  {status?.status === 'pending' && (
                    <span className="status-badge pending">Pending</span>
                  )}
                  {status?.status === 'enriching' && (
                    <span className="status-badge enriching">
                      <span className="spinner-small" />
                      Enriching...
                    </span>
                  )}
                  {status?.status === 'enriched' && (
                    <span className="status-badge enriched">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Enriched
                    </span>
                  )}
                  {status?.status === 'failed' && (
                    <span className="status-badge failed">Failed</span>
                  )}
                </div>
              </div>
            );
          })}
          {state.qualifiedCompanies.length > 10 && (
            <div className="more-companies">
              +{state.qualifiedCompanies.length - 10} more companies
            </div>
          )}
        </div>
      </div>

      {/* Enriched Data Preview (when complete) */}
      {enrichmentComplete && enrichmentStatuses.length > 0 && (
        <div className="enrichment-preview">
          <h3>Enrichment Summary</h3>
          <div className="enrichment-summary-grid">
            <div className="summary-item">
              <span className="summary-label">Industries Identified</span>
              <span className="summary-value">
                {new Set(state.qualifiedCompanies.map((c) => c.industry)).size}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Avg. Enrichment Quality</span>
              <span className="summary-value">94%</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Data Points Added</span>
              <span className="summary-value">{enrichedCount * 6}</span>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        <button className="btn-secondary" onClick={prevStep}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>

        {!enrichmentComplete ? (
          <button
            className="btn-primary btn-large"
            onClick={handleStartEnrichment}
            disabled={isEnriching || totalCount === 0}
          >
            {isEnriching ? (
              <>
                <span className="spinner-small" />
                Enriching...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
                </svg>
                Start Enrichment
              </>
            )}
          </button>
        ) : (
          <button className="btn-primary btn-large" onClick={nextStep}>
            Continue
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default StepCompanyEnrichment;

