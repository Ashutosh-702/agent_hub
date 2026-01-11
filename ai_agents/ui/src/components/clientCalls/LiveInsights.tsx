import { useState, useEffect } from 'react';
import type { Insight } from './useMeetingWebSocket';

interface LiveInsightsProps {
  insights: Insight[];
  pinnedIds: Set<string>;
  onPin: (id: string) => void;
  onAddActionItem: (item: string) => void;
}

// Icons for different insight types - extended with new types
const InsightIcons: Record<string, string> = {
  // Detection types
  objection: '⚠️',
  objection_detected: '⚠️',
  buying_signal: '✨',
  competitor: '🏢',
  competitor_mention: '🏢',
  pricing_question: '💰',
  timeline_question: '📅',
  product_opportunity: '🎯',
  next_step_suggestion: '➡️',
  risk_flag: '🚩',
  action_item: '✅',
  // Proactive suggestion types
  discovery_question: '🔍',
  discovery_opportunity: '🔍',
  value_prop: '💎',
  product_feature: '⚡',
  feature_interest: '💡',
};

// Type labels - extended with new types
const TypeLabels: Record<string, string> = {
  // Detection types
  objection: 'Objection',
  objection_detected: 'Objection',
  buying_signal: 'Buying Signal',
  competitor: 'Competitor',
  competitor_mention: 'Competitor',
  pricing_question: 'Pricing',
  timeline_question: 'Timeline',
  product_opportunity: 'Opportunity',
  next_step_suggestion: 'Next Step',
  risk_flag: 'Risk',
  action_item: 'Action Item',
  // Proactive suggestion types
  discovery_question: 'Ask This',
  discovery_opportunity: 'Discovery',
  value_prop: 'Value Prop',
  product_feature: 'Feature',
  feature_interest: 'Feature',
};

// Badge colors for different insight categories
const BadgeColors: Record<string, { bg: string; text: string }> = {
  // Proactive suggestions - blue tones
  discovery_question: { bg: 'var(--color-primary-light)', text: 'var(--color-primary)' },
  value_prop: { bg: 'var(--color-success-light)', text: 'var(--color-success)' },
  product_feature: { bg: 'var(--color-info-light)', text: 'var(--color-info)' },
  // Detection types - varied colors
  objection: { bg: 'var(--color-warning-light)', text: 'var(--color-warning)' },
  buying_signal: { bg: 'var(--color-success-light)', text: 'var(--color-success)' },
  risk_flag: { bg: 'var(--color-error-light)', text: 'var(--color-error)' },
  competitor: { bg: 'var(--color-info-light)', text: 'var(--color-info)' },
};

export const LiveInsights = ({ insights, pinnedIds, onPin, onAddActionItem }: LiveInsightsProps) => {
  // Track which insights are new (for highlight animation)
  const [seenIds, setSeenIds] = useState<Set<string>>(new Set());
  const [newInsightIds, setNewInsightIds] = useState<Set<string>>(new Set());
  
  // Mark new insights and clear highlight after 3 seconds
  useEffect(() => {
    const newIds = new Set<string>();
    insights.forEach(insight => {
      if (!seenIds.has(insight.id)) {
        newIds.add(insight.id);
      }
    });
    
    if (newIds.size > 0) {
      setNewInsightIds(prev => new Set([...prev, ...newIds]));
      setSeenIds(prev => new Set([...prev, ...newIds]));
      
      // Clear highlight after 3 seconds
      const timeout = setTimeout(() => {
        setNewInsightIds(prev => {
          const updated = new Set(prev);
          newIds.forEach(id => updated.delete(id));
          return updated;
        });
      }, 3000);
      
      return () => clearTimeout(timeout);
    }
  }, [insights, seenIds]);
  
  // Sort insights: pinned first, then by timestamp (newest first)
  const sortedInsights = [...insights].sort((a, b) => {
    const aPinned = pinnedIds.has(a.id);
    const bPinned = pinnedIds.has(b.id);
    if (aPinned && !bPinned) return -1;
    if (!aPinned && bPinned) return 1;
    return b.timestamp - a.timestamp;
  });
  
  // Helper to check if insight type is actionable
  const isActionableType = (type: string) => {
    return ['next_step_suggestion', 'product_opportunity', 'action_item', 'value_prop', 'product_feature'].includes(type);
  };
  
  // Get badge style for insight type
  const getBadgeStyle = (type: string) => {
    const colors = BadgeColors[type];
    if (colors) {
      return {
        backgroundColor: colors.bg,
        color: colors.text,
      };
    }
    return {};
  };
  
  if (insights.length === 0) {
    return (
      <div className="insights-empty">
        <div className="insights-empty-icon">💡</div>
        <p>No insights yet</p>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', marginTop: '0.5rem' }}>
          AI-powered suggestions will appear here every 20 seconds based on your conversation
        </p>
      </div>
    );
  }
  
  return (
    <div className="insights-container">
      {sortedInsights.map((insight) => {
        const isNew = newInsightIds.has(insight.id);
        const isPinned = pinnedIds.has(insight.id);
        
        return (
          <div
            key={insight.id}
            className={`insight-card ${isPinned ? 'pinned' : ''} ${isNew ? 'insight-new' : ''}`}
            style={isNew ? {
              animation: 'insightHighlight 3s ease-out',
              boxShadow: '0 0 12px var(--color-primary-light)',
            } : {}}
          >
            <div className="insight-header">
              <span className="insight-icon">
                {InsightIcons[insight.type] || '💡'}
              </span>
              <span 
                className="insight-type-badge"
                style={getBadgeStyle(insight.type)}
              >
                {TypeLabels[insight.type] || insight.type}
              </span>
              {insight.confidence && insight.confidence >= 0.8 && (
                <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: 'var(--color-gray-400)' }}>
                  High confidence
                </span>
              )}
              {isNew && (
                <span style={{ 
                  marginLeft: insight.confidence && insight.confidence >= 0.8 ? '0.5rem' : 'auto',
                  fontSize: '0.65rem', 
                  color: 'var(--color-primary)',
                  fontWeight: 600,
                }}>
                  NEW
                </span>
              )}
            </div>
            
            <p className="insight-message">{insight.message}</p>
            
            {insight.suggestedResponse && (
              <div className="insight-response" style={{
                backgroundColor: 'var(--color-gray-50)',
                padding: '0.75rem',
                borderRadius: 'var(--border-radius-sm)',
                marginTop: '0.5rem',
                fontSize: '0.85rem',
                lineHeight: 1.5,
              }}>
                <strong style={{ color: 'var(--color-primary)' }}>Say this:</strong>{' '}
                <span style={{ color: 'var(--color-gray-700)' }}>{insight.suggestedResponse}</span>
              </div>
            )}
            
            <div className="insight-actions">
              <button
                className={`insight-action-btn ${isPinned ? 'active' : ''}`}
                onClick={() => onPin(insight.id)}
                title={isPinned ? 'Unpin' : 'Pin insight'}
              >
                {isPinned ? '📌 Pinned' : '📌 Pin'}
              </button>
              
              {isActionableType(insight.type) && (
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
        );
      })}
      
      {/* CSS for highlight animation */}
      <style>{`
        @keyframes insightHighlight {
          0% {
            box-shadow: 0 0 20px var(--color-primary);
            background-color: var(--color-primary-light);
          }
          100% {
            box-shadow: none;
            background-color: transparent;
          }
        }
        
        .insight-new {
          border-left: 3px solid var(--color-primary);
        }
        
        .insights-container {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
      `}</style>
    </div>
  );
};

