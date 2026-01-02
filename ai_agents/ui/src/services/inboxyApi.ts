// Inboxy AI Recommendations API Service
// Fetches smart recommendations for CXO/Founders

export type RecommendationType =
  | 'priority_leads'
  | 'followup_alert'
  | 'channel_insight'
  | 'timing_optimization'
  | 'buying_signals'
  | 'risk_alert'
  | 'performance_insight';

export type RecommendationPriority = 'high' | 'medium' | 'low';

export interface RecommendationAction {
  label: string;
  route: string;
}

export interface Recommendation {
  id: string;
  type: RecommendationType;
  priority: RecommendationPriority;
  title: string;
  description: string;
  action: RecommendationAction;
  leads: string[];
  metadata: Record<string, unknown>;
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
  generated_at: string;
  ai_powered: boolean;
  count: number;
}

const API_BASE = '/api/v1/inbox';

// Check if we should use mock API
const USE_MOCK = import.meta.env.DEV || import.meta.env.VITE_USE_REAL_API !== 'true';

// Mock recommendations
function generateMockRecommendations(): RecommendationsResponse {
  return {
    recommendations: [
      {
        id: 'rec_priority_1',
        type: 'priority_leads',
        priority: 'high',
        title: '5 hot leads need your attention today',
        description: 'These leads have shown strong buying signals and are waiting for your response. Prioritize them to maximize conversion.',
        action: { label: 'View Hot Leads', route: '/inbox/messages?temperature=hot' },
        leads: ['lead_1', 'lead_2', 'lead_3', 'lead_4', 'lead_5'],
        metadata: {},
      },
      {
        id: 'rec_unread_1',
        type: 'priority_leads',
        priority: 'high',
        title: '8 unread replies waiting',
        description: 'You have leads actively engaging with you. Quick responses improve conversion rates by up to 50%.',
        action: { label: 'View Unread', route: '/inbox/messages?tab=attention' },
        leads: [],
        metadata: { unread_count: 8 },
      },
      {
        id: 'rec_followup_1',
        type: 'followup_alert',
        priority: 'high',
        title: '3 leads haven\'t been contacted in 5+ days',
        description: 'These conversations have gone cold. A quick follow-up could re-engage them before they lose interest.',
        action: { label: 'View Stale Leads', route: '/inbox/messages?sort=oldest' },
        leads: ['lead_6', 'lead_7', 'lead_8'],
        metadata: {},
      },
      {
        id: 'rec_channel_1',
        type: 'channel_insight',
        priority: 'medium',
        title: 'LinkedIn is outperforming email by 2.5x',
        description: 'This week, LinkedIn has a 37% reply rate vs 15% for email. Consider shifting more outreach to LinkedIn.',
        action: { label: 'View LinkedIn Leads', route: '/inbox/messages?channel=linkedin' },
        leads: [],
        metadata: { linkedin_rate: 37, email_rate: 15 },
      },
      {
        id: 'rec_risk_1',
        type: 'risk_alert',
        priority: 'high',
        title: '2 hot leads are going cold',
        description: 'These high-value leads haven\'t had activity in 3+ days. Immediate action recommended to prevent losing them.',
        action: { label: 'Take Action', route: '/inbox/messages?temperature=hot&sort=oldest' },
        leads: ['lead_9', 'lead_10'],
        metadata: {},
      },
      {
        id: 'rec_timing_1',
        type: 'timing_optimization',
        priority: 'low',
        title: 'Best time to send: Tuesday-Thursday, 9-11 AM',
        description: 'Based on your reply patterns, leads are most responsive during mid-week mornings. Schedule your outreach accordingly.',
        action: { label: 'View Analytics', route: '/inbox/messages' },
        leads: [],
        metadata: { best_days: ['Tuesday', 'Wednesday', 'Thursday'], best_hours: '9-11 AM' },
      },
      {
        id: 'rec_perf_1',
        type: 'performance_insight',
        priority: 'low',
        title: 'Replies up 27% this week',
        description: 'Great progress! You received 28 replies this week vs 22 last week. Keep up the momentum!',
        action: { label: 'View Details', route: '/inbox/messages' },
        leads: [],
        metadata: { this_week: 28, last_week: 22, change: 27 },
      },
    ],
    generated_at: new Date().toISOString(),
    ai_powered: false,
    count: 7,
  };
}

export async function getRecommendations(limit: number = 5): Promise<RecommendationsResponse> {
  if (USE_MOCK) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));
    const mock = generateMockRecommendations();
    return {
      ...mock,
      recommendations: mock.recommendations.slice(0, limit),
      count: Math.min(mock.recommendations.length, limit),
    };
  }

  try {
    const response = await fetch(`${API_BASE}/recommendations?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.warn('Real API failed, falling back to mock:', error);
    const mock = generateMockRecommendations();
    return {
      ...mock,
      recommendations: mock.recommendations.slice(0, limit),
      count: Math.min(mock.recommendations.length, limit),
    };
  }
}

// Helper to get icon for recommendation type
export function getRecommendationIcon(type: RecommendationType): string {
  const icons: Record<RecommendationType, string> = {
    priority_leads: '🎯',
    followup_alert: '⏰',
    channel_insight: '📊',
    timing_optimization: '🕐',
    buying_signals: '💰',
    risk_alert: '⚠️',
    performance_insight: '📈',
  };
  return icons[type] || '💡';
}

// Helper to get color for priority
export function getPriorityColor(priority: RecommendationPriority): string {
  const colors: Record<RecommendationPriority, string> = {
    high: '#ef4444',
    medium: '#f59e0b',
    low: '#6b7280',
  };
  return colors[priority] || '#6b7280';
}

