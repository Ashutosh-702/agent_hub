import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, NotificationBanner, Spinner, Typography } from 'novus';
import { useGetCampaignsQuery } from '../store';

type UiCampaign = {
  id: string;
  name: string;
  statusLabel: string;
  contacts: number;
  qualified: number;
  approved: number;
  enrolled: number;
  progressPct: number; // 0..100
};

const mockCampaigns: UiCampaign[] = [
  {
    id: 'mock-1',
    name: 'Q1 Enterprise Outreach',
    statusLabel: 'In Progress',
    contacts: 200,
    qualified: 63,
    approved: 12,
    enrolled: 0,
    progressPct: 30,
  },
  {
    id: 'mock-2',
    name: 'Mid-Market SaaS Push',
    statusLabel: 'Completed',
    contacts: 150,
    qualified: 45,
    approved: 45,
    enrolled: 42,
    progressPct: 55,
  },
];

export const CampaignList = () => {
  const navigate = useNavigate();
  const [page] = useState(1);
  const limit = 12;
  const { data, isLoading, error, refetch } = useGetCampaignsQuery({ page, limit });

  const apiCampaigns = data?.data || [];

  const campaigns: UiCampaign[] = useMemo(() => {
    if (apiCampaigns.length === 0) return mockCampaigns;
    return apiCampaigns.map((c: any) => {
      const statusRaw = String(c?.lifecycle?.status || '').toLowerCase();
      const statusLabel =
        statusRaw === 'started' || statusRaw === 'active' ? 'In Progress' : statusRaw ? statusRaw : 'In Progress';

      const companies = Number(c?.company_mappings_count || 0);
      const contacts = companies > 0 ? companies * 10 : 200; // mock-ish until we have real counts
      const qualified = Math.round(contacts * 0.3);
      const approved = Math.round(contacts * 0.06);
      const enrolled = statusRaw === 'completed' ? Math.round(contacts * 0.28) : 0;

      const progressPct = Math.max(
        8,
        Math.min(100, statusRaw === 'completed' ? 60 : statusRaw === 'started' ? 35 : 25)
      );

      return {
        id: c._id,
        name: c?.ownership?.product_name ? `${c.ownership.product_name} Outreach` : `Campaign ${String(c._id).slice(0, 6)}`,
        statusLabel: statusLabel === 'completed' ? 'Completed' : 'In Progress',
        contacts,
        qualified,
        approved,
        enrolled,
        progressPct,
      };
    });
  }, [apiCampaigns]);

  const goToCampaign = (id: string) => {
    // If the campaign is mock, we can still open the wizard review screen for UI.
    if (id.startsWith('mock-')) {
      navigate('/prospecting/wide/review-prospects');
      return;
    }
    navigate(`/master-data/campaign/${id}`);
  };

  return (
    <div className="figma-campaigns-page">
      <div className="figma-titlebar">
        <div className="figma-titlebar-inner">
          <Typography variant="heading-xl" type="h1" className="figma-page-title">
            Campaigns
          </Typography>
          <Button
            type="primary"
            appearance="default"
            size="m"
            className="figma-primary-cta"
            onClick={() => navigate('/prospecting/wide/define-filters')}
          >
            New Campaign
          </Button>
        </div>
      </div>

      <div className="figma-page-body">
        {error && (
          <div className="figma-page-banner">
            <NotificationBanner
              appearance="negative"
              type="inline"
              title="Failed to load campaigns"
              description="Showing mock campaigns for UI. You can retry to fetch real data."
              primaryButtonText="Retry"
              onPrimaryClick={() => refetch()}
              showIcon
            />
          </div>
        )}

        {isLoading ? (
          <div className="figma-loading">
            <Spinner size="l" label="Loading campaigns..." labelPlacement="bottom" />
          </div>
        ) : (
          <div className="figma-campaign-grid">
            {campaigns.map(c => {
              const primaryLabel = c.statusLabel === 'Completed' ? 'View Campaign' : 'Resume';
              const isPrimary = c.statusLabel !== 'Completed';
              return (
                <div key={c.id} className="figma-campaign-card">
                  <div className="figma-campaign-card-header">
                    <div>
                      <div className="figma-campaign-name">{c.name}</div>
                      <span className="figma-status-pill">{c.statusLabel}</span>
                    </div>
                  </div>

                  <div className="figma-campaign-stats">
                    <div className="figma-stat-row">
                      <span className="figma-stat-label">Contacts</span>
                      <span className="figma-stat-value">{c.contacts}</span>
                    </div>
                    <div className="figma-stat-row">
                      <span className="figma-stat-label">Qualified</span>
                      <span className="figma-stat-value">{c.qualified}</span>
                    </div>
                    <div className="figma-stat-row">
                      <span className="figma-stat-label">Approved</span>
                      <span className="figma-stat-value">{c.approved}</span>
                    </div>
                    <div className="figma-stat-row">
                      <span className="figma-stat-label">Enrolled</span>
                      <span className="figma-stat-value">{c.enrolled}</span>
                    </div>
                  </div>

                  <div className="figma-progressbar">
                    <div className="figma-progressbar-fill" style={{ width: `${c.progressPct}%` }} />
                  </div>

                  <Button
                    type={isPrimary ? 'primary' : 'secondary'}
                    appearance="default"
                    size="m"
                    className={`figma-card-cta ${isPrimary ? 'primary' : 'secondary'}`}
                    onClick={() => goToCampaign(c.id)}
                  >
                    {primaryLabel}
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
