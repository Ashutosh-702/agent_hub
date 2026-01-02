import { LeadRow } from './LeadRow';
import { Loader } from '../shared/Loader';
import { EmptyState } from '../shared/EmptyState';
import type { LeadSummary } from '../../types/inbox';

interface LeadListProps {
  leads: LeadSummary[];
  selectedLeadId: string | null;
  onSelectLead: (lead: LeadSummary) => void;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  activeTab: 'all' | 'attention' | 'sequence';
}

export const LeadList = ({
  leads,
  selectedLeadId,
  onSelectLead,
  isLoading,
  error,
  onRetry,
  activeTab,
}: LeadListProps) => {
  if (isLoading) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem',
      }}>
        <Loader text="Loading leads..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '64px',
            height: '64px',
            margin: '0 auto 1.25rem',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <p style={{
            color: 'var(--color-error)',
            marginBottom: '0.5rem',
            fontSize: '1rem',
            fontWeight: 600,
          }}>
            Failed to load leads
          </p>
          <p style={{
            color: 'var(--color-gray-500)',
            marginBottom: '1.25rem',
            fontSize: '0.9375rem',
          }}>
            {error}
          </p>
          <button
            onClick={onRetry}
            style={{
              padding: '0.75rem 1.5rem',
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: 'white',
              background: 'var(--color-primary)',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (leads.length === 0) {
    const emptyContent = {
      attention: {
        icon: (
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        ),
        title: 'All caught up!',
        description: 'No leads need your attention right now. Great work!',
        color: '#10b981',
      },
      sequence: {
        icon: (
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        ),
        title: 'No leads in sequence',
        description: 'Start an outreach campaign to enroll leads.',
        color: '#6366f1',
      },
      all: {
        icon: (
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
            <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
          </svg>
        ),
        title: 'No leads found',
        description: 'Try adjusting your filters or search query.',
        color: '#6b7280',
      },
    };

    const content = emptyContent[activeTab];

    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '80px',
            height: '80px',
            margin: '0 auto 1.5rem',
            borderRadius: '50%',
            background: `${content.color}12`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: content.color,
          }}>
            {content.icon}
          </div>
          <p style={{
            fontSize: '1.125rem',
            fontWeight: 600,
            color: 'var(--color-gray-700)',
            marginBottom: '0.5rem',
          }}>
            {content.title}
          </p>
          <p style={{
            fontSize: '0.9375rem',
            color: 'var(--color-gray-500)',
            maxWidth: '280px',
            lineHeight: 1.5,
          }}>
            {content.description}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      overflowX: 'hidden',
    }}>
      {/* List header */}
      <div style={{
        padding: '0.75rem 1.5rem',
        fontSize: '0.75rem',
        fontWeight: 600,
        color: 'var(--color-gray-400)',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        background: 'var(--color-gray-50)',
        borderBottom: '1px solid var(--color-gray-100)',
      }}>
        {leads.length} lead{leads.length !== 1 ? 's' : ''}
      </div>
      
      {leads.map(lead => (
        <LeadRow
          key={lead.leadId}
          lead={lead}
          isSelected={lead.leadId === selectedLeadId}
          onClick={() => onSelectLead(lead)}
          showAttentionReasons={activeTab === 'attention'}
        />
      ))}
    </div>
  );
};
