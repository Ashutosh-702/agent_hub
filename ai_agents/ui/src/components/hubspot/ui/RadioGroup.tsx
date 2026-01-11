interface RadioOption<T extends string> {
  value: T;
  label: string;
  description?: string;
}

interface RadioGroupProps<T extends string> {
  options: RadioOption<T>[];
  value: T | undefined;
  onChange: (value: T) => void;
  name: string;
  label?: string;
  orientation?: 'horizontal' | 'vertical';
}

export function RadioGroup<T extends string>({
  options,
  value,
  onChange,
  name,
  label,
  orientation = 'vertical',
}: RadioGroupProps<T>) {
  return (
    <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
      {label && (
        <legend
          style={{
            marginBottom: '0.75rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            color: 'var(--color-gray-700)',
          }}
        >
          {label}
        </legend>
      )}
      <div
        style={{
          display: 'flex',
          flexDirection: orientation === 'vertical' ? 'column' : 'row',
          gap: '0.75rem',
        }}
      >
        {options.map((option) => {
          const isSelected = value === option.value;

          return (
            <label
              key={option.value}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '1rem 1.25rem',
                background: isSelected ? 'rgba(46, 49, 190, 0.04)' : 'var(--color-gray-50)',
                border: `2px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-gray-200)'}`,
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                flex: orientation === 'horizontal' ? 1 : undefined,
              }}
              onMouseOver={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.borderColor = 'var(--color-gray-300)';
                  e.currentTarget.style.background = 'var(--color-gray-100)';
                }
              }}
              onMouseOut={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.borderColor = 'var(--color-gray-200)';
                  e.currentTarget.style.background = 'var(--color-gray-50)';
                }
              }}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={isSelected}
                onChange={() => onChange(option.value)}
                style={{
                  width: '20px',
                  height: '20px',
                  accentColor: 'var(--color-primary)',
                  cursor: 'pointer',
                  marginTop: '0.125rem',
                }}
              />
              <div style={{ flex: 1 }}>
                <span
                  style={{
                    display: 'block',
                    fontWeight: 600,
                    fontSize: '0.9375rem',
                    color: isSelected ? 'var(--color-primary)' : 'var(--color-gray-800)',
                  }}
                >
                  {option.label}
                </span>
                {option.description && (
                  <span
                    style={{
                      display: 'block',
                      marginTop: '0.25rem',
                      fontSize: '0.8125rem',
                      color: 'var(--color-gray-500)',
                      lineHeight: 1.4,
                    }}
                  >
                    {option.description}
                  </span>
                )}
              </div>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}


