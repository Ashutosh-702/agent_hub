import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Recommendation } from '../../services/inboxyApi';
import { getRecommendations, getRecommendationIcon, getPriorityColor } from '../../services/inboxyApi';

interface InboxyRecommenderProps {
  maxItems?: number;
  compact?: boolean;
}

export const InboxyRecommender = ({ maxItems = 5, compact = false }: InboxyRecommenderProps) => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [aiPowered, setAiPowered] = useState(false);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setIsLoading(true);
      try {
        const data = await getRecommendations(maxItems);
        setRecommendations(data.recommendations);
        setAiPowered(data.ai_powered);
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
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
          borderRadius: '16px',
          padding: '1.5rem',
          color: 'white',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ fontSize: '1.5rem' }}>✨</span>
          <span style={{ fontWeight: 600, fontSize: '1.125rem' }}>Inboxy</span>
          <span
            style={{
              fontSize: '0.75rem',
              background: 'rgba(255,255,255,0.2)',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
            }}
          >
            AI Recommender
          </span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: '60px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '8px',
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
        background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
        borderRadius: '16px',
        overflow: 'hidden',
        color: 'white',
      }}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: '100%',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'none',
          border: 'none',
          color: 'white',
          cursor: 'pointer',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.5rem' }}>✨</span>
          <span style={{ fontWeight: 700, fontSize: '1.125rem' }}>Inboxy</span>
          <span
            style={{
              fontSize: '0.6875rem',
              fontWeight: 600,
              background: aiPowered ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.2)',
              padding: '0.25rem 0.625rem',
              borderRadius: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {aiPowered ? 'AI Powered' : 'Smart Insights'}
          </span>
          {recommendations.filter((r) => r.priority === 'high').length > 0 && (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                background: '#ef4444',
                padding: '0.25rem 0.5rem',
                borderRadius: '10px',
              }}
            >
              {recommendations.filter((r) => r.priority === 'high').length} urgent
            </span>
          )}
        </div>
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
            opacity: 0.7,
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div style={{ padding: '0 1.5rem 1.5rem' }}>
          {recommendations.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '2rem',
                opacity: 0.7,
              }}
            >
              <p style={{ margin: 0 }}>No recommendations right now. You're all caught up! 🎉</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recommendations.map((rec) => (
                <div
                  key={rec.id}
                  style={{
                    background: 'rgba(255,255,255,0.08)',
                    borderRadius: '12px',
                    padding: compact ? '1rem' : '1.25rem',
                    borderLeft: `4px solid ${getPriorityColor(rec.priority)}`,
                    transition: 'all 0.2s ease',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.12)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.75rem',
                    }}
                  >
                    <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>
                      {getRecommendationIcon(rec.type)}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p
                        style={{
                          fontSize: '0.9375rem',
                          fontWeight: 600,
                          margin: 0,
                          marginBottom: '0.375rem',
                          lineHeight: 1.4,
                        }}
                      >
                        {rec.title}
                      </p>
                      {!compact && (
                        <p
                          style={{
                            fontSize: '0.8125rem',
                            opacity: 0.8,
                            margin: 0,
                            marginBottom: '0.75rem',
                            lineHeight: 1.5,
                          }}
                        >
                          {rec.description}
                        </p>
                      )}
                      <button
                        onClick={() => handleActionClick(rec.action.route)}
                        style={{
                          padding: '0.5rem 1rem',
                          fontSize: '0.8125rem',
                          fontWeight: 600,
                          background: 'rgba(255,255,255,0.15)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.375rem',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.25)';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                        }}
                      >
                        {rec.action.label}
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <line x1="5" y1="12" x2="19" y2="12" />
                          <polyline points="12 5 19 12 12 19" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

