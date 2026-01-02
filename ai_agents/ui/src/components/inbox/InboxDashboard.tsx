import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MetricsCard } from './MetricsCard';
import { ConversionFunnel } from './ConversionFunnel';
import { ChannelPerformance } from './ChannelPerformance';
import { InboxyRecommender } from './InboxyRecommender';
import { Loader } from '../shared/Loader';
import type { DashboardMetrics } from '../../services/inboxMetricsApi';
import { getMetrics } from '../../services/inboxMetricsApi';
import './InboxDashboard.css';

type PeriodType = '7d' | '30d' | '90d' | 'custom';

export const InboxDashboard = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState<PeriodType>('7d');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getMetrics(period);
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load metrics');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
  }, [period]);

  const handleNavigate = (route: string) => {
    navigate(route);
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount}`;
  };

  if (isLoading) {
    return (
      <div className="inbox-dashboard">
        <div className="inbox-dashboard__header">
          <h1 className="inbox-dashboard__title">Inbox</h1>
        </div>
        <div className="inbox-dashboard__loading">
          <Loader text="Loading dashboard..." />
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="inbox-dashboard">
        <div className="inbox-dashboard__header">
          <h1 className="inbox-dashboard__title">Inbox</h1>
        </div>
        <div className="inbox-dashboard__error">
          <p>{error || 'Failed to load metrics'}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="inbox-dashboard">
      {/* Header with Quick Actions */}
      <div className="inbox-dashboard__header">
        <div className="inbox-dashboard__header-left">
          <h1 className="inbox-dashboard__title">Inbox</h1>
          <p className="inbox-dashboard__subtitle">Your unified outreach command center</p>
        </div>
        <div className="inbox-dashboard__header-right">
          {/* Quick Action Buttons */}
          <div className="quick-action-buttons">
            <button
              className="quick-action-btn quick-action-btn--primary"
              onClick={() => handleNavigate('/inbox/messages')}
            >
              View All Messages
              <span className="quick-action-btn__badge">{metrics.funnel.replied}</span>
            </button>
            {metrics.needs_attention.total > 0 && (
              <button
                className="quick-action-btn quick-action-btn--attention"
                onClick={() => handleNavigate('/inbox/messages?tab=attention')}
              >
                Needs Attention
                <span className="quick-action-btn__badge">{metrics.needs_attention.total}</span>
              </button>
            )}
          </div>
          
          {/* Period Selector */}
          <div className="period-selector">
            {(['7d', '30d', '90d'] as PeriodType[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`period-selector__btn ${period === p ? 'period-selector__btn--active' : ''}`}
              >
                {p === '7d' ? '7D' : p === '30d' ? '30D' : '90D'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="inbox-dashboard__metrics">
        <MetricsCard
          title="Response Rate"
          value={`${metrics.response_rate.value}%`}
          trend={metrics.response_rate.trend}
          trendLabel="vs last period"
          color="var(--metric-primary)"
          onClick={() => handleNavigate('/inbox/messages')}
        />
        <MetricsCard
          title="Hot Leads"
          value={metrics.hot_leads.count}
          subtitle={metrics.hot_leads.urgent > 0 ? `${metrics.hot_leads.urgent} urgent` : undefined}
          color="var(--metric-hot)"
          onClick={() => handleNavigate('/inbox/messages?temperature=hot')}
        />
        <MetricsCard
          title="Awaiting Response"
          value={metrics.needs_attention.unread}
          subtitle={metrics.needs_attention.overdue > 0 ? `${metrics.needs_attention.overdue} overdue` : undefined}
          color="var(--metric-warning)"
          onClick={() => handleNavigate('/inbox/messages?tab=attention')}
        />
        <MetricsCard
          title="Pipeline Value"
          value={formatCurrency(metrics.pipeline_value.amount)}
          subtitle={`${metrics.pipeline_value.deals} deals`}
          color="var(--metric-success)"
          onClick={() => handleNavigate('/inbox/messages?status=deal_open')}
        />
      </div>

      {/* Main Content Grid */}
      <div className="inbox-dashboard__grid">
        {/* Left Column - AI Insights */}
        <div className="inbox-dashboard__section">
          <InboxyRecommender maxItems={4} />
        </div>

        {/* Right Column - Analytics */}
        <div className="inbox-dashboard__section">
          <div className="inbox-dashboard__charts">
            <ConversionFunnel data={metrics.funnel} />
            <ChannelPerformance data={metrics.channel_performance} />
          </div>
        </div>
      </div>
    </div>
  );
};
