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
  color = '#374151',
  onClick,
}: MetricsCardProps) => {
  const isPositiveTrend = trend !== undefined && trend >= 0;

  return (
    <div
      onClick={onClick}
      style={{
        background: '#ffffff',
        borderRadius: '8px',
        padding: '1.25rem',
        border: '1px solid #e5e7eb',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
      }}
      onMouseOver={(e) => {
        if (onClick) {
          e.currentTarget.style.borderColor = '#d1d5db';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)';
        }
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.borderColor = '#e5e7eb';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <p
        style={{
          fontSize: '0.75rem',
          fontWeight: 500,
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          margin: 0,
          marginBottom: '0.5rem',
        }}
      >
        {title}
      </p>
      
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
        <p
          style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            color: '#111827',
            margin: 0,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
          }}
        >
          {value}
        </p>
        
        {trend !== undefined && (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 500,
              color: isPositiveTrend ? '#059669' : '#dc2626',
            }}
          >
            {isPositiveTrend ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>

      {subtitle && (
        <p
          style={{
            fontSize: '0.8125rem',
            color: '#9ca3af',
            margin: 0,
            marginTop: '0.375rem',
          }}
        >
          {subtitle}
        </p>
      )}

      {/* Subtle accent line */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: '1.25rem',
          right: '1.25rem',
          height: '2px',
          background: color,
          opacity: 0.3,
          borderRadius: '1px',
        }}
      />
    </div>
  );
};
