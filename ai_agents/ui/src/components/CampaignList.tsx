import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCampaignsQuery } from '../store';
import { DataTable, EmptyState, ErrorBanner, Loader, PageHeader, Pagination } from './shared';
import type { DataTableColumn } from './shared';
import type { Campaign } from '../store';

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

  const columns: Array<DataTableColumn<Campaign>> = [
    {
      id: 'campaignId',
      header: 'Campaign ID',
      cell: (campaign) => (
        <span className="campaign-name" title={campaign._id}>
          {campaign._id.slice(0, 8)}...
        </span>
      ),
    },
    {
      id: 'product',
      header: 'Product',
      cell: (campaign) => (
        <span className="product-badge">{campaign.ownership?.product_name || 'N/A'}</span>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      cell: (campaign) => (
        <span
          className="status-badge"
          style={{
            backgroundColor: statusColors[campaign.lifecycle?.status]?.bg || statusColors.draft.bg,
            color: statusColors[campaign.lifecycle?.status]?.text || statusColors.draft.text,
          }}
        >
          {campaign.lifecycle?.status || 'unknown'}
        </span>
      ),
    },
    {
      id: 'companies',
      header: 'Companies',
      cell: (campaign) => campaign.company_mappings_count || 0,
    },
    {
      id: 'created',
      header: 'Created',
      cell: (campaign) => formatDate(campaign.metadata?.created_at),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (campaign) => (
        <button
          className="action-btn"
          title="View Details"
          aria-label="View campaign details"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/campaign/${campaign._id}`);
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      ),
    },
  ];

  return (
    <div className="campaign-list-container">
      <div className="campaign-list-card">
        {/* Header */}
        <div className="campaign-list-header">
          <PageHeader
            variant="inline"
            title="Campaigns"
            subtitle="View all your outreach campaigns"
            titleClassName="campaign-list-title"
            subtitleClassName="campaign-list-subtitle"
          />
        </div>

        {/* Error State */}
        {error && <ErrorBanner message="Failed to load campaigns" onRetry={() => refetch()} />}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading campaigns..." />
        ) : (
          <>
            {/* Campaigns Table */}
            <div className="campaigns-table-wrapper">
              <DataTable<Campaign>
                rows={campaigns}
                columns={columns}
                getRowKey={(c) => c._id}
                onRowClick={(c) => navigate(`/campaign/${c._id}`)}
                rowClassName={() => 'clickable-row'}
                tableClassName="campaigns-table"
                emptyState={
                  <div className="empty-state">
                    <div className="empty-state-content">
                      <EmptyState
                        title="No campaigns yet"
                        description="Go to Prospecting → Wide Prospecting to create a campaign"
                      />
                    </div>
                  </div>
                }
              />
            </div>

            {/* Pagination */}
            {pagination && campaigns.length > 0 && (
              <Pagination
                currentPage={pagination.page_number}
                totalRecords={pagination.total_records}
                pageSize={limit}
                hasNext={pagination.has_next}
                onPrevious={handlePrevPage}
                onNext={handleNextPage}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};
