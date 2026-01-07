import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetCampaignDetailsQuery } from '../store';
import type { CampaignCompany } from '../store';
import { InfoGrid, Loader, Pagination } from './shared';
import type { InfoGridItem } from './shared';

// Polling interval in milliseconds (5 seconds)
const POLLING_INTERVAL = 5000;

const statusColors: Record<string, { bg: string; text: string }> = {
  true: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  false: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  active: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  started: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  completed: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1' },
  draft: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  paused: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  high: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  medium: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  low: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
};

type CompanyStatusFilter = 'all' | 'true' | 'false';

const shortlistingApproachLabel = (value?: string) => {
  if (!value) return '-';
  const normalized = value.trim().toLowerCase();
  const map: Record<string, string> = {
    manual_company: 'Manual Company Shortlisting',
    overall_manual: 'Overall Manual Shortlisting (Company + Contact)',
    overall_ai: 'Overall AI Shortlisting (Company + Contact)',
  };
  return map[normalized] || value;
};

export const CampaignDetails = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<CompanyStatusFilter>('all');
  // Local-only (mock) overrides for manual shortlisting mode; keyed by campaign_company mapping `_id`
  const [manualCompanyStatus, setManualCompanyStatus] = useState<Record<string, boolean>>({});
  const limit = 10;

  // Convert filter value to API param
  const getCompanyStatusParam = (): boolean | undefined => {
    if (statusFilter === 'true') return true;
    if (statusFilter === 'false') return false;
    return undefined; // 'all' - don't send parameter
  };

  // State to track if polling is active
  const [isPolling, setIsPolling] = useState(false);

  // RTK Query hook with conditional polling
  const { data, isLoading, isFetching, error, refetch } = useGetCampaignDetailsQuery(
    {
      campaign_id: campaignId || '',
      company_status: getCompanyStatusParam(),
      page,
      limit,
    },
    { 
      skip: !campaignId,
      // Poll every 5 seconds only if campaign status is 'started'
      pollingInterval: isPolling ? POLLING_INTERVAL : 0,
    }
  );

  const campaign = data?.data?.campaign;
  const companies = data?.data?.companies || [];
  const pagination = data?.pagination;
  const isManualCompanyShortlisting =
    campaign?.shortlisting_approach === 'manual_company' ||
    campaign?.shortlisting_approach === 'overall_manual';

  const getEffectiveCompanyStatus = (company: CampaignCompany) => {
    const override = manualCompanyStatus[company._id];
    return override !== undefined ? override : company.company_status;
  };

  const displayedCompanies =
    statusFilter === 'all'
      ? companies
      : companies.filter(c => String(getEffectiveCompanyStatus(c)) === statusFilter);

  // Reset local overrides when switching campaigns
  useEffect(() => {
    setManualCompanyStatus({});
  }, [campaignId]);

  // Update polling state based on campaign lifecycle status
  useEffect(() => {
    if (campaign?.lifecycle?.status === 'started') {
      setIsPolling(true);
    } else {
      setIsPolling(false);
    }
  }, [campaign?.lifecycle?.status]);

  // Show polling indicator when fetching in background (not initial load)
  const isBackgroundFetching = isFetching && !isLoading;

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const getStatusStats = () => {
    const stats = { shortlisted: 0, notShortlisted: 0, total: displayedCompanies.length };
    displayedCompanies.forEach(c => {
      if (getEffectiveCompanyStatus(c)) stats.shortlisted++;
      else stats.notShortlisted++;
    });
    return stats;
  };

  const stats = getStatusStats();

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (pagination?.has_next) setPage(page + 1);
  };

  const handleStatusFilterChange = (newFilter: CompanyStatusFilter) => {
    setStatusFilter(newFilter);
    setPage(1); // Reset to first page when filter changes
  };

  const infoItems: InfoGridItem[] = campaign
    ? [
        { label: 'Business Team', value: campaign.ownership?.business_team || '-' },
        { label: 'Owner Email', value: campaign.ownership?.user_email || '-' },
        { label: 'HubSpot Email', value: campaign.ownership?.hubspot_email || '-' },
        { label: 'Shortlisting Approach', value: shortlistingApproachLabel(campaign.shortlisting_approach ?? undefined) },
        { label: 'Target Industries', value: campaign.segmentation?.industry?.join(', ') || '-' },
        { label: 'Employee Range', value: campaign.target?.employee_count?.join(', ') || '-' },
        {
          label: 'Revenue Range',
          value:
            campaign.target?.revenue_min && campaign.target?.revenue_max
              ? `$${campaign.target.revenue_min}M - $${campaign.target.revenue_max}M`
              : '-',
        },
        { label: 'Locations', value: campaign.target?.location?.names?.join(', ') || '-' },
        { label: 'Created', value: formatDate(campaign.metadata?.created_at) },
      ]
    : [];

  return (
    <div className="campaign-details-container">
      <div className="campaign-details-card">
        {/* Back Button */}
        <button
          className="back-to-campaigns-btn"
          onClick={() => navigate('/campaign')}
        >
          ← Back to Campaigns
        </button>

        {/* Error State */}
        {error && (
          <div className="error-banner">
            <span>Failed to load campaign details</span>
            <button className="retry-btn" onClick={() => refetch()}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading campaign details..." />
        ) : campaign ? (
          <>
            {/* Campaign Info Section */}
            <div className="campaign-info-section">
              <div className="campaign-details-header">
                <div>
                  <h1 className="campaign-details-title">
                    {campaign.name || 'N/A'}
                  </h1>
                  <p className="campaign-id">ID: {campaignId}</p>
                </div>
                <div className="campaign-status-area">
                  {/* Polling indicator */}
                  {isBackgroundFetching && (
                    <div className="polling-indicator" title="Auto-refreshing...">
                      <Loader size="small" />
                    </div>
                  )}
                  {isPolling && !isBackgroundFetching && (
                    <span className="polling-badge" title="Auto-refresh active">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 4 }}>
                        <polyline points="23 4 23 10 17 10"/>
                        <polyline points="1 20 1 14 7 14"/>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                      </svg>
                      Live
                    </span>
                  )}
                  <span
                    className="campaign-status-badge"
                    style={{
                      backgroundColor: statusColors[campaign.lifecycle?.status]?.bg || statusColors.draft.bg,
                      color: statusColors[campaign.lifecycle?.status]?.text || statusColors.draft.text,
                    }}
                  >
                    {campaign.lifecycle?.status || 'unknown'}
                  </span>
                </div>
              </div>

              <InfoGrid className="campaign-info-grid" items={infoItems} />

              {/* Progress Stats */}
              <div className="campaign-progress-section">
                <h3>Company Progress</h3>
                <div className="progress-stats">
                  <div className="stat-card total">
                    <span className="stat-number">{pagination?.total_records || stats.total}</span>
                    <span className="stat-label">Total Companies</span>
                  </div>
                  <div className="stat-card enriched">
                    <span className="stat-number">{stats.shortlisted}</span>
                    <span className="stat-label">Shortlisted</span>
                  </div>
                  <div className="stat-card pending">
                    <span className="stat-number">{stats.notShortlisted}</span>
                    <span className="stat-label">Not Shortlisted</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Companies Section */}
            <div className="campaign-companies-section">
              <div className="section-header">
                <h2>Companies {pagination?.total_records ? `(${pagination.total_records})` : `(${companies.length})`}</h2>
                
                {/* Status Filter */}
                <div className="status-filter">
                  <label>Filter by status:</label>
                  <select 
                    value={statusFilter} 
                    onChange={(e) => handleStatusFilterChange(e.target.value as CompanyStatusFilter)}
                    className="status-filter-select"
                    title="Filters the list only (does not update status)"
                  >
                    <option value="all">All</option>
                    <option value="true">Shortlisted</option>
                    <option value="false">Not Shortlisted</option>
                  </select>
                </div>
              </div>

              <div className="campaign-companies-table-wrapper">
                <table className="campaign-companies-table">
                  <thead>
                    <tr>
                      <th>Company ID</th>
                      <th>Status</th>
                      <th>LinkedIn Status</th>
                      <th>Relevant</th>
                      <th>Confidence</th>
                      <th>Relevance Reason</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedCompanies.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="empty-state">
                          <div className="empty-state-content">
                            <span className="empty-icon" aria-hidden="true">
                              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.4 }}>
                                <path d="M3 21h18"/>
                                <path d="M5 21V7l8-4v18"/>
                                <path d="M19 21V11l-6-4"/>
                                <path d="M9 9h.01"/>
                                <path d="M9 12h.01"/>
                                <path d="M9 15h.01"/>
                              </svg>
                            </span>
                            <p>No companies found</p>
                            {statusFilter !== 'all' && (
                              <button 
                                className="clear-filter-btn"
                                onClick={() => handleStatusFilterChange('all')}
                              >
                                Clear filter
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ) : (
                      displayedCompanies.map((company: CampaignCompany) => (
                        <tr 
                          key={company._id}
                          className="clickable-row"
                          onClick={() =>
                            navigate(`/master-data/companies/${company.company_id}`, {
                              state: {
                                from: 'campaign',
                                campaignId,
                                shortlistingApproach: campaign?.shortlisting_approach,
                              },
                            })
                          }
                        >
                          <td className="company-id-cell" title={company.company_id}>
                            {company.company_id.slice(0, 12)}...
                          </td>
                          <td>
                            {isManualCompanyShortlisting ? (
                              <select
                                className="status-filter-select"
                                value={String(getEffectiveCompanyStatus(company))}
                                onClick={(e) => e.stopPropagation()}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  const next = e.target.value === 'true';
                                  setManualCompanyStatus(prev => ({ ...prev, [company._id]: next }));
                                }}
                                title="Mock update (API will be added later)"
                              >
                                <option value="true">Shortlisted</option>
                                <option value="false">Not Shortlisted</option>
                              </select>
                            ) : (
                              <span
                                className="status-badge"
                                style={{
                                  backgroundColor: statusColors[String(company.company_status)]?.bg,
                                  color: statusColors[String(company.company_status)]?.text,
                                }}
                              >
                                {company.company_status ? 'Shortlisted' : 'Not Shortlisted'}
                              </span>
                            )}
                          </td>
                          <td>
                            <span
                              className="status-badge"
                              style={{
                                backgroundColor: statusColors[String(company.linkedin_contact_status)]?.bg,
                                color: statusColors[String(company.linkedin_contact_status)]?.text,
                              }}
                            >
                              {company.linkedin_contact_status ? 'Done' : 'Pending'}
                            </span>
                          </td>
                          <td>
                            <span className={`relevance-badge ${company.is_relevant ? 'relevant' : 'not-relevant'}`}>
                              {company.is_relevant ? '✓ Yes' : '✗ No'}
                            </span>
                          </td>
                          <td>
                            {company.metadata?.confidence_level && (
                              <span
                                className="confidence-badge"
                                style={{
                                  backgroundColor: statusColors[company.metadata.confidence_level]?.bg,
                                  color: statusColors[company.metadata.confidence_level]?.text,
                                }}
                              >
                                {company.metadata.confidence_level}
                              </span>
                            )}
                          </td>
                          <td className="relevance-reason-cell" title={company.metadata?.relevance_reason}>
                            {company.metadata?.relevance_reason 
                              ? company.metadata.relevance_reason.slice(0, 50) + '...'
                              : '-'}
                          </td>
                          <td>
                            <button 
                              className="action-btn" 
                              title="View Company"
                              aria-label="View company details"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/master-data/companies/${company.company_id}`, {
                                  state: {
                                    from: 'campaign',
                                    campaignId,
                                    shortlistingApproach: campaign?.shortlisting_approach,
                                  },
                                });
                              }}
                            >
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                              </svg>
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination && companies.length > 0 && (
                <Pagination
                  currentPage={pagination.page_number}
                  totalRecords={pagination.total_records}
                  pageSize={limit}
                  hasNext={pagination.has_next}
                  onPrevious={handlePrevPage}
                  onNext={handleNextPage}
                />
              )}
            </div>
          </>
        ) : (
          <div className="empty-state-content" style={{ padding: '3rem', textAlign: 'center' }}>
            <span className="empty-icon" aria-hidden="true">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.4 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </span>
            <p>Campaign not found</p>
          </div>
        )}
      </div>
    </div>
  );
};
