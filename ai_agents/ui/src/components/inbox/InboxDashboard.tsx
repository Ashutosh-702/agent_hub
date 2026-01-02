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
      {/* Header */}
      <div className="inbox-dashboard__header">
        <div className="inbox-dashboard__header-left">
          <h1 className="inbox-dashboard__title">Inbox</h1>
          <p className="inbox-dashboard__subtitle">Your unified outreach command center</p>
        </div>
        <div className="inbox-dashboard__header-right">
          {/* Period Selector */}
          <div className="period-selector">
            {(['7d', '30d', '90d'] as PeriodType[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`period-selector__btn ${period === p ? 'period-selector__btn--active' : ''}`}
              >
                {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Stats Bar */}
      <div className="inbox-dashboard__stats">
        <MetricsCard
          title="Response Rate"
          value={`${metrics.response_rate.value}%`}
          trend={metrics.response_rate.trend}
          trendLabel="vs last period"
          icon={<span>📈</span>}
          color="#10b981"
          onClick={() => handleNavigate('/inbox/messages')}
        />
        <MetricsCard
          title="Hot Leads"
          value={metrics.hot_leads.count}
          subtitle={`${metrics.hot_leads.urgent} need urgent attention`}
          icon={<span>🔥</span>}
          color="#ef4444"
          onClick={() => handleNavigate('/inbox/messages?temperature=hot')}
        />
        <MetricsCard
          title="Needs Attention"
          value={metrics.needs_attention.total}
          subtitle={`${metrics.needs_attention.unread} unread, ${metrics.needs_attention.overdue} overdue`}
          icon={<span>⚡</span>}
          color="#f59e0b"
          onClick={() => handleNavigate('/inbox/messages?tab=attention')}
        />
        <MetricsCard
          title="Pipeline Value"
          value={formatCurrency(metrics.pipeline_value.amount)}
          subtitle={`${metrics.pipeline_value.deals} active deals`}
          icon={<span>💰</span>}
          color="#6366f1"
          onClick={() => handleNavigate('/inbox/messages?status=deal_open')}
        />
      </div>

      {/* Main Content Grid */}
      <div className="inbox-dashboard__grid">
        {/* Left Column - Inboxy Recommender */}
        <div className="inbox-dashboard__left">
          <InboxyRecommender maxItems={5} />

          {/* Quick Actions */}
          <div className="quick-actions">
            <h3 className="quick-actions__title">Quick Actions</h3>
            <div className="quick-actions__grid">
              <button
                className="quick-action-card"
                onClick={() => handleNavigate('/inbox/messages')}
              >
                <span className="quick-action-card__icon">📬</span>
                <span className="quick-action-card__label">All Messages</span>
                <span className="quick-action-card__count">{metrics.funnel.replied}</span>
              </button>
              <button
                className="quick-action-card quick-action-card--hot"
                onClick={() => handleNavigate('/inbox/messages?temperature=hot')}
              >
                <span className="quick-action-card__icon">🔥</span>
                <span className="quick-action-card__label">Hot Leads</span>
                <span className="quick-action-card__count">{metrics.hot_leads.count}</span>
              </button>
              <button
                className="quick-action-card quick-action-card--attention"
                onClick={() => handleNavigate('/inbox/messages?tab=attention')}
              >
                <span className="quick-action-card__icon">⚡</span>
                <span className="quick-action-card__label">Needs Attention</span>
                <span className="quick-action-card__count">{metrics.needs_attention.total}</span>
              </button>
              <button
                className="quick-action-card"
                onClick={() => handleNavigate('/inbox/messages?tab=sequence')}
              >
                <span className="quick-action-card__icon">📋</span>
                <span className="quick-action-card__label">In Sequence</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Charts */}
        <div className="inbox-dashboard__right">
          <ConversionFunnel data={metrics.funnel} />
          <ChannelPerformance data={metrics.channel_performance} />

          {/* Weekly Comparison */}
          <div className="weekly-comparison">
            <h3 className="weekly-comparison__title">This Week vs Last Week</h3>
            <div className="weekly-comparison__content">
              <div className="weekly-comparison__stat">
                <span className="weekly-comparison__label">This Week</span>
                <span className="weekly-comparison__value">{metrics.weekly_comparison.this_week} replies</span>
              </div>
              <div className="weekly-comparison__arrow">
                {metrics.weekly_comparison.change >= 0 ? (
                  <span style={{ color: '#10b981', fontSize: '1.5rem' }}>↑</span>
                ) : (
                  <span style={{ color: '#ef4444', fontSize: '1.5rem' }}>↓</span>
                )}
              </div>
              <div className="weekly-comparison__stat">
                <span className="weekly-comparison__label">Last Week</span>
                <span className="weekly-comparison__value">{metrics.weekly_comparison.last_week} replies</span>
              </div>
            </div>
            <div
              className="weekly-comparison__change"
              style={{
                color: metrics.weekly_comparison.change >= 0 ? '#10b981' : '#ef4444',
              }}
            >
              {metrics.weekly_comparison.change >= 0 ? '+' : ''}
              {metrics.weekly_comparison.change.toFixed(1)}% change
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

