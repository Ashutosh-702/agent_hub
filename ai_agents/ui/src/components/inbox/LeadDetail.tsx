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
            stageStatus: newStatus as any
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
      // Refresh detail to get new note
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
        background: 'var(--color-white)',
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
        background: 'var(--color-white)',
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

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--color-white)',
      overflow: 'hidden',
    }}>
      {/* Header with back button (mobile) */}
      {isMobile && onBack && (
        <div style={{
          padding: '1rem',
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
          <span style={{ fontWeight: 600 }}>Back to list</span>
        </div>
      )}

      {/* Summary Card */}
      <div style={{
        padding: '1.5rem',
        borderBottom: '1px solid var(--color-gray-200)',
      }}>
        {/* Company & Contact */}
        <div style={{ marginBottom: '1rem' }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: 'var(--color-gray-900)',
            marginBottom: '0.25rem',
          }}>
            {summary.company.name}
          </h2>
          <p style={{
            fontSize: '0.9375rem',
            color: 'var(--color-gray-600)',
          }}>
            {summary.contact.name}
            {summary.contact.title && ` · ${summary.contact.title}`}
          </p>
          {summary.contact.email && (
            <p style={{
              fontSize: '0.8125rem',
              color: 'var(--color-gray-500)',
              marginTop: '0.25rem',
            }}>
              {summary.contact.email}
            </p>
          )}
        </div>

        {/* Temperature & Status Dropdowns */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1rem',
          flexWrap: 'wrap',
        }}>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--color-gray-500)',
              marginBottom: '0.375rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Temperature
            </label>
            <select
              value={summary.temperature}
              onChange={(e) => handleTemperatureChange(e.target.value as Temperature)}
              style={{
                padding: '0.5rem 2rem 0.5rem 0.75rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                border: '1px solid var(--color-gray-200)',
                borderRadius: '6px',
                background: 'var(--color-white)',
                cursor: 'pointer',
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 0.5rem center',
              }}
            >
              <option value="cold">Cold</option>
              <option value="warm">Warm</option>
              <option value="hot">Hot</option>
            </select>
          </div>

          <div>
            <label style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--color-gray-500)',
              marginBottom: '0.375rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Status
            </label>
            <select
              value={summary.status}
              onChange={(e) => handleStatusChange(e.target.value as LeadStatus)}
              style={{
                padding: '0.5rem 2rem 0.5rem 0.75rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                border: '1px solid var(--color-gray-200)',
                borderRadius: '6px',
                background: 'var(--color-white)',
                cursor: 'pointer',
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 0.5rem center',
              }}
            >
              {Object.entries(LEAD_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Sequence Panel */}
        {summary.inSequence && summary.sequence && (
          <div style={{
            padding: '0.75rem 1rem',
            background: 'var(--color-primary-lighter)',
            borderRadius: '8px',
            marginBottom: '1rem',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}>
              <span style={{
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-gray-800)',
              }}>
                {summary.sequence.outreachCampaignName}
              </span>
              <span style={{
                padding: '0.125rem 0.5rem',
                fontSize: '0.6875rem',
                fontWeight: 600,
                background: summary.sequence.stageStatus === 'active' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: summary.sequence.stageStatus === 'active' ? '#059669' : '#d97706',
                borderRadius: '4px',
                textTransform: 'capitalize',
              }}>
                {summary.sequence.stageStatus}
              </span>
            </div>
            <p style={{
              fontSize: '0.8125rem',
              color: 'var(--color-gray-600)',
              marginBottom: '0.75rem',
            }}>
              Step {summary.sequence.currentStage.stepNumber}: {summary.sequence.currentStage.stepName}
              ({CHANNEL_LABELS[summary.sequence.currentStage.channel]})
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleSequenceToggle}
                style={{
                  padding: '0.375rem 0.75rem',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  background: summary.sequence.stageStatus === 'active' ? 'var(--color-warning)' : 'var(--color-success)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                {summary.sequence.stageStatus === 'active' ? 'Pause' : 'Resume'}
              </button>
              <button
                style={{
                  padding: '0.375rem 0.75rem',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  background: 'var(--color-gray-100)',
                  color: 'var(--color-gray-700)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                View Campaign
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          flexWrap: 'wrap',
        }}>
          {summary.unreadCount > 0 && (
            <button
              onClick={handleMarkRead}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                background: 'var(--color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Mark as Read
            </button>
          )}
          <button
            onClick={() => setShowNoteModal(true)}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              background: 'var(--color-gray-100)',
              color: 'var(--color-gray-700)',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Add Note
          </button>
          <button
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              background: 'var(--color-gray-100)',
              color: 'var(--color-gray-700)',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            Open in HubSpot
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem 1.5rem',
        background: 'var(--color-gray-50)',
      }}>
        <h3 style={{
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: 'var(--color-gray-500)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '1rem',
        }}>
          Activity Timeline
        </h3>

        {/* Notes */}
        {notes.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            {notes.map(note => (
              <div
                key={note.id}
                style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(245, 158, 11, 0.08)',
                  borderLeft: '3px solid var(--color-warning)',
                  borderRadius: '0 6px 6px 0',
                  marginBottom: '0.75rem',
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '0.25rem',
                }}>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color: 'var(--color-gray-700)',
                  }}>
                    {note.author}
                  </span>
                  <span style={{
                    fontSize: '0.6875rem',
                    color: 'var(--color-gray-400)',
                  }}>
                    {new Date(note.at).toLocaleDateString()}
                  </span>
                </div>
                <p style={{
                  fontSize: '0.8125rem',
                  color: 'var(--color-gray-600)',
                  margin: 0,
                }}>
                  {note.text}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Events */}
        {events.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            color: 'var(--color-gray-400)',
          }}>
            No activity yet
          </div>
        ) : (
          <div>
            {events.map(event => (
              <TimelineEventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>

      {/* Add Note Modal */}
      <Modal
        isOpen={showNoteModal}
        onClose={() => setShowNoteModal(false)}
        title="Add Note"
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
            minHeight: '120px',
            padding: '0.75rem',
            fontSize: '0.9375rem',
            border: '1px solid var(--color-gray-200)',
            borderRadius: '8px',
            resize: 'vertical',
            fontFamily: 'inherit',
          }}
          autoFocus
        />
      </Modal>
    </div>
  );
};

