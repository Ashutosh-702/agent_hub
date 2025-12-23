import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCampaignsQuery } from '../store';
import { Loader } from './shared';

const statusColors: Record<string, { bg: string; text: string }> = {
  active: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  completed: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1' },
  draft: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  paused: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
};

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

  return (
    <div className="campaign-list-container">
      <div className="campaign-list-card">
        {/* Header */}
        <div className="campaign-list-header">
          <div>
            <h1 className="campaign-list-title">Campaigns</h1>
            <p className="campaign-list-subtitle">Manage your outreach campaigns</p>
          </div>
          <button
            className="create-campaign-btn"
            onClick={() => navigate('/master-data/campaign/new')}
          >
            <span className="btn-icon">+</span>
            Create New Campaign
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="error-banner">
            ❌ Failed to load campaigns
            <button className="retry-btn" onClick={() => refetch()}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading campaigns..." />
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
                          <span className="empty-icon">📋</span>
                          <p>No campaigns yet</p>
                          <button
                            className="create-campaign-btn-small"
                            onClick={() => navigate('/master-data/campaign/new')}
                          >
                            Create your first campaign
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    campaigns.map((campaign) => (
                      <tr key={campaign._id}>
                        <td className="campaign-name" title={campaign._id}>
                          {campaign._id.slice(0, 8)}...
                        </td>
                        <td>
                          <span className="product-badge">
                            {campaign.ownership?.product_name || 'N/A'}
                          </span>
                        </td>
                        <td>
                          <span
                            className="status-badge"
                            style={{
                              backgroundColor: statusColors[campaign.lifecycle?.status]?.bg || statusColors.draft.bg,
                              color: statusColors[campaign.lifecycle?.status]?.text || statusColors.draft.text,
                            }}
                          >
                            {campaign.lifecycle?.status || 'unknown'}
                          </span>
                        </td>
                        <td>{campaign.company_mappings_count || 0}</td>
                        <td>{formatDate(campaign.metadata?.created_at)}</td>
                        <td>
                          <button className="action-btn" title="View">
                            👁️
                          </button>
                          <button className="action-btn" title="Edit">
                            ✏️
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && campaigns.length > 0 && (
              <div className="pagination-container">
                <div className="pagination-info">
                  Showing page {pagination.page_number} 
                  {pagination.total_records > 0 && ` of ${Math.ceil(pagination.total_records / limit)}`}
                  {pagination.total_records > 0 && ` (${pagination.total_records} total)`}
                </div>
                <div className="pagination-controls">
                  <button
                    className="pagination-btn"
                    onClick={handlePrevPage}
                    disabled={page === 1}
                  >
                    ← Previous
                  </button>
                  <span className="pagination-current">Page {page}</span>
                  <button
                    className="pagination-btn"
                    onClick={handleNextPage}
                    disabled={!pagination.has_next}
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
