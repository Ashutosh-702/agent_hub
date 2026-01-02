import { useState, useEffect } from 'react';
import { TimelineEventCard } from './TimelineEventCard';
import { Loader } from '../shared/Loader';
import { Modal, Button, ToastProvider, useToast } from '../hubspot/ui';
import type { LeadDetail as LeadDetailType, Temperature, LeadStatus } from '../../types/inbox';
import { TEMPERATURE_LABELS, LEAD_STATUS_LABELS, CHANNEL_LABELS } from '../../types/inbox';
import * as inboxApi from '../../services/inboxApi';

interface LeadDetailProps {
  leadId: string;
  onBack?: () => void;
  onUpdate?: () => void;
  isMobile?: boolean;
}

// Wrapper to provide Toast context
export const LeadDetail = (props: LeadDetailProps) => {
  return (
    <ToastProvider>
      <LeadDetailContent {...props} />
    </ToastProvider>
  );
};

// Collapsible Section Component
const CollapsibleSection = ({ 
  title, 
  defaultOpen = true, 
  children,
  badge
}: { 
  title: string; 
  defaultOpen?: boolean; 
  children: React.ReactNode;
  badge?: React.ReactNode;
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div style={{
      background: 'var(--color-white)',
      borderRadius: '12px',
      border: '1px solid var(--color-gray-200)',
      overflow: 'hidden',
      marginBottom: '1rem',
    }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--color-gray-50)',
          border: 'none',
          cursor: 'pointer',
          borderBottom: isOpen ? '1px solid var(--color-gray-200)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            style={{
              transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
              color: 'var(--color-gray-500)',
            }}
          >
            <polyline points="9 18 15 12 9 6"/>
          </svg>
          <span style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--color-gray-700)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}>
            {title}
          </span>
        </div>
        {badge}
      </button>
      {isOpen && (
        <div style={{ padding: '1.25rem' }}>
          {children}
        </div>
      )}
    </div>
  );
};

