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
        padding: '2rem',
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
        padding: '2rem',
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{
            color: 'var(--color-error)',
            marginBottom: '1rem',
            fontSize: '0.9375rem',
          }}>
            {error}
          </p>
          <button
            onClick={onRetry}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'var(--color-primary)',
              background: 'var(--color-primary-light)',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}>
        <EmptyState
          title={
            activeTab === 'attention'
              ? 'No leads need attention'
              : activeTab === 'sequence'
              ? 'No leads in sequence'
              : 'No leads found'
          }
          description={
            activeTab === 'attention'
              ? 'Great job! All your leads are up to date.'
              : activeTab === 'sequence'
              ? 'Enroll leads in a sequence to see them here.'
              : 'Try adjusting your filters or search query.'
          }
        />
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
    }}>
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

