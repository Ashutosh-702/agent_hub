import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Recommendation, RecommendationType, RecommendationPriority } from '../../services/inboxyApi';
import { getRecommendations } from '../../services/inboxyApi';

interface InboxyRecommenderProps {
  maxItems?: number;
  compact?: boolean;
}

// Simple, professional icons as text
const typeIcons: Record<RecommendationType, string> = {
  priority_leads: '●',
  followup_alert: '○',
  channel_insight: '◐',
  timing_optimization: '◑',
  buying_signals: '◆',
  risk_alert: '▲',
  performance_insight: '◇',
};

const priorityStyles: Record<RecommendationPriority, { bg: string; border: string; dot: string }> = {
  high: { bg: '#fef2f2', border: '#fecaca', dot: '#dc2626' },
  medium: { bg: '#fffbeb', border: '#fde68a', dot: '#d97706' },
  low: { bg: '#f9fafb', border: '#e5e7eb', dot: '#6b7280' },
};

export const InboxyRecommender = ({ maxItems = 5 }: InboxyRecommenderProps) => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setIsLoading(true);
      try {
        const data = await getRecommendations(maxItems);
        setRecommendations(data.recommendations);
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [maxItems]);

  const handleActionClick = (route: string) => {
    navigate(route);
  };

  if (isLoading) {
    return (
      <div
        style={{
          background: '#ffffff',
          borderRadius: '8px',
          padding: '1.25rem',
          border: '1px solid #e5e7eb',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '1rem',
          }}
        >
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: '#374151',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            AI Insights
          </span>
          <span
            style={{
              fontSize: '0.625rem',
              fontWeight: 500,
              padding: '0.125rem 0.375rem',
              borderRadius: '3px',
              background: '#f3f4f6',
              color: '#6b7280',
            }}
          >
            INBOXY
          </span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: '60px',
                background: '#f9fafb',
                borderRadius: '6px',
                animation: 'pulse 1.5s infinite',
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        background: '#ffffff',
        borderRadius: '8px',
        padding: '1.25rem',
        border: '1px solid #e5e7eb',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: '#374151',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            AI Insights
          </span>
          <span
            style={{
              fontSize: '0.625rem',
              fontWeight: 500,
              padding: '0.125rem 0.375rem',
              borderRadius: '3px',
              background: '#374151',
              color: '#ffffff',
            }}
          >
            INBOXY
          </span>
        </div>
        {recommendations.filter((r) => r.priority === 'high').length > 0 && (
          <span
            style={{
              fontSize: '0.6875rem',
              fontWeight: 600,
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              background: '#fef2f2',
              color: '#dc2626',
            }}
          >
            {recommendations.filter((r) => r.priority === 'high').length} action needed
          </span>
        )}
      </div>

      {/* Recommendations */}
      {recommendations.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '2rem 1rem',
            color: '#9ca3af',
            fontSize: '0.875rem',
          }}
        >
          No recommendations right now. You're all caught up!
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {recommendations.map((rec) => {
            const styles = priorityStyles[rec.priority];

            return (
              <div
                key={rec.id}
                style={{
                  background: styles.bg,
                  border: `1px solid ${styles.border}`,
                  borderRadius: '6px',
                  padding: '1rem',
                  transition: 'all 0.15s ease',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.04)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem',
                  }}
                >
                  {/* Priority indicator */}
                  <span
                    style={{
                      color: styles.dot,
                      fontSize: '0.5rem',
                      marginTop: '0.375rem',
                    }}
                  >
                    {typeIcons[rec.type]}
                  </span>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p
                      style={{
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        color: '#111827',
                        margin: 0,
                        marginBottom: '0.25rem',
                        lineHeight: 1.4,
                      }}
                    >
                      {rec.title}
                    </p>
                    <p
                      style={{
                        fontSize: '0.8125rem',
                        color: '#6b7280',
                        margin: 0,
                        marginBottom: '0.75rem',
                        lineHeight: 1.5,
                      }}
                    >
                      {rec.description}
                    </p>
                    <button
                      onClick={() => handleActionClick(rec.action.route)}
                      style={{
                        padding: '0.375rem 0.75rem',
                        fontSize: '0.75rem',
                        fontWeight: 500,
                        background: '#374151',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = '#1f2937';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = '#374151';
                      }}
                    >
                      {rec.action.label} →
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
