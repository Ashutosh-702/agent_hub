import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCampaignsQuery } from '../store';
import { DataTable, EmptyState, ErrorBanner, Loader, PageHeader, Pagination } from './shared';
import type { DataTableColumn } from './shared';
import type { Campaign } from '../store';
import { ExportContactsModal } from './campaign/ExportContactsModal';

type WizardStepId = 1 | 2 | 3 | 4 | 5 | 6;

// Prospecting cycle status options for filtering
const PROSPECTING_CYCLE_STAGES = [
  { value: '', label: 'All Campaigns' },
  { value: 'prospecting', label: 'Step 1: Prospecting' },
  { value: 'company_qualification', label: 'Step 2: Company Qualification' },
  { value: 'contact_qualification', label: 'Step 3: Contact Qualification' },
  { value: 'contact_enrichment_in_progress', label: 'Step 3: Enriching Contacts...' },
  { value: 'contact_enriched', label: 'Step 4: Sync to HubSpot' },
  { value: 'hubspot_sync_in_progress', label: 'Step 4: Syncing to HubSpot...' },
  { value: 'hubspot_sync_completed', label: 'Step 5: Personalization' },
  { value: 'hubspot_sync_failed', label: 'Step 4: HubSpot Sync Failed' },
  { value: 'personalization_completed', label: 'Step 6: Enroll for Outreach' },
  { value: 'enrolled_to_sequence', label: 'Step 6: Enrolled ✓' },
];

// Step derivation based on prospecting_cycle.status
const deriveWizardStep = (cycle: string): { stepId: WizardStepId; label: string } => {
  if (cycle === 'enrolled_to_sequence') return { stepId: 6, label: 'Enrolled to Sequence ✓' };
  if (cycle === 'personalization_completed') return { stepId: 6, label: 'Enroll for Outreach' };
  if (cycle === 'hubspot_sync_completed') return { stepId: 5, label: 'Personalization' };
  if (cycle === 'hubspot_sync_in_progress') return { stepId: 4, label: 'Syncing to HubSpot...' };
  if (cycle === 'hubspot_sync_failed') return { stepId: 4, label: 'HubSpot Sync Failed' };
  if (cycle === 'contact_enriched') return { stepId: 4, label: 'Sync to HubSpot' };
  if (cycle === 'contact_enrichment_in_progress') return { stepId: 3, label: 'Enriching Contacts...' };
  if (cycle === 'contact_qualification') return { stepId: 3, label: 'Contact Qualification' };
  if (cycle === 'company_qualification') return { stepId: 2, label: 'Company Qualification' };
  if (cycle === 'prospecting') return { stepId: 1, label: 'Prospecting' };
  if (cycle) return { stepId: 1, label: `Unknown: ${cycle}` };
  return { stepId: 1, label: 'Not Started' };
};

const statusColors: Record<string, { bg: string; text: string }> = {
  active: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  completed: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1' },
  draft: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  paused: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  pending: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  company_qualification: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  contact_qualification: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7' },
  contact_enrichment_in_progress: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7' },
  contact_enriched: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
};

const stepColors: Record<number, { bg: string; text: string }> = {
  1: { bg: 'rgba(156, 163, 175, 0.15)', text: '#6b7280' },
  2: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  3: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7' },
  4: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  5: { bg: 'rgba(236, 72, 153, 0.15)', text: '#ec4899' },
  6: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
};

interface CampaignRow {
  campaign: Campaign;
  stepId: WizardStepId;
  stepLabel: string;
}

