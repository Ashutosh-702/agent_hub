import { useState, useRef, useEffect } from 'react';

interface Option {
  value: string;
  label: string;
  secondary?: string;
}

interface MultiSelectProps {
  options: Option[];
  values: string[];
  onChange: (values: string[]) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  isLoading?: boolean;
  required?: boolean;
}

export const MultiSelect = ({
  options,
  values,
  onChange,
  label,
  placeholder = 'Select options...',
  error,
  isLoading = false,
  required,
}: MultiSelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOptions = options.filter((o) => values.includes(o.value));

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredOptions = searchQuery
    ? options.filter(
        (o) =>
          o.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          o.secondary?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  const toggleOption = (optionValue: string) => {
    if (values.includes(optionValue)) {
      onChange(values.filter((v) => v !== optionValue));
    } else {
      onChange([...values, optionValue]);
    }
  };

  const removeOption = (optionValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(values.filter((v) => v !== optionValue));
  };

  return (
    <div style={{ position: 'relative' }} ref={containerRef}>
      {label && (
        <label
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            color: 'var(--color-gray-700)',
          }}
        >
          {label}
          {required && <span style={{ color: 'var(--color-error)', marginLeft: '0.25rem' }}>*</span>}
        </label>
      )}
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          minHeight: '44px',
          padding: '0.5rem',
          border: `1px solid ${error ? 'var(--color-error)' : isOpen ? 'var(--color-primary)' : 'var(--color-gray-300)'}`,
          borderRadius: '8px',
          background: 'var(--color-white)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.375rem',
          transition: 'all 0.15s ease',
          boxShadow: isOpen ? '0 0 0 3px rgba(46, 49, 190, 0.1)' : 'none',
        }}
      >
        {selectedOptions.length > 0 ? (
          selectedOptions.map((option) => (
            <span
              key={option.value}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                padding: '0.25rem 0.5rem',
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                borderRadius: '4px',
                fontSize: '0.8125rem',
                fontWeight: 500,
              }}
            >
              {option.label}
              <button
                onClick={(e) => removeOption(option.value, e)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '0.125rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  color: 'var(--color-primary)',
                  borderRadius: '2px',
                }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </span>
          ))
        ) : (
          <span style={{ color: 'var(--color-gray-400)', fontSize: '0.9375rem', paddingLeft: '0.5rem' }}>
            {placeholder}
          </span>
        )}
        <div style={{ marginLeft: 'auto', paddingRight: '0.5rem' }}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{
              color: 'var(--color-gray-400)',
              transform: isOpen ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.15s ease',
            }}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </div>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '0.25rem',
            background: 'var(--color-white)',
            border: '1px solid var(--color-gray-200)',
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
            zIndex: 100,
            maxHeight: '280px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ padding: '0.5rem', borderBottom: '1px solid var(--color-gray-100)' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search..."
              autoFocus
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid var(--color-gray-200)',
                borderRadius: '6px',
                fontSize: '0.875rem',
                outline: 'none',
              }}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {isLoading ? (
              <div
                style={{
                  padding: '1rem',
                  textAlign: 'center',
                  color: 'var(--color-gray-500)',
                  fontSize: '0.875rem',
                }}
              >
                Loading...
              </div>
            ) : filteredOptions.length === 0 ? (
              <div
                style={{
                  padding: '1rem',
                  textAlign: 'center',
                  color: 'var(--color-gray-500)',
                  fontSize: '0.875rem',
                }}
              >
                No results found
              </div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = values.includes(option.value);
                return (
                  <div
                    key={option.value}
                    onClick={() => toggleOption(option.value)}
                    style={{
                      padding: '0.75rem 1rem',
                      cursor: 'pointer',
                      background: isSelected ? 'var(--color-primary-light)' : 'transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      transition: 'background 0.1s ease',
                    }}
                    onMouseOver={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'var(--color-gray-50)';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <div
                      style={{
                        width: '18px',
                        height: '18px',
                        borderRadius: '4px',
                        border: `2px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-gray-300)'}`,
                        background: isSelected ? 'var(--color-primary)' : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      {isSelected && (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontSize: '0.9375rem',
                          fontWeight: isSelected ? 600 : 400,
                          color: isSelected ? 'var(--color-primary)' : 'var(--color-gray-800)',
                        }}
                      >
                        {option.label}
                      </div>
                      {option.secondary && (
                        <div
                          style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-gray-500)',
                            marginTop: '0.125rem',
                          }}
                        >
                          {option.secondary}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
      {error && (
        <p
          style={{
            marginTop: '0.375rem',
            fontSize: '0.8125rem',
            color: 'var(--color-error)',
          }}
        >
          {error}
        </p>
      )}
    </div>
  );
};


