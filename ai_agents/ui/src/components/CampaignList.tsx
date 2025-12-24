import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCampaignsQuery } from '../store';
import { Badge, Button, EmptyState, NotificationBanner, Pagination, Spinner, Typography } from 'novus';
import viteLogo from '/vite.svg';

export const CampaignList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const limit = 10;

  // RTK Query hook - handles loading, error, caching automatically
  const { data, isLoading, error, refetch } = useGetCampaignsQuery({ page, limit });

  const campaigns = data?.data || [];
  const pagination = data?.pagination;

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (pagination?.has_next) setPage(page + 1);
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
      case 'draft':
      default:
        return 'default';
    }
  };

  return (
    <div className="campaign-list-container">
      <div className="campaign-list-card">
        {/* Header */}
        <div className="campaign-list-header">
          <div>
            <Typography variant="heading-xl" type="h1" className="campaign-list-title">
              Campaigns
            </Typography>
            <Typography variant="body-m" type="p" className="campaign-list-subtitle">
              View all your outreach campaigns
            </Typography>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <NotificationBanner
            appearance="negative"
            type="inline"
            title="Failed to load campaigns"
            description="Please try again."
            primaryButtonText="Retry"
            onPrimaryClick={() => refetch()}
            showIcon
          />
        )}

        {/* Loading State */}
        {isLoading ? (
          <div style={{ padding: '2rem 0' }}>
            <Spinner size="l" label="Loading campaigns..." labelPlacement="bottom" />
          </div>
        ) : (
          <>
            {/* Campaigns Table */}
            <div className="campaigns-table-wrapper">
              <table className="campaigns-table">
                <thead>
                  <tr>
                    <th>Campaign ID</th>
                    <th>Product</th>
                    <th>Status</th>
                    <th>Companies</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        <div className="empty-state-content">
                          <EmptyState
                            type="single"
                            imageURL={viteLogo}
                            title="No campaigns yet"
                            description="Go to Prospecting → Wide Prospecting to create a campaign"
                          />
                        </div>
                      </td>
                    </tr>
                  ) : (
                    campaigns.map((campaign) => (
                      <tr
                        key={campaign._id}
                        className="clickable-row"
                        onClick={() => navigate(`/master-data/campaign/${campaign._id}`)}
                      >
                        <td className="campaign-name" title={campaign._id}>
                          {campaign._id.slice(0, 8)}...
                        </td>
                        <td>
                          <span className="product-badge">
                            {campaign.ownership?.product_name || 'N/A'}
                          </span>
                        </td>
                        <td>
                          <Badge
                            state={statusToBadgeState(campaign.lifecycle?.status)}
                            emphasis="subtle"
                            className="status-badge-component"
                          >
                            {campaign.lifecycle?.status || 'unknown'}
                          </Badge>
                        </td>
                        <td>{campaign.company_mappings_count || 0}</td>
                        <td>{formatDate(campaign.metadata?.created_at)}</td>
                        <td>
                          <Button
                            size="s"
                            type="tertiary"
                            appearance="default"
                            onClick={(e: any) => {
                              e.stopPropagation();
                              navigate(`/master-data/campaign/${campaign._id}`);
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
            {pagination && campaigns.length > 0 && (
              <Pagination
                total={pagination.total_records}
                defaultPageSize={[limit]}
                value={{ currentActivePage: page, currentPageSize: limit }}
                onPreviousClick={handlePrevPage}
                onNextClick={handleNextPage}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};
