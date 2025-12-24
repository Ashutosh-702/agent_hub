import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetCampaignDetailsQuery } from '../store';
import type { CampaignCompany } from '../store';
import { Badge, Button, NotificationBanner, SelectorDropdown, Spinner, Typography } from 'novus';

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

  const statusToBadgeState = (status?: string) => {
    switch (status) {
      case 'active':
      case 'started':
        return 'success';
      case 'paused':
        return 'warning';
      case 'completed':
        return 'neutral';
      default:
        return 'default';
    }
  };

  const statusFilterOptions = [
    { label: 'All', value: 'all' },
    { label: 'Shortlisted', value: 'true' },
    { label: 'Not Shortlisted', value: 'false' },
  ];

  const selectedStatusFilterOption =
    statusFilterOptions.find(o => o.value === statusFilter) || statusFilterOptions[0];

  return (
    <div className="campaign-details-container">
      <div className="campaign-details-card">
        {/* Back Button */}
        <Button
          type="tertiary"
          appearance="default"
          onClick={() => navigate('/master-data/campaign')}
          className="back-to-campaigns-btn"
        >
          ← Back to Campaigns
        </Button>

        {/* Error State */}
        {error && (
          <NotificationBanner
            appearance="negative"
            type="inline"
            title="Failed to load campaign details"
            description="Please try again."
            primaryButtonText="Retry"
            onPrimaryClick={() => refetch()}
            showIcon
          />
        )}

        {/* Loading State */}
        {isLoading ? (
          <div style={{ padding: '2rem 0' }}>
            <Spinner size="l" label="Loading campaign details..." labelPlacement="bottom" />
          </div>
        ) : campaign ? (
          <>
            {/* Campaign Info Section */}
            <div className="campaign-info-section">
              <div className="campaign-details-header">
                <div>
                  <Typography variant="heading-xl" type="h1" className="campaign-details-title">
                    {campaign.ownership?.product_name || 'Campaign'}
                  </Typography>
                  <p className="campaign-id">ID: {campaignId}</p>
                </div>
                <div className="campaign-status-area">
                  {/* Polling indicator */}
                  {isBackgroundFetching && (
                    <div className="polling-indicator" title="Auto-refreshing...">
                      <Spinner size="s" />
                    </div>
                  )}
                  {isPolling && !isBackgroundFetching && (
                    <span className="polling-badge" title="Auto-refresh active">
                      🔄 Live
                    </span>
                  )}
                  <Badge state={statusToBadgeState(campaign.lifecycle?.status)} emphasis="subtle">
                    {campaign.lifecycle?.status || 'unknown'}
                  </Badge>
                </div>
              </div>

              <div className="campaign-info-grid">
                <div className="info-item">
                  <label>Business Team</label>
                  <span>{campaign.ownership?.business_team || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Owner Email</label>
                  <span>{campaign.ownership?.user_email || '-'}</span>
                </div>
                <div className="info-item">
                  <label>HubSpot Email</label>
                  <span>{campaign.ownership?.hubspot_email || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Shortlisting Approach</label>
                  <span>{shortlistingApproachLabel(campaign.shortlisting_approach)}</span>
                </div>
                <div className="info-item">
                  <label>Target Industries</label>
                  <span>{campaign.segmentation?.industry?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Employee Range</label>
                  <span>{campaign.target?.employee_count?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Revenue Range</label>
                  <span>
                    {campaign.target?.revenue_min && campaign.target?.revenue_max
                      ? `$${campaign.target.revenue_min}M - $${campaign.target.revenue_max}M`
                      : '-'}
                  </span>
                </div>
                <div className="info-item">
                  <label>Locations</label>
                  <span>{campaign.target?.location?.names?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Created</label>
                  <span>{formatDate(campaign.metadata?.created_at)}</span>
                </div>
              </div>

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
                  <SelectorDropdown
                    label="Status"
                    options={statusFilterOptions}
                    value={selectedStatusFilterOption}
                    onChange={(opt: any) => handleStatusFilterChange((opt?.value || 'all') as CompanyStatusFilter)}
                    size="s"
                  />
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
                            <span className="empty-icon">🏢</span>
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
                              <div onClick={(e) => e.stopPropagation()}>
                                <SelectorDropdown
                                  label={getEffectiveCompanyStatus(company) ? 'Shortlisted' : 'Not Shortlisted'}
                                  options={[
                                    { label: 'Shortlisted', value: 'true' },
                                    { label: 'Not Shortlisted', value: 'false' },
                                  ]}
                                  value={{
                                    label: getEffectiveCompanyStatus(company) ? 'Shortlisted' : 'Not Shortlisted',
                                    value: String(getEffectiveCompanyStatus(company)),
                                  }}
                                  onChange={(opt: any) => {
                                    const next = opt?.value === 'true';
                                    setManualCompanyStatus(prev => ({ ...prev, [company._id]: next }));
                                  }}
                                  size="s"
                                />
                              </div>
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
                            <Button
                              type="tertiary"
                              appearance="default"
                              size="s"
                              className="action-btn"
                              onClick={(e: any) => {
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
                              View
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination && companies.length > 0 && (
                <div className="pagination-container">
                  <div className="pagination-info">
                    Showing page {pagination.page_number} 
                    {pagination.total_records > 0 && ` of ${Math.ceil(pagination.total_records / limit)}`}
                    {pagination.total_records > 0 && ` (${pagination.total_records} total)`}
                  </div>
                  <div className="pagination-controls">
                    <Button type="secondary" appearance="default" size="s" className="pagination-btn" onClick={handlePrevPage} disabled={page === 1}>
                      ← Previous
                    </Button>
                    <span className="pagination-current">Page {page}</span>
                    <Button type="secondary" appearance="default" size="s" className="pagination-btn" onClick={handleNextPage} disabled={!pagination.has_next}>
                      Next →
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="empty-state-content" style={{ padding: '3rem', textAlign: 'center' }}>
            <span className="empty-icon">📋</span>
            <p>Campaign not found</p>
          </div>
        )}
      </div>
    </div>
  );
};
