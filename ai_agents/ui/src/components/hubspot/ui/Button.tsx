import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: `
    background: linear-gradient(135deg, var(--color-primary) 0%, #5558e3 100%);
    color: white;
    border: none;
    box-shadow: 0 2px 8px rgba(46, 49, 190, 0.25);
  `,
  secondary: `
    background: var(--color-gray-100);
    color: var(--color-gray-700);
    border: 1px solid var(--color-gray-200);
  `,
  outline: `
    background: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
  `,
  ghost: `
    background: transparent;
    color: var(--color-gray-600);
    border: none;
  `,
  danger: `
    background: var(--color-error);
    color: white;
    border: none;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.25);
  `,
};

const sizeStyles: Record<ButtonSize, { padding: string; fontSize: string; height: string }> = {
  sm: { padding: '0.375rem 0.75rem', fontSize: '0.8125rem', height: '32px' },
  md: { padding: '0.625rem 1.25rem', fontSize: '0.875rem', height: '40px' },
  lg: { padding: '0.875rem 1.75rem', fontSize: '1rem', height: '48px' },
};

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  disabled,
  style,
  ...props
}: ButtonProps) => {
  const sizeStyle = sizeStyles[size];

  return (
    <button
      disabled={disabled || isLoading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        padding: sizeStyle.padding,
        fontSize: sizeStyle.fontSize,
        minHeight: sizeStyle.height,
        fontWeight: 600,
        borderRadius: '8px',
        cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.15s ease',
        width: fullWidth ? '100%' : 'auto',
        fontFamily: 'inherit',
        ...Object.fromEntries(
          variantStyles[variant]
            .split(';')
            .filter(s => s.trim())
            .map(s => {
              const [key, value] = s.split(':').map(p => p.trim());
              return [key.replace(/-([a-z])/g, (_, l) => l.toUpperCase()), value];
            })
        ),
        ...style,
      }}
      {...props}
    >
      {isLoading ? (
        <span
          style={{
            width: '1rem',
            height: '1rem',
            border: '2px solid transparent',
            borderTopColor: 'currentColor',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};


