import type { Insight } from './useMeetingWebSocket';

interface LiveInsightsProps {
  insights: Insight[];
  pinnedIds: Set<string>;
  onPin: (id: string) => void;
  onAddActionItem: (item: string) => void;
}

// Icons for different insight types
const InsightIcons: Record<string, string> = {
  objection_detected: '⚠️',
  buying_signal: '✨',
  competitor_mention: '🏢',
  pricing_question: '💰',
  timeline_question: '📅',
  product_opportunity: '🎯',
  next_step_suggestion: '➡️',
  risk_flag: '🚩',
  discovery_opportunity: '🔍',
  feature_interest: '💡',
};

// Type labels
const TypeLabels: Record<string, string> = {
  objection_detected: 'Objection',
  buying_signal: 'Buying Signal',
  competitor_mention: 'Competitor',
  pricing_question: 'Pricing',
  timeline_question: 'Timeline',
  product_opportunity: 'Opportunity',
  next_step_suggestion: 'Next Step',
  risk_flag: 'Risk',
  discovery_opportunity: 'Discovery',
  feature_interest: 'Feature',
};

export const LiveInsights = ({ insights, pinnedIds, onPin, onAddActionItem }: LiveInsightsProps) => {
  // Sort insights: pinned first, then by timestamp (newest first)
  const sortedInsights = [...insights].sort((a, b) => {
    const aPinned = pinnedIds.has(a.id);
    const bPinned = pinnedIds.has(b.id);
    if (aPinned && !bPinned) return -1;
    if (!aPinned && bPinned) return 1;
    return b.timestamp - a.timestamp;
  });
  
  if (insights.length === 0) {
    return (
      <div className="insights-empty">
        <div className="insights-empty-icon">💡</div>
        <p>No insights yet</p>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', marginTop: '0.5rem' }}>
          AI insights will appear here as you discuss
        </p>
      </div>
    );
  }
  
  return (
    <div>
      {sortedInsights.map((insight) => (
        <div
          key={insight.id}
          className={`insight-card ${pinnedIds.has(insight.id) ? 'pinned' : ''}`}
        >
          <div className="insight-header">
            <span className="insight-icon">
              {InsightIcons[insight.type] || '💡'}
            </span>
            <span className="insight-type-badge">
              {TypeLabels[insight.type] || insight.type}
            </span>
            {insight.confidence && insight.confidence >= 0.8 && (
              <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: 'var(--color-gray-400)' }}>
                High confidence
              </span>
            )}
          </div>
          
          <p className="insight-message">{insight.message}</p>
          
          {insight.suggestedResponse && (
            <p className="insight-response">
              <strong>Suggested:</strong> {insight.suggestedResponse}
            </p>
          )}
          
          <div className="insight-actions">
            <button
              className={`insight-action-btn ${pinnedIds.has(insight.id) ? 'active' : ''}`}
              onClick={() => onPin(insight.id)}
              title={pinnedIds.has(insight.id) ? 'Unpin' : 'Pin insight'}
            >
              📌 {pinnedIds.has(insight.id) ? 'Pinned' : 'Pin'}
            </button>
            
            {(insight.type === 'next_step_suggestion' || insight.type === 'product_opportunity') && (
              <button
                className="insight-action-btn"
                onClick={() => onAddActionItem(insight.message)}
                title="Add as action item"
              >
                ✓ Action
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

