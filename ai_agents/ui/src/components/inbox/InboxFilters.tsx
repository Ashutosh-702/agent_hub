import { useState } from 'react';
import type { ListLeadsParams, Channel, Temperature, LeadStatus, StageStatus } from '../../types/inbox';
import { CHANNEL_LABELS, TEMPERATURE_LABELS, LEAD_STATUS_LABELS, STAGE_STATUS_LABELS } from '../../types/inbox';
import { MOCK_OWNERS } from '../../services/inboxApi';

interface InboxFiltersProps {
  filters: ListLeadsParams;
  onChange: (filters: Partial<ListLeadsParams>) => void;
  activeTab: 'all' | 'attention' | 'sequence';
}

export const InboxFilters = ({ filters, onChange, activeTab }: InboxFiltersProps) => {
  const [showFilters, setShowFilters] = useState(false);

  const selectStyle: React.CSSProperties = {
    padding: '0.5rem 2rem 0.5rem 0.75rem',
    fontSize: '0.8125rem',
    border: '1px solid var(--color-gray-200)',
    borderRadius: '6px',
    background: 'var(--color-white)',
    cursor: 'pointer',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 0.5rem center',
    minWidth: '120px',
  };

  const hasActiveFilters = filters.query || filters.channel || filters.temperature ||
    filters.status || filters.inSequence !== 'any' || filters.stageStatus || filters.ownerEmail;

  return (
    <div style={{
      padding: '0.75rem 1.5rem',
      background: 'var(--color-white)',
      borderBottom: '1px solid var(--color-gray-200)',
    }}>
      {/* Search + Filter toggle row */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'center',
        marginBottom: showFilters ? '0.75rem' : 0,
      }}>
        {/* Search */}
        <div style={{
          flex: 1,
          maxWidth: '300px',
          position: 'relative',
        }}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{
              position: 'absolute',
              left: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--color-gray-400)',
            }}
          >
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            value={filters.query || ''}
            onChange={(e) => onChange({ query: e.target.value || undefined })}
            placeholder="Search company or contact..."
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem 0.5rem 2.25rem',
              fontSize: '0.8125rem',
              border: '1px solid var(--color-gray-200)',
              borderRadius: '6px',
              outline: 'none',
            }}
          />
        </div>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            padding: '0.5rem 0.75rem',
            fontSize: '0.8125rem',
            fontWeight: 600,
            background: showFilters || hasActiveFilters ? 'var(--color-primary-light)' : 'var(--color-gray-100)',
            color: showFilters || hasActiveFilters ? 'var(--color-primary)' : 'var(--color-gray-600)',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          Filters
          {hasActiveFilters && (
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: 'var(--color-primary)',
            }} />
          )}
        </button>

        {/* Sort */}
        <select
          value={filters.sort || 'recent'}
          onChange={(e) => onChange({ sort: e.target.value as any })}
          style={selectStyle}
        >
          <option value="recent">Most Recent</option>
          <option value="attention">Needs Attention</option>
          <option value="hot">Hot First</option>
        </select>
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div style={{
          display: 'flex',
          gap: '0.75rem',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}>
          {/* Channel */}
          <select
            value={filters.channel || ''}
            onChange={(e) => onChange({ channel: e.target.value as Channel || undefined })}
            style={selectStyle}
          >
            <option value="">Any Channel</option>
            {Object.entries(CHANNEL_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          {/* Temperature */}
          <select
            value={filters.temperature || ''}
            onChange={(e) => onChange({ temperature: e.target.value as Temperature || undefined })}
            style={selectStyle}
          >
            <option value="">Any Temperature</option>
            {Object.entries(TEMPERATURE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          {/* Status */}
          <select
            value={filters.status || ''}
            onChange={(e) => onChange({ status: e.target.value as LeadStatus || undefined })}
            style={selectStyle}
          >
            <option value="">Any Status</option>
            {Object.entries(LEAD_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          {/* Sequence */}
          {activeTab !== 'sequence' && (
            <select
              value={filters.inSequence || 'any'}
              onChange={(e) => onChange({ inSequence: e.target.value as any })}
              style={selectStyle}
            >
              <option value="any">Any Sequence</option>
              <option value="yes">In Sequence</option>
              <option value="no">Not in Sequence</option>
            </select>
          )}

          {/* Stage Status (only when in sequence tab or sequence filter is "yes") */}
          {(activeTab === 'sequence' || filters.inSequence === 'yes') && (
            <select
              value={filters.stageStatus || ''}
              onChange={(e) => onChange({ stageStatus: e.target.value as StageStatus || undefined })}
              style={selectStyle}
            >
              <option value="">Any Stage</option>
              {Object.entries(STAGE_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          )}

          {/* Owner */}
          <select
            value={filters.ownerEmail || ''}
            onChange={(e) => onChange({ ownerEmail: e.target.value || undefined })}
            style={selectStyle}
          >
            <option value="">Any Owner</option>
            {MOCK_OWNERS.map(owner => (
              <option key={owner.email} value={owner.email}>{owner.name}</option>
            ))}
          </select>

          {/* Clear filters */}
          {hasActiveFilters && (
            <button
              onClick={() => onChange({
                query: undefined,
                channel: undefined,
                temperature: undefined,
                status: undefined,
                inSequence: 'any',
                stageStatus: undefined,
                ownerEmail: undefined,
              })}
              style={{
                padding: '0.5rem 0.75rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                background: 'none',
                color: 'var(--color-error)',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {/* Quick filter chips for Needs Attention tab */}
      {activeTab === 'attention' && (
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginTop: '0.75rem',
        }}>
          {['Unread', 'Overdue', 'Waiting on us', 'Hot stale'].map(chip => (
            <button
              key={chip}
              style={{
                padding: '0.375rem 0.75rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: 'var(--color-gray-100)',
                color: 'var(--color-gray-600)',
                border: 'none',
                borderRadius: '20px',
                cursor: 'pointer',
              }}
            >
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

