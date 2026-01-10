import type { SelectHTMLAttributes } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  hint?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
  onChange?: (value: string) => void;
}

export const Select = ({
  label,
  error,
  hint,
  options,
  placeholder,
  fullWidth = true,
  onChange,
  id,
  value,
  ...props
}: SelectProps) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div style={{ width: fullWidth ? '100%' : 'auto' }}>
      {label && (
        <label
          htmlFor={selectId}
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
      <div style={{ position: 'relative' }}>
        <select
          id={selectId}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem 2.5rem 0.75rem 1rem',
            fontSize: '0.9375rem',
            fontFamily: 'inherit',
            border: `1px solid ${error ? 'var(--color-error)' : 'var(--color-gray-300)'}`,
            borderRadius: '8px',
            backgroundColor: 'var(--color-white)',
            color: value ? 'var(--color-gray-800)' : 'var(--color-gray-400)',
            transition: 'all 0.15s ease',
            outline: 'none',
            appearance: 'none',
            cursor: 'pointer',
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
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <div
          style={{
            position: 'absolute',
            right: '1rem',
            top: '50%',
            transform: 'translateY(-50%)',
            pointerEvents: 'none',
            color: 'var(--color-gray-400)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
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


