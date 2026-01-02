import type { ChannelPerformance as ChannelPerformanceData } from '../../services/inboxMetricsApi';

interface ChannelPerformanceProps {
  data: ChannelPerformanceData;
}

const channelConfig = {
  email: { label: 'Email', abbr: 'EM' },
  linkedin: { label: 'LinkedIn', abbr: 'LI' },
  whatsapp: { label: 'WhatsApp', abbr: 'WA' },
  call: { label: 'Call', abbr: 'CL' },
};

export const ChannelPerformance = ({ data }: ChannelPerformanceProps) => {
  const channels = Object.entries(data)
    .filter(([_, metrics]) => metrics.sent > 0)
    .sort((a, b) => b[1].rate - a[1].rate);

  const maxRate = Math.max(...channels.map(([_, m]) => m.rate), 1);

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
        Channel Performance
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {channels.map(([channel, metrics], index) => {
          const config = channelConfig[channel as keyof typeof channelConfig];
          const barWidth = (metrics.rate / maxRate) * 100;
          const isTop = index === 0;

          return (
            <div key={channel}>
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
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '24px',
                      height: '24px',
                      borderRadius: '4px',
                      background: isTop ? '#374151' : '#f3f4f6',
                      color: isTop ? '#ffffff' : '#6b7280',
                      fontSize: '0.625rem',
                      fontWeight: 600,
                    }}
                  >
                    {config.abbr}
                  </span>
                  <span
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: '#374151',
                    }}
                  >
                    {config.label}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span
                    style={{
                      fontSize: '0.9375rem',
                      fontWeight: 600,
                      color: '#111827',
                    }}
                  >
                    {metrics.rate.toFixed(1)}%
                  </span>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      color: '#9ca3af',
                      marginLeft: '0.375rem',
                    }}
                  >
                    ({metrics.replied}/{metrics.sent})
                  </span>
                </div>
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
                    width: `${barWidth}%`,
                    background: isTop ? '#374151' : '#9ca3af',
                    borderRadius: '3px',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {channels.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '1.5rem',
            color: '#9ca3af',
            fontSize: '0.875rem',
          }}
        >
          No channel data available
        </div>
      )}
    </div>
  );
};