export const CampaignList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [prospectingCycleFilter, setProspectingCycleFilter] = useState('');
  const [searchName, setSearchName] = useState('');
  const [searchInput, setSearchInput] = useState(''); // Local input state for debouncing
  const limit = 10;
  
  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportCampaignId, setExportCampaignId] = useState('');
  const [exportCampaignName, setExportCampaignName] = useState('');

  // Debounce search input
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== searchName) {
        setSearchName(searchInput);
        setPage(1); // Reset to first page on search
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [searchInput, searchName]);

  // RTK Query hook - handles loading, error, caching automatically
  const { data, isLoading, error, refetch } = useGetCampaignsQuery({ 
    page, 
    limit,
    prospecting_cycle_status: prospectingCycleFilter || undefined,
    search_name: searchName || undefined,
  });

  const campaigns = data?.data || [];
  const pagination = data?.pagination;

  // Transform campaigns to include wizard step info
  const rows: CampaignRow[] = useMemo(() => {
    return campaigns.map((c) => {
      const cycle = c.prospecting_cycle?.status || '';
      const derived = deriveWizardStep(cycle);
      return {
        campaign: c,
        stepId: derived.stepId,
        stepLabel: derived.label,
      };
    });
  }, [campaigns]);

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

  const handleFilterChange = (value: string) => {
    setProspectingCycleFilter(value);
    setPage(1); // Reset to first page when filter changes
  };

  const openWizard = (campaignId: string) => {
    navigate(`/campaign/new?campaign_id=${encodeURIComponent(campaignId)}`);
  };

  const openDetails = (campaignId: string) => {
    navigate(`/campaign/${campaignId}`);
  };

  const openExportModal = (campaignId: string, campaignName: string) => {
    setExportCampaignId(campaignId);
    setExportCampaignName(campaignName);
    setShowExportModal(true);
  };

  // Truncate ID to first 4 characters with full ID on hover
  const truncateId = (id: string) => {
    if (!id) return 'N/A';
    return id.length > 4 ? `${id.substring(0, 4)}...` : id;
  };

  const columns: Array<DataTableColumn<CampaignRow>> = [
    {
      id: 'campaignId',
      header: 'Campaign ID',
      cell: (row) => (
        <span className="campaign-id-cell" title={row.campaign._id}>
          {truncateId(row.campaign._id)}
        </span>
      ),
    },
    {
      id: 'campaignName',
      header: 'Campaign Name',
      cell: (row) => (
        <span className="campaign-name-cell" title={row.campaign.name || 'N/A'}>
          {row.campaign.name || 'N/A'}
        </span>
      ),
    },
    {
      id: 'industry',
      header: 'Industry',
      cell: (row) => {
        const industries = (row.campaign.segmentation?.industry || []).join(', ') || 'N/A';
        return (
          <span className="industry-cell" title={industries}>
            {industries}
          </span>
        );
      },
    },
    {
      id: 'status',
      header: 'Status',
      cell: (row) => (
        <span
          className="status-badge"
          style={{
            backgroundColor: statusColors[row.campaign.lifecycle?.status]?.bg || statusColors.draft.bg,
            color: statusColors[row.campaign.lifecycle?.status]?.text || statusColors.draft.text,
          }}
        >
          {row.campaign.lifecycle?.status || 'unknown'}
        </span>
      ),
    },
    {
      id: 'currentStep',
      header: 'Current Step',
      cell: (row) => (
        <span
          className="status-badge"
          style={{
            backgroundColor: stepColors[row.stepId]?.bg || stepColors[1].bg,
            color: stepColors[row.stepId]?.text || stepColors[1].text,
          }}
          title={`Step ${row.stepId}`}
        >
          Step {row.stepId}: {row.stepLabel}
        </span>
      ),
    },
    {
      id: 'prospectingCycleStatus',
      header: 'Prospecting Cycle',
      cell: (row) => (
        <span className="metric-value">{row.campaign.prospecting_cycle?.status || 'N/A'}</span>
      ),
    },
    {
      id: 'relevantCompanyMappingsCount',
      header: 'Relevant Companies',
      cell: (row) => (
        <span className="metric-value metric-qualified">{row.campaign.relevant_company_mappings_count ?? 0}</span>
      ),
    },
    {
      id: 'totalCompanyMappingsCount',
      header: 'Total Companies',
      cell: (row) => (
        <span className="metric-value">{row.campaign.total_company_mappings_count ?? 0}</span>
      ),
    },
    {
      id: 'contactRunsCount',
      header: 'Contacts',
      cell: (row) => (
        <span className="metric-value">{row.campaign.contact_runs_count ?? 0}</span>
      ),
    },
    {
      id: 'created',
      header: 'Created',
      cell: (row) => formatDate(row.campaign.metadata?.created_at),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (row) => (
        <div className="action-buttons-cell">
          <button
            className="action-btn"
            title="View Details"
            aria-label="View campaign details"
            onClick={(e) => {
              e.stopPropagation();
              openDetails(row.campaign._id);
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          <button
            className="action-btn"
            title="Export Contacts CSV"
            aria-label="Export contacts to CSV"
            onClick={(e) => {
              e.stopPropagation();
              openExportModal(row.campaign._id, row.campaign.name || 'Unnamed Campaign');
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
          <button
            className="action-btn action-btn-primary"
            title="Resume Wizard"
            aria-label="Resume campaign wizard"
            onClick={(e) => {
              e.stopPropagation();
              openWizard(row.campaign._id);
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="campaign-list-container">
      {/* Export Modal */}
      <ExportContactsModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        campaignId={exportCampaignId}
        campaignName={exportCampaignName}
      />

      <div className="campaign-list-card">
        {/* Header */}
        <div className="campaign-list-header">
          <PageHeader
            variant="inline"
            title="Prospecting + Outreach Campaigns"
            subtitle="View all your prospecting + outreach campaigns"
            titleClassName="campaign-list-title"
            subtitleClassName="campaign-list-subtitle"
          />
          <button
            className="new-campaign-btn"
            onClick={() => navigate('/campaign/new')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            New Campaign
          </button>
        </div>

        {/* Filter Section */}
        <div className="campaign-filters">
          {/* Search by Name */}
          <div className="filter-group search-group">
            <label htmlFor="search-name" className="filter-label">
              Search by Name:
            </label>
            <div className="search-input-wrapper">
              <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                id="search-name"
                type="text"
                className="search-input"
                placeholder="Search campaigns..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
              {searchInput && (
                <button 
                  className="search-clear-btn"
                  onClick={() => {
                    setSearchInput('');
                    setSearchName('');
                  }}
                  title="Clear search"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Filter by Stage */}
          <div className="filter-group">
            <label htmlFor="prospecting-cycle-filter" className="filter-label">
              Filter by Prospecting Stage:
            </label>
            <select
              id="prospecting-cycle-filter"
              className="filter-select"
              value={prospectingCycleFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
            >
              {PROSPECTING_CYCLE_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
            </select>
          </div>
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
              <DataTable<CampaignRow>
                rows={rows}
                columns={columns}
                getRowKey={(r) => r.campaign._id}
                onRowClick={(r) => openDetails(r.campaign._id)}
                rowClassName={() => 'clickable-row'}
                tableClassName="campaigns-table"
                emptyState={
                  <div className="empty-state">
                    <div className="empty-state-content">
                      <EmptyState
                        title={prospectingCycleFilter ? "No campaigns found for this filter" : "No campaigns yet"}
                        description={prospectingCycleFilter 
                          ? "Try selecting a different filter or create a new campaign"
                          : "Click 'New Campaign' to create your first campaign"
                        }
                      />
                    </div>
                  </div>
                }
              />
            </div>

            {/* Pagination */}
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
