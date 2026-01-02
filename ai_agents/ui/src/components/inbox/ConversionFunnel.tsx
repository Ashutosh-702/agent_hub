import type { FunnelMetric } from '../../services/inboxMetricsApi';

interface ConversionFunnelProps {
  data: FunnelMetric;
}

export const ConversionFunnel = ({ data }: ConversionFunnelProps) => {
  const stages = [
    { key: 'sent', label: 'Sent', value: data.sent },
    { key: 'opened', label: 'Opened', value: data.opened },
    { key: 'replied', label: 'Replied', value: data.replied },
    { key: 'meeting', label: 'Meeting', value: data.meeting },
    { key: 'deal', label: 'Deal', value: data.deal },
  ];

  const maxValue = Math.max(...stages.map((s) => s.value), 1);

  return (
    <div
      style={{
        background: '#ffffff',
        borderRadius: '8px',
        padding: '1.25rem',
        border: '1px solid #e5e7eb',
      }}
    >
      <h3
        style={{
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: '#374151',
          margin: 0,
          marginBottom: '1.25rem',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        Conversion Funnel
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
        {stages.map((stage, index) => {
          const widthPercent = (stage.value / maxValue) * 100;
          const conversionRate =
            index > 0 && stages[index - 1].value > 0
              ? ((stage.value / stages[index - 1].value) * 100).toFixed(0)
              : null;

          return (
            <div key={stage.key}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.375rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span
                    style={{
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                      color: '#374151',
                    }}
                  >
                    {stage.label}
                  </span>
                  {conversionRate && (
                    <span
                      style={{
                        fontSize: '0.6875rem',
                        color: '#9ca3af',
                      }}
                    >
                      {conversionRate}%
                    </span>
                  )}
                </div>
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#111827',
                  }}
                >
                  {stage.value.toLocaleString()}
                </span>
              </div>
              <div
                style={{
                  height: '6px',
                  background: '#f3f4f6',
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${widthPercent}%`,
                    background: '#374151',
                    borderRadius: '3px',
                    transition: 'width 0.4s ease',
                    opacity: 1 - index * 0.15,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall conversion */}
      <div
        style={{
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid #f3f4f6',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          style={{
            fontSize: '0.8125rem',
            color: '#6b7280',
          }}
        >
          Overall Conversion
        </span>
        <span
          style={{
            fontSize: '1rem',
            fontWeight: 600,
            color: '#059669',
          }}
        >
          {data.sent > 0 ? ((data.deal / data.sent) * 100).toFixed(2) : 0}%
        </span>
      </div>
    </div>
  );
};
