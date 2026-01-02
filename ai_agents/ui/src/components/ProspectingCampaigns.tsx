import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetProspectingCampaignsQuery } from '../store';
import { DataTable, EmptyState, ErrorBanner, Loader, PageHeader, Pagination } from './shared';
import type { DataTableColumn } from './shared';

type WizardStepId = 1 | 2 | 3 | 4 | 5 | 6;

// Step derivation depends ONLY on prospecting_cycle.status (lifecycle.status is ignored for wizard).
const deriveWizardStepFromStatuses = (
  _lifecycle: string,
  cycle: string
): { stepId: WizardStepId; label: string } => {
  // Step 6: Enrollment complete or in progress
  if (cycle === 'enrolled_to_sequence') return { stepId: 6, label: 'Enrolled to Sequence ✓' };
  
  // Step 6: Ready for enrollment
  if (cycle === 'personalization_completed') return { stepId: 6, label: 'Enroll for Outreach' };
  
  // Step 5: Personalization
  if (cycle === 'hubspot_sync_completed') return { stepId: 5, label: 'Personalization' };
  
  // Step 4: HubSpot Sync in progress or ready
  if (cycle === 'hubspot_sync_in_progress') return { stepId: 4, label: 'Syncing to HubSpot...' };
  if (cycle === 'hubspot_sync_failed') return { stepId: 4, label: 'HubSpot Sync Failed' };
  if (cycle === 'contact_enriched') return { stepId: 4, label: 'Sync to HubSpot' };
  
  // Step 3: Contact Qualification
  if (cycle === 'contact_qualification') return { stepId: 3, label: 'Contact Qualification' };
  
  // Step 2: Company Qualification
  if (cycle === 'company_qualification') return { stepId: 2, label: 'Company Qualification' };
  
  // Step 1: Prospecting
  if (cycle === 'prospecting') return { stepId: 1, label: 'Prospecting' };

  // Fallback for unknown/new statuses - show what the status is
  if (cycle) return { stepId: 1, label: `Unknown: ${cycle}` };
  return { stepId: 1, label: 'Prospecting' };
};

export const ProspectingCampaigns = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const limit = 10;

  // Use the new dedicated API that only returns campaigns with prospecting_cycle.status
  const { data, isLoading, error, refetch } = useGetProspectingCampaignsQuery({ page, limit });

  const campaigns = data?.data || [];
  const pagination = data?.pagination;

  const rows = useMemo(() => {
    return campaigns.map((c) => {
      const lifecycle = c.lifecycle?.status || '';
      const cycle = c.prospecting_cycle?.status || '';
      const derived = deriveWizardStepFromStatuses(lifecycle, cycle);
      return {
        campaign: c,
        lifecycle,
        cycle,
        stepId: derived.stepId,
        stepLabel: derived.label,
      };
    });
  }, [campaigns]);

  const columns: Array<DataTableColumn<(typeof rows)[number]>> = [
    {
      id: 'campaignId',
      header: 'Campaign ID',
      cell: (row) => (
        <span className="campaign-name-cell" title={row.campaign._id}>
          {row.campaign._id}
        </span>
      ),
    },
    {
      id: 'industry',
      header: 'Industry',
      cell: (row) => (
        <span className="product-badge">
          {(row.campaign.segmentation?.industry || []).join(', ') || 'N/A'}
        </span>
      ),
    },
    {
      id: 'pendingStep',
      header: 'Current / Pending Step',
      cell: (row) => (
        <span className="metric-value" title={`Step ${row.stepId}`}>
          Step {row.stepId}: {row.stepLabel}
        </span>
      ),
    },
    {
      id: 'cycle',
      header: 'Prospecting Cycle',
      cell: (row) => <span className="metric-value">{row.cycle || 'N/A'}</span>,
    },
    {
      id: 'status',
      header: 'Lifecycle',
      cell: (row) => <span className="metric-value">{row.lifecycle || 'N/A'}</span>,
    },
  ];

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (pagination?.has_next) setPage(page + 1);
  };

  const openWizard = (campaignId: string) => {
    navigate(`/campaign/new?campaign_id=${encodeURIComponent(campaignId)}`);
  };

  return (
    <div className="campaign-list-container">
      <div className="campaign-list-card">
        <div className="campaign-list-header">
          <PageHeader
            variant="inline"
            title="Campaign Prospecting"
            subtitle="Resume pending prospecting workflows from existing campaigns"
            titleClassName="campaign-list-title"
            subtitleClassName="campaign-list-subtitle"
          />
        </div>

        {error && <ErrorBanner message="Failed to load campaigns" onRetry={() => refetch()} />}

        {isLoading ? (
          <Loader size="large" text="Loading campaigns..." />
        ) : (
          <>
            <div className="campaigns-table-wrapper">
              <DataTable<(typeof rows)[number]>
                rows={rows}
                columns={columns}
                getRowKey={(r) => r.campaign._id}
                onRowClick={(r) => openWizard(r.campaign._id)}
                rowClassName={() => 'clickable-row'}
                tableClassName="campaigns-table"
                emptyState={
                  <div className="empty-state">
                    <div className="empty-state-content">
                      <EmptyState
                        title="No campaigns found"
                        description="Create a campaign first, then you can resume it here."
                      />
                    </div>
                  </div>
                }
              />
            </div>

            {pagination && rows.length > 0 && (
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

