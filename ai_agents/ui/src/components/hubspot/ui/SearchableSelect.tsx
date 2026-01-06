import { useState, useRef, useEffect } from 'react';

interface Option {
  value: string;
  label: string;
  secondary?: string;
}

interface SearchableSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  onSearch?: (query: string) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  isLoading?: boolean;
  required?: boolean;
}

export const SearchableSelect = ({
  options,
  value,
  onChange,
  onSearch,
  label,
  placeholder = 'Search...',
  error,
  isLoading = false,
  required,
}: SearchableSelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((o) => o.value === value);

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

  // Handle search
  useEffect(() => {
    if (onSearch && searchQuery) {
      const timeout = setTimeout(() => onSearch(searchQuery), 300);
      return () => clearTimeout(timeout);
    }
  }, [searchQuery, onSearch]);

  const filteredOptions = searchQuery
    ? options.filter(
        (o) =>
          o.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          o.secondary?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

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
          padding: '0.75rem 1rem',
          border: `1px solid ${error ? 'var(--color-error)' : isOpen ? 'var(--color-primary)' : 'var(--color-gray-300)'}`,
          borderRadius: '8px',
          background: 'var(--color-white)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'all 0.15s ease',
          boxShadow: isOpen ? '0 0 0 3px rgba(46, 49, 190, 0.1)' : 'none',
        }}
      >
        <span
          style={{
            color: selectedOption ? 'var(--color-gray-800)' : 'var(--color-gray-400)',
            fontSize: '0.9375rem',
          }}
        >
          {selectedOption ? selectedOption.label : placeholder}
        </span>
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
              filteredOptions.map((option) => (
                <div
                  key={option.value}
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                    setSearchQuery('');
                  }}
                  style={{
                    padding: '0.75rem 1rem',
                    cursor: 'pointer',
                    background: option.value === value ? 'var(--color-primary-light)' : 'transparent',
                    transition: 'background 0.1s ease',
                  }}
                  onMouseOver={(e) => {
                    if (option.value !== value) {
                      e.currentTarget.style.background = 'var(--color-gray-50)';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (option.value !== value) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.9375rem',
                      fontWeight: option.value === value ? 600 : 400,
                      color: option.value === value ? 'var(--color-primary)' : 'var(--color-gray-800)',
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
              ))
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


