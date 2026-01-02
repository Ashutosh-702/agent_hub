import type { ChannelPerformance as ChannelPerformanceData } from '../../services/inboxMetricsApi';

interface ChannelPerformanceProps {
  data: ChannelPerformanceData;
}

const channelConfig = {
  email: { label: 'Email', icon: '✉️', color: '#3b82f6' },
  linkedin: { label: 'LinkedIn', icon: '💼', color: '#0077b5' },
  whatsapp: { label: 'WhatsApp', icon: '💬', color: '#25d366' },
  call: { label: 'Call', icon: '📞', color: '#8b5cf6' },
};

export const ChannelPerformance = ({ data }: ChannelPerformanceProps) => {
  const channels = Object.entries(data)
    .filter(([_, metrics]) => metrics.sent > 0)
    .sort((a, b) => b[1].rate - a[1].rate);

  const maxRate = Math.max(...channels.map(([_, m]) => m.rate), 1);

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
        Channel Performance
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {channels.map(([channel, metrics]) => {
          const config = channelConfig[channel as keyof typeof channelConfig];
          const barWidth = (metrics.rate / maxRate) * 100;

          return (
            <div key={channel}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.25rem' }}>{config.icon}</span>
                  <span
                    style={{
                      fontSize: '0.9375rem',
                      fontWeight: 500,
                      color: 'var(--color-gray-700)',
                    }}
                  >
                    {config.label}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span
                    style={{
                      fontSize: '1.125rem',
                      fontWeight: 700,
                      color: config.color,
                    }}
                  >
                    {metrics.rate.toFixed(1)}%
                  </span>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-gray-400)',
                      marginLeft: '0.5rem',
                    }}
                  >
                    ({metrics.replied}/{metrics.sent})
                  </span>
                </div>
              </div>
              <div
                style={{
                  height: '10px',
                  background: 'var(--color-gray-100)',
                  borderRadius: '5px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${barWidth}%`,
                    background: `linear-gradient(90deg, ${config.color}, ${config.color}cc)`,
                    borderRadius: '5px',
                    transition: 'width 0.5s ease',
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
            padding: '2rem',
            color: 'var(--color-gray-400)',
          }}
        >
          No channel data available
        </div>
      )}

      {/* Best channel insight */}
      {channels.length > 0 && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1rem',
            background: 'rgba(16, 185, 129, 0.05)',
            borderRadius: '8px',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1rem' }}>💡</span>
            <span
              style={{
                fontSize: '0.875rem',
                color: '#059669',
                fontWeight: 500,
              }}
            >
              {channelConfig[channels[0][0] as keyof typeof channelConfig].label} has the highest
              reply rate at {channels[0][1].rate.toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

