import type { ReactNode } from 'react';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'default' | 'high' | 'medium' | 'low';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  success: { bg: 'rgba(16, 185, 129, 0.12)', text: '#059669' },
  warning: { bg: 'rgba(245, 158, 11, 0.12)', text: '#d97706' },
  error: { bg: 'rgba(239, 68, 68, 0.12)', text: '#dc2626' },
  info: { bg: 'rgba(59, 130, 246, 0.12)', text: '#2563eb' },
  default: { bg: 'rgba(107, 114, 128, 0.12)', text: '#4b5563' },
  high: { bg: 'rgba(16, 185, 129, 0.12)', text: '#059669' },
  medium: { bg: 'rgba(245, 158, 11, 0.12)', text: '#d97706' },
  low: { bg: 'rgba(239, 68, 68, 0.12)', text: '#dc2626' },
};

export const Badge = ({ children, variant = 'default', size = 'sm' }: BadgeProps) => {
  const styles = variantStyles[variant];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: size === 'sm' ? '0.125rem 0.5rem' : '0.25rem 0.75rem',
        fontSize: size === 'sm' ? '0.6875rem' : '0.75rem',
        fontWeight: 600,
        borderRadius: '4px',
        backgroundColor: styles.bg,
        color: styles.text,
        textTransform: 'capitalize',
        letterSpacing: '0.01em',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  );
};

// Confidence Badge - specialized for showing enrichment confidence
export const ConfidenceBadge = ({ confidence }: { confidence: 'high' | 'medium' | 'low' }) => {
  const icons: Record<string, string> = {
    high: '✓',
    medium: '~',
    low: '?',
  };

  return (
    <Badge variant={confidence} size="sm">
      {icons[confidence]} {confidence}
    </Badge>
  );
};