const LeadDetailContent = ({ leadId, onBack, onUpdate, isMobile }: LeadDetailProps) => {
  const { showToast } = useToast();
  const [detail, setDetail] = useState<LeadDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch lead detail
  useEffect(() => {
    const fetchDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await inboxApi.getLeadDetail(leadId);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lead');
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetail();
  }, [leadId]);

  // Handle temperature change
  const handleTemperatureChange = async (temp: Temperature) => {
    if (!detail) return;
    try {
      await inboxApi.updateLead(leadId, { temperature: temp });
      setDetail(prev => prev ? {
        ...prev,
        summary: { ...prev.summary, temperature: temp }
      } : null);
      showToast(`Temperature updated to ${TEMPERATURE_LABELS[temp]}`, 'success');
      onUpdate?.();
    } catch (err) {
      showToast('Failed to update temperature', 'error');
    }
  };

  // Handle status change
  const handleStatusChange = async (status: LeadStatus) => {
    if (!detail) return;
    try {
      await inboxApi.updateLead(leadId, { status });
      setDetail(prev => prev ? {
        ...prev,
        summary: { ...prev.summary, status }
      } : null);
      showToast(`Status updated to ${LEAD_STATUS_LABELS[status]}`, 'success');
      onUpdate?.();
    } catch (err) {
      showToast('Failed to update status', 'error');
    }
  };

  // Handle mark as read
  const handleMarkRead = async () => {
    if (!detail || detail.summary.unreadCount === 0) return;
    try {
      await inboxApi.markLeadRead(leadId);
      setDetail(prev => prev ? {
        ...prev,
        summary: { ...prev.summary, unreadCount: 0 }
      } : null);
      showToast('Marked as read', 'success');
      onUpdate?.();
    } catch (err) {
      showToast('Failed to mark as read', 'error');
    }
  };

  // Handle pause/resume sequence
  const handleSequenceToggle = async () => {
    if (!detail || !detail.summary.inSequence) return;
    const currentStatus = detail.summary.sequence?.stageStatus;
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    try {
      await inboxApi.updateSequence(leadId, { stageStatus: newStatus });
      setDetail(prev => prev ? {
        ...prev,
        summary: {
          ...prev.summary,
          sequence: prev.summary.sequence ? {
            ...prev.summary.sequence,
            stageStatus: newStatus as 'active' | 'paused' | 'completed' | 'exited'
          } : undefined
        }
      } : null);
      showToast(`Sequence ${newStatus === 'paused' ? 'paused' : 'resumed'}`, 'success');
      onUpdate?.();
    } catch (err) {
      showToast('Failed to update sequence', 'error');
    }
  };

  // Handle add note
  const handleAddNote = async () => {
    if (!noteText.trim()) return;
    setIsSubmitting(true);
    try {
      await inboxApi.addNote(leadId, noteText.trim());
      setNoteText('');
      setShowNoteModal(false);
      const data = await inboxApi.getLeadDetail(leadId);
      setDetail(data);
      showToast('Note added', 'success');
    } catch (err) {
      showToast('Failed to add note', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-gray-50)',
      }}>
        <Loader text="Loading lead details..." />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-gray-50)',
        padding: '2rem',
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--color-error)', marginBottom: '1rem' }}>
            {error || 'Lead not found'}
          </p>
        </div>
      </div>
    );
  }

  const { summary, events, notes } = detail;

  const selectStyle: React.CSSProperties = {
    padding: '0.625rem 2.5rem 0.625rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    border: '1px solid var(--color-gray-200)',
    borderRadius: '8px',
    background: 'var(--color-white)',
    cursor: 'pointer',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 0.75rem center',
    minWidth: '140px',
  };

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--color-gray-50)',
      overflow: 'hidden',
    }}>
      {/* Header with back button (mobile) */}
      {isMobile && onBack && (
        <div style={{
          padding: '1rem 1.25rem',
          background: 'var(--color-white)',
          borderBottom: '1px solid var(--color-gray-200)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          <button
            onClick={onBack}
            style={{
              padding: '0.5rem',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-gray-600)',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
          </button>
          <span style={{ fontWeight: 600, fontSize: '1rem' }}>Back to list</span>
        </div>
      )}

      {/* Scrollable Content */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1.5rem',
      }}>
        {/* Lead Header - Always Visible */}
        <div style={{
          background: 'var(--color-white)',
          borderRadius: '12px',
          border: '1px solid var(--color-gray-200)',
          padding: '1.5rem',
          marginBottom: '1rem',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '1.25rem',
          }}>
            <div>
              <h2 style={{
                fontSize: '1.375rem',
                fontWeight: 700,
                color: 'var(--color-gray-900)',
                marginBottom: '0.375rem',
              }}>
                {summary.company.name}
              </h2>
              <p style={{
                fontSize: '1rem',
                color: 'var(--color-gray-600)',
                marginBottom: '0.25rem',
              }}>
                {summary.contact.name}
                {summary.contact.title && (
                  <span style={{ color: 'var(--color-gray-400)' }}> · {summary.contact.title}</span>
                )}
              </p>
              {summary.contact.email && (
                <p style={{
                  fontSize: '0.875rem',
                  color: 'var(--color-gray-500)',
                }}>
                  {summary.contact.email}
                </p>
              )}
            </div>
            {summary.unreadCount > 0 && (
              <span style={{
                padding: '0.25rem 0.75rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                background: 'var(--color-primary)',
                color: 'white',
                borderRadius: '12px',
              }}>
                {summary.unreadCount} unread
              </span>
            )}
          </div>

          {/* Quick Actions */}
          <div style={{
            display: 'flex',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}>
            {summary.unreadCount > 0 && (
              <button
                onClick={handleMarkRead}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: 'var(--color-primary)',
                  color: 'white',
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
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Mark as Read
              </button>
            )}
            <button
              onClick={() => setShowNoteModal(true)}
              style={{
                padding: '0.625rem 1.25rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                background: 'var(--color-gray-100)',
                color: 'var(--color-gray-700)',
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
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Add Note
            </button>
            <button
              style={{
                padding: '0.625rem 1.25rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                background: 'var(--color-gray-100)',
                color: 'var(--color-gray-700)',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Open in HubSpot
            </button>
          </div>
        </div>

        {/* Lead Properties - Collapsible */}
        <CollapsibleSection title="Lead Properties" defaultOpen={true}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '1.25rem',
          }}>
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--color-gray-500)',
                marginBottom: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Temperature
              </label>
              <select
                value={summary.temperature}
                onChange={(e) => handleTemperatureChange(e.target.value as Temperature)}
                style={selectStyle}
              >
                <option value="cold">🥶 Cold</option>
                <option value="warm">🌡️ Warm</option>
                <option value="hot">🔥 Hot</option>
              </select>
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--color-gray-500)',
                marginBottom: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Status
              </label>
              <select
                value={summary.status}
                onChange={(e) => handleStatusChange(e.target.value as LeadStatus)}
                style={selectStyle}
              >
                {Object.entries(LEAD_STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--color-gray-500)',
                marginBottom: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Owner
              </label>
              <p style={{
                fontSize: '0.9375rem',
                fontWeight: 500,
                color: 'var(--color-gray-800)',
                padding: '0.625rem 0',
              }}>
                {summary.owner.name}
              </p>
            </div>
          </div>
        </CollapsibleSection>

        {/* Sequence Panel - Collapsible (if in sequence) */}
        {summary.inSequence && summary.sequence && (
          <CollapsibleSection 
            title="Sequence" 
            defaultOpen={true}
            badge={
              <span style={{
                padding: '0.25rem 0.75rem',
                fontSize: '0.6875rem',
                fontWeight: 600,
                background: summary.sequence.stageStatus === 'active' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: summary.sequence.stageStatus === 'active' ? '#059669' : '#d97706',
                borderRadius: '6px',
                textTransform: 'capitalize',
              }}>
                {summary.sequence.stageStatus}
              </span>
            }
          >
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              <div>
                <h4 style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'var(--color-gray-800)',
                  marginBottom: '0.375rem',
                }}>
                  {summary.sequence.outreachCampaignName}
                </h4>
                <p style={{
                  fontSize: '0.9375rem',
                  color: 'var(--color-gray-600)',
                }}>
                  Step {summary.sequence.currentStage.stepNumber}: {summary.sequence.currentStage.stepName}
                  <span style={{ color: 'var(--color-gray-400)' }}>
                    {' '}({CHANNEL_LABELS[summary.sequence.currentStage.channel]})
                  </span>
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={handleSequenceToggle}
                  style={{
                    padding: '0.625rem 1.25rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    background: summary.sequence.stageStatus === 'active' ? 'var(--color-warning)' : 'var(--color-success)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {summary.sequence.stageStatus === 'active' ? 'Pause Sequence' : 'Resume Sequence'}
                </button>
                <button
                  style={{
                    padding: '0.625rem 1.25rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    background: 'var(--color-gray-100)',
                    color: 'var(--color-gray-700)',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  View Campaign
                </button>
              </div>
            </div>
          </CollapsibleSection>
        )}

        {/* Notes - Collapsible */}
        {notes.length > 0 && (
          <CollapsibleSection 
            title="Notes" 
            defaultOpen={false}
            badge={
              <span style={{
                padding: '0.125rem 0.5rem',
                fontSize: '0.6875rem',
                fontWeight: 600,
                background: 'var(--color-gray-200)',
                color: 'var(--color-gray-600)',
                borderRadius: '10px',
              }}>
                {notes.length}
              </span>
            }
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {notes.map(note => (
                <div
                  key={note.id}
                  style={{
                    padding: '1rem 1.25rem',
                    background: 'rgba(245, 158, 11, 0.06)',
                    borderLeft: '3px solid var(--color-warning)',
                    borderRadius: '0 8px 8px 0',
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '0.5rem',
                  }}>
                    <span style={{
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      color: 'var(--color-gray-700)',
                    }}>
                      {note.author}
                    </span>
                    <span style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-gray-400)',
                    }}>
                      {new Date(note.at).toLocaleDateString()}
                    </span>
                  </div>
                  <p style={{
                    fontSize: '0.9375rem',
                    color: 'var(--color-gray-600)',
                    margin: 0,
                    lineHeight: 1.6,
                  }}>
                    {note.text}
                  </p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Activity Timeline - Always Open */}
        <div style={{
          background: 'var(--color-white)',
          borderRadius: '12px',
          border: '1px solid var(--color-gray-200)',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '1rem 1.25rem',
            background: 'var(--color-gray-50)',
            borderBottom: '1px solid var(--color-gray-200)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--color-gray-700)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Activity Timeline
            </span>
            <span style={{
              padding: '0.125rem 0.5rem',
              fontSize: '0.6875rem',
              fontWeight: 600,
              background: 'var(--color-gray-200)',
              color: 'var(--color-gray-600)',
              borderRadius: '10px',
            }}>
              {events.length} events
            </span>
          </div>
          <div style={{ padding: '1.5rem' }}>
            {events.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem 2rem',
                color: 'var(--color-gray-400)',
              }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.5, marginBottom: '1rem' }}>
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                <p style={{ fontSize: '0.9375rem' }}>No activity yet</p>
              </div>
            ) : (
              <div>
                {events.map((event, index) => (
                  <TimelineEventCard 
                    key={event.id} 
                    event={event} 
                    isLast={index === events.length - 1}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Note Modal */}
      <Modal
        isOpen={showNoteModal}
        onClose={() => setShowNoteModal(false)}
        title="Add Note"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowNoteModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddNote}
              isLoading={isSubmitting}
              disabled={!noteText.trim()}
            >
              Add Note
            </Button>
          </>
        }
      >
        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          placeholder="Write a note about this lead..."
          style={{
            width: '100%',
            minHeight: '150px',
            padding: '1rem',
            fontSize: '0.9375rem',
            border: '1px solid var(--color-gray-200)',
            borderRadius: '8px',
            resize: 'vertical',
            fontFamily: 'inherit',
            lineHeight: 1.6,
          }}
          autoFocus
        />
      </Modal>
    </div>
  );
};
