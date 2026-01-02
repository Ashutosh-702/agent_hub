import type { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

export const Input = ({
  label,
  error,
  hint,
  leftIcon,
  rightIcon,
  fullWidth = true,
  style,
  id,
  ...props
}: InputProps) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div style={{ width: fullWidth ? '100%' : 'auto' }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            color: 'var(--color-gray-700)',
          }}
        >
          {label}
          {props.required && <span style={{ color: 'var(--color-error)', marginLeft: '0.25rem' }}>*</span>}
        </label>
      )}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {leftIcon && (
          <span
            style={{
              position: 'absolute',
              left: '0.75rem',
              color: 'var(--color-gray-400)',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {leftIcon}
          </span>
        )}
        <input
          id={inputId}
          style={{
            width: '100%',
            padding: '0.75rem 1rem',
            paddingLeft: leftIcon ? '2.5rem' : '1rem',
            paddingRight: rightIcon ? '2.5rem' : '1rem',
            fontSize: '0.9375rem',
            fontFamily: 'inherit',
            border: `1px solid ${error ? 'var(--color-error)' : 'var(--color-gray-300)'}`,
            borderRadius: '8px',
            backgroundColor: 'var(--color-white)',
            color: 'var(--color-gray-800)',
            transition: 'all 0.15s ease',
            outline: 'none',
            ...style,
          }}
          onFocus={(e) => {
            e.target.style.borderColor = error ? 'var(--color-error)' : 'var(--color-primary)';
            e.target.style.boxShadow = `0 0 0 3px ${error ? 'rgba(220, 38, 38, 0.1)' : 'rgba(46, 49, 190, 0.1)'}`;
          }}
          onBlur={(e) => {
            e.target.style.borderColor = error ? 'var(--color-error)' : 'var(--color-gray-300)';
            e.target.style.boxShadow = 'none';
          }}
          {...props}
        />
        {rightIcon && (
          <span
            style={{
              position: 'absolute',
              right: '0.75rem',
              color: 'var(--color-gray-400)',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {rightIcon}
          </span>
        )}
      </div>
      {(error || hint) && (
        <p
          style={{
            marginTop: '0.375rem',
            fontSize: '0.8125rem',
            color: error ? 'var(--color-error)' : 'var(--color-gray-500)',
          }}
        >
          {error || hint}
        </p>
      )}
    </div>
  );
};

