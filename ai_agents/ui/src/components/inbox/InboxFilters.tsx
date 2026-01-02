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
    padding: '0.625rem 2.25rem 0.625rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 500,
    border: '1px solid var(--color-gray-200)',
    borderRadius: '8px',
    background: 'var(--color-white)',
    cursor: 'pointer',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 0.75rem center',
    minWidth: '140px',
    color: 'var(--color-gray-700)',
  };

  const hasActiveFilters = filters.query || filters.channel || filters.temperature ||
    filters.status || filters.inSequence !== 'any' || filters.stageStatus || filters.ownerEmail;

  const activeFilterCount = [
    filters.channel,
    filters.temperature,
    filters.status,
    filters.inSequence !== 'any' ? filters.inSequence : undefined,
    filters.stageStatus,
    filters.ownerEmail,
  ].filter(Boolean).length;

  return (
    <div style={{
      padding: '1rem 1.5rem',
      background: 'var(--color-white)',
      borderBottom: '1px solid var(--color-gray-200)',
      flexShrink: 0,
    }}>
      {/* Search + Filter toggle row */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        marginBottom: showFilters ? '1rem' : 0,
      }}>
        {/* Search */}
        <div style={{
          flex: 1,
          maxWidth: '400px',
          position: 'relative',
        }}>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{
              position: 'absolute',
              left: '0.875rem',
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
              padding: '0.75rem 1rem 0.75rem 2.75rem',
              fontSize: '0.9375rem',
              border: '1px solid var(--color-gray-200)',
              borderRadius: '8px',
              outline: 'none',
              transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--color-primary)';
              e.target.style.boxShadow = '0 0 0 3px var(--color-primary-lighter)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--color-gray-200)';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            padding: '0.75rem 1rem',
            fontSize: '0.9375rem',
            fontWeight: 600,
            background: showFilters || hasActiveFilters ? 'var(--color-primary-light)' : 'var(--color-gray-100)',
            color: showFilters || hasActiveFilters ? 'var(--color-primary)' : 'var(--color-gray-600)',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          Filters
          {activeFilterCount > 0 && (
            <span style={{
              padding: '0.125rem 0.5rem',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: 'var(--color-primary)',
              color: 'white',
              borderRadius: '10px',
            }}>
              {activeFilterCount}
            </span>
          )}
        </button>

        {/* Sort */}
        <select
          value={filters.sort || 'recent'}
          onChange={(e) => onChange({ sort: e.target.value as 'recent' | 'attention' | 'hot' })}
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
          padding: '1rem',
          background: 'var(--color-gray-50)',
          borderRadius: '8px',
          border: '1px solid var(--color-gray-100)',
        }}>
          {/* Channel */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-gray-400)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.375rem',
            }}>
              Channel
            </label>
            <select
              value={filters.channel || ''}
              onChange={(e) => onChange({ channel: e.target.value as Channel || undefined })}
              style={selectStyle}
            >
              <option value="">Any</option>
              {Object.entries(CHANNEL_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {/* Temperature */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-gray-400)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.375rem',
            }}>
              Temperature
            </label>
            <select
              value={filters.temperature || ''}
              onChange={(e) => onChange({ temperature: e.target.value as Temperature || undefined })}
              style={selectStyle}
            >
              <option value="">Any</option>
              {Object.entries(TEMPERATURE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-gray-400)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.375rem',
            }}>
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => onChange({ status: e.target.value as LeadStatus || undefined })}
              style={selectStyle}
            >
              <option value="">Any</option>
              {Object.entries(LEAD_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {/* Sequence */}
          {activeTab !== 'sequence' && (
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.6875rem',
                fontWeight: 600,
                color: 'var(--color-gray-400)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '0.375rem',
              }}>
                Sequence
              </label>
              <select
                value={filters.inSequence || 'any'}
                onChange={(e) => onChange({ inSequence: e.target.value as 'any' | 'yes' | 'no' })}
                style={selectStyle}
              >
                <option value="any">Any</option>
                <option value="yes">In Sequence</option>
                <option value="no">Not in Sequence</option>
              </select>
            </div>
          )}

          {/* Stage Status (only when in sequence tab or sequence filter is "yes") */}
          {(activeTab === 'sequence' || filters.inSequence === 'yes') && (
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.6875rem',
                fontWeight: 600,
                color: 'var(--color-gray-400)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '0.375rem',
              }}>
                Stage
              </label>
              <select
                value={filters.stageStatus || ''}
                onChange={(e) => onChange({ stageStatus: e.target.value as StageStatus || undefined })}
                style={selectStyle}
              >
                <option value="">Any</option>
                {Object.entries(STAGE_STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Owner */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-gray-400)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.375rem',
            }}>
              Owner
            </label>
            <select
              value={filters.ownerEmail || ''}
              onChange={(e) => onChange({ ownerEmail: e.target.value || undefined })}
              style={selectStyle}
            >
              <option value="">Any</option>
              {MOCK_OWNERS.map(owner => (
                <option key={owner.email} value={owner.email}>{owner.name}</option>
              ))}
            </select>
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <div style={{ marginLeft: 'auto', paddingTop: '1.25rem' }}>
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
                  padding: '0.625rem 1rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: 'var(--color-error)',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                Clear all
              </button>
            </div>
          )}
        </div>
      )}

      {/* Quick filter chips for Needs Attention tab */}
      {activeTab === 'attention' && (
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginTop: '1rem',
          flexWrap: 'wrap',
        }}>
          {[
            { label: 'Unread', icon: '📬' },
            { label: 'Overdue', icon: '⏰' },
            { label: 'Waiting on us', icon: '⚡' },
            { label: 'Hot stale', icon: '🔥' },
          ].map(chip => (
            <button
              key={chip.label}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                background: 'var(--color-gray-100)',
                color: 'var(--color-gray-600)',
                border: 'none',
                borderRadius: '20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                transition: 'all 0.15s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'var(--color-primary-light)';
                e.currentTarget.style.color = 'var(--color-primary)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'var(--color-gray-100)';
                e.currentTarget.style.color = 'var(--color-gray-600)';
              }}
            >
              <span>{chip.icon}</span>
              {chip.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
