import type { ReactNode, CSSProperties } from 'react';

interface CardProps {
  children: ReactNode;
  style?: CSSProperties;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  variant?: 'default' | 'elevated' | 'outlined';
}

const paddingStyles = {
  none: '0',
  sm: '1rem',
  md: '1.5rem',
  lg: '2rem',
};

const variantStyles = {
  default: {
    background: 'var(--color-white)',
    border: '1px solid var(--color-gray-200)',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
  },
  elevated: {
    background: 'var(--color-white)',
    border: 'none',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
  },
  outlined: {
    background: 'transparent',
    border: '1px solid var(--color-gray-200)',
    boxShadow: 'none',
  },
};

export const Card = ({
  children,
  style,
  className,
  padding = 'md',
  variant = 'default',
}: CardProps) => {
  const vStyles = variantStyles[variant];

  return (
    <div
      className={className}
      style={{
        padding: paddingStyles[padding],
        borderRadius: '12px',
        ...vStyles,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// Card Header
export const CardHeader = ({
  children,
  style,
}: {
  children: ReactNode;
  style?: CSSProperties;
}) => (
  <div
    style={{
      marginBottom: '1.5rem',
      paddingBottom: '1rem',
      borderBottom: '1px solid var(--color-gray-100)',
      ...style,
    }}
  >
    {children}
  </div>
);

// Card Title
export const CardTitle = ({
  children,
  subtitle,
}: {
  children: ReactNode;
  subtitle?: string;
}) => (
  <div>
    <h3
      style={{
        margin: 0,
        fontSize: '1.25rem',
        fontWeight: 700,
        color: 'var(--color-gray-900)',
      }}
    >
      {children}
    </h3>
    {subtitle && (
      <p
        style={{
          margin: '0.25rem 0 0 0',
          fontSize: '0.875rem',
          color: 'var(--color-gray-500)',
        }}
      >
        {subtitle}
      </p>
    )}
  </div>
);

// Card Footer
export const CardFooter = ({
  children,
  style,
}: {
  children: ReactNode;
  style?: CSSProperties;
}) => (
  <div
    style={{
      marginTop: '1.5rem',
      paddingTop: '1rem',
      borderTop: '1px solid var(--color-gray-100)',
      display: 'flex',
      justifyContent: 'flex-end',
      gap: '0.75rem',
      ...style,
    }}
  >
    {children}
  </div>
);


