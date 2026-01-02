interface JsonViewerProps {
  data: Record<string, unknown>;
  title?: string;
}

export const JsonViewer = ({ data, title }: JsonViewerProps) => {
  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'string') return `"${value}"`;
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  return (
    <div
      style={{
        background: 'var(--color-gray-900)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      {title && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: 'rgba(255, 255, 255, 0.05)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2">
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--color-gray-400)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {title}
          </span>
        </div>
      )}
      <pre
        style={{
          margin: 0,
          padding: '1rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8125rem',
          lineHeight: 1.6,
          color: '#e5e7eb',
          overflowX: 'auto',
          maxHeight: '300px',
        }}
      >
        <code>
          {'{'}
          {'\n'}
          {Object.entries(data).map(([key, value], index, arr) => (
            <span key={key}>
              {'  '}
              <span style={{ color: '#93c5fd' }}>"{key}"</span>
              <span style={{ color: '#9ca3af' }}>: </span>
              <span
                style={{
                  color:
                    typeof value === 'string'
                      ? '#86efac'
                      : typeof value === 'number'
                      ? '#fcd34d'
                      : typeof value === 'boolean'
                      ? '#f9a8d4'
                      : '#9ca3af',
                }}
              >
                {formatValue(value)}
              </span>
              {index < arr.length - 1 && <span style={{ color: '#9ca3af' }}>,</span>}
              {'\n'}
            </span>
          ))}
          {'}'}
        </code>
      </pre>
    </div>
  );
};

