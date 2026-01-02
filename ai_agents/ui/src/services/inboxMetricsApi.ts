// Inbox Metrics API Service
// Fetches dashboard metrics for CXO view

export interface MetricsPeriod {
  start: string;
  end: string;
  label: string;
}

export interface ResponseRateMetric {
  value: number;
  trend: number;
  benchmark: number;
}

export interface HotLeadsMetric {
  count: number;
  urgent: number;
}

export interface NeedsAttentionMetric {
  total: number;
  unread: number;
  overdue: number;
  waiting: number;
  hot_stale: number;
}

export interface PipelineValueMetric {
  amount: number;
  currency: string;
  deals: number;
}

export interface FunnelMetric {
  sent: number;
  opened: number;
  replied: number;
  meeting: number;
  deal: number;
}

export interface ChannelMetric {
  sent: number;
  replied: number;
  rate: number;
}

export interface ChannelPerformance {
  email: ChannelMetric;
  linkedin: ChannelMetric;
  whatsapp: ChannelMetric;
  call: ChannelMetric;
}

export interface WeeklyComparison {
  this_week: number;
  last_week: number;
  change: number;
}

export interface DashboardMetrics {
  period: MetricsPeriod;
  response_rate: ResponseRateMetric;
  hot_leads: HotLeadsMetric;
  needs_attention: NeedsAttentionMetric;
  pipeline_value: PipelineValueMetric;
  avg_response_time_hours: number;
  funnel: FunnelMetric;
  channel_performance: ChannelPerformance;
  weekly_comparison: WeeklyComparison;
}

const API_BASE = '/api/v1/inbox';

// Check if we should use mock API
const USE_MOCK = import.meta.env.DEV || import.meta.env.VITE_USE_REAL_API !== 'true';

// Mock metrics data
function generateMockMetrics(period: string): DashboardMetrics {
  const now = new Date();
  const days = { '7d': 7, '30d': 30, '90d': 90 }[period] || 7;
  const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

  return {
    period: {
      start: start.toISOString(),
      end: now.toISOString(),
      label: period,
    },
    response_rate: {
      value: 23.5,
      trend: 2.1,
      benchmark: 20.0,
    },
    hot_leads: {
      count: 12,
      urgent: 4,
    },
    needs_attention: {
      total: 16,
      unread: 8,
      overdue: 3,
      waiting: 3,
      hot_stale: 2,
    },
    pipeline_value: {
      amount: 185000,
      currency: 'USD',
      deals: 12,
    },
    avg_response_time_hours: 18.5,
    funnel: {
      sent: 450,
      opened: 280,
      replied: 105,
      meeting: 18,
      deal: 6,
    },
    channel_performance: {
      email: { sent: 280, replied: 42, rate: 15.0 },
      linkedin: { sent: 140, replied: 52, rate: 37.1 },
      whatsapp: { sent: 25, replied: 9, rate: 36.0 },
      call: { sent: 5, replied: 2, rate: 40.0 },
    },
    weekly_comparison: {
      this_week: 28,
      last_week: 22,
      change: 27.3,
    },
  };
}

export async function getMetrics(
  period: '7d' | '30d' | '90d' | 'custom' = '7d',
  startDate?: string,
  endDate?: string
): Promise<DashboardMetrics> {
  if (USE_MOCK) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return generateMockMetrics(period);
  }

  try {
    const params = new URLSearchParams({ period });
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);

    const response = await fetch(`${API_BASE}/metrics?${params.toString()}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.warn('Real API failed, falling back to mock:', error);
    return generateMockMetrics(period);
  }
}

