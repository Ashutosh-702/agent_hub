import React from 'react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  color?: string;
  onClick?: () => void;
}

export const MetricsCard = ({
  title,
  value,
  subtitle,
  trend,
  trendLabel,
  icon,
  color = 'var(--color-primary)',
  onClick,
}: MetricsCardProps) => {
  const isPositiveTrend = trend !== undefined && trend >= 0;

  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--color-white)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--color-gray-200)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseOver={(e) => {
        if (onClick) {
          e.currentTarget.style.borderColor = color;
          e.currentTarget.style.boxShadow = `0 4px 12px ${color}20`;
        }
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-gray-200)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Color accent bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: color,
          opacity: 0.8,
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <p
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--color-gray-500)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              margin: 0,
              marginBottom: '0.5rem',
            }}
          >
            {title}
          </p>
          <p
            style={{
              fontSize: '2rem',
              fontWeight: 700,
              color: 'var(--color-gray-900)',
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            {value}
          </p>
          {subtitle && (
            <p
              style={{
                fontSize: '0.875rem',
                color: 'var(--color-gray-500)',
                margin: 0,
                marginTop: '0.25rem',
              }}
            >
              {subtitle}
            </p>
          )}
          {trend !== undefined && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                marginTop: '0.75rem',
                padding: '0.25rem 0.5rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: isPositiveTrend ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                color: isPositiveTrend ? '#059669' : '#dc2626',
              }}
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{
                  transform: isPositiveTrend ? 'rotate(0deg)' : 'rotate(180deg)',
                }}
              >
                <polyline points="18 15 12 9 6 15" />
              </svg>
              {Math.abs(trend).toFixed(1)}%{trendLabel && ` ${trendLabel}`}
            </div>
          )}
        </div>
        {icon && (
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: `${color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color,
              fontSize: '1.5rem',
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

