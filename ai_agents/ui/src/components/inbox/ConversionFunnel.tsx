import type { FunnelMetric } from '../../services/inboxMetricsApi';

interface ConversionFunnelProps {
  data: FunnelMetric;
}

export const ConversionFunnel = ({ data }: ConversionFunnelProps) => {
  const stages = [
    { key: 'sent', label: 'Sent', value: data.sent, color: '#6366f1' },
    { key: 'opened', label: 'Opened', value: data.opened, color: '#8b5cf6' },
    { key: 'replied', label: 'Replied', value: data.replied, color: '#10b981' },
    { key: 'meeting', label: 'Meeting', value: data.meeting, color: '#f59e0b' },
    { key: 'deal', label: 'Deal', value: data.deal, color: '#059669' },
  ];

  const maxValue = Math.max(...stages.map((s) => s.value), 1);

  return (
    <div
      style={{
        background: 'var(--color-white)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--color-gray-200)',
      }}
    >
      <h3
        style={{
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--color-gray-900)',
          margin: 0,
          marginBottom: '1.5rem',
        }}
      >
        Conversion Funnel
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {stages.map((stage, index) => {
          const widthPercent = (stage.value / maxValue) * 100;
          const conversionRate =
            index > 0 && stages[index - 1].value > 0
              ? ((stage.value / stages[index - 1].value) * 100).toFixed(1)
              : null;

          return (
            <div key={stage.key}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'var(--color-gray-700)',
                    }}
                  >
                    {stage.label}
                  </span>
                  {conversionRate && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: 'var(--color-gray-400)',
                      }}
                    >
                      ({conversionRate}%)
                    </span>
                  )}
                </div>
                <span
                  style={{
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: stage.color,
                  }}
                >
                  {stage.value.toLocaleString()}
                </span>
              </div>
              <div
                style={{
                  height: '8px',
                  background: 'var(--color-gray-100)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${widthPercent}%`,
                    background: stage.color,
                    borderRadius: '4px',
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall conversion rate */}
      <div
        style={{
          marginTop: '1.5rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--color-gray-100)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          style={{
            fontSize: '0.875rem',
            color: 'var(--color-gray-600)',
          }}
        >
          Overall Conversion (Sent → Deal)
        </span>
        <span
          style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: '#059669',
          }}
        >
          {data.sent > 0 ? ((data.deal / data.sent) * 100).toFixed(2) : 0}%
        </span>
      </div>
    </div>
  );
};

