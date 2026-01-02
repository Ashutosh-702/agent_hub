import React, { useState } from 'react';
import type { EngagementEvent, Channel } from '../../types/inbox';
import { CHANNEL_LABELS } from '../../types/inbox';

interface TimelineEventCardProps {
  event: EngagementEvent;
  isLast?: boolean;
}

// Channel icons
const ChannelIcon = ({ channel, size = 16 }: { channel: Channel; size?: number }) => {
  const icons: Record<Channel, React.ReactElement> = {
    email: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>
    ),
    linkedin: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
        <rect x="2" y="9" width="4" height="12"/>
        <circle cx="4" cy="4" r="2"/>
      </svg>
    ),
    whatsapp: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
      </svg>
    ),
    call: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
      </svg>
    ),
  };
  return icons[channel];
};

// Direction icons
const DirectionIcon = ({ direction, size = 14 }: { direction: 'inbound' | 'outbound'; size?: number }) => {
  if (direction === 'inbound') {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="19" y1="12" x2="5" y2="12"/>
        <polyline points="12 19 5 12 12 5"/>
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="5" y1="12" x2="19" y2="12"/>
      <polyline points="12 5 19 12 12 19"/>
    </svg>
  );
};

// Format time
function formatEventTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  
  if (isToday) {
    return 'Today at ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) +
    ' at ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Format duration
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

export const TimelineEventCard = ({ event, isLast = false }: TimelineEventCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const isInbound = event.direction === 'inbound';
  
  // Channel colors
  const channelColors: Record<Channel, string> = {
    email: '#3b82f6',
    linkedin: '#0077b5',
    whatsapp: '#25d366',
    call: '#8b5cf6',
  };
  
  const channelColor = channelColors[event.channel];

  return (
    <div style={{
      display: 'flex',
      gap: '1rem',
      marginBottom: isLast ? 0 : '1.5rem',
    }}>
      {/* Timeline marker */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '0.25rem',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: `${channelColor}12`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: channelColor,
          flexShrink: 0,
        }}>
          <ChannelIcon channel={event.channel} size={18} />
        </div>
        {!isLast && (
          <div style={{
            flex: 1,
            width: '2px',
            background: 'var(--color-gray-200)',
            marginTop: '0.75rem',
            minHeight: '24px',
          }} />
        )}
      </div>

      {/* Event content */}
      <div style={{
        flex: 1,
        background: 'var(--color-gray-50)',
        borderRadius: '12px',
        border: '1px solid var(--color-gray-200)',
        overflow: 'hidden',
        minWidth: 0,
      }}>
        {/* Header */}
        <div style={{
          padding: '1rem 1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '1rem',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.25rem 0.625rem',
              background: isInbound ? 'rgba(16, 185, 129, 0.1)' : 'rgba(107, 114, 128, 0.1)',
              color: isInbound ? '#059669' : '#6b7280',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 600,
            }}>
              <DirectionIcon direction={event.direction} size={12} />
              {isInbound ? 'Received' : 'Sent'}
            </span>
            <span style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: 'var(--color-gray-800)',
            }}>
              {event.title || `${CHANNEL_LABELS[event.channel]} ${isInbound ? 'received' : 'sent'}`}
            </span>
            {event.meta?.sequence && (
              <span style={{
                padding: '0.25rem 0.625rem',
                fontSize: '0.6875rem',
                fontWeight: 600,
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                borderRadius: '6px',
              }}>
                Sequence Step
              </span>
            )}
          </div>
          <span style={{
            fontSize: '0.8125rem',
            color: 'var(--color-gray-400)',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}>
            {formatEventTime(event.at)}
          </span>
        </div>

        {/* Meta line (subject, status, duration) */}
        {(event.meta?.subject || event.meta?.messageStatus || event.meta?.callDurationSec) && (
          <div style={{
            padding: '0.75rem 1.25rem',
            background: 'var(--color-white)',
            borderTop: '1px solid var(--color-gray-100)',
            borderBottom: '1px solid var(--color-gray-100)',
            fontSize: '0.8125rem',
            color: 'var(--color-gray-600)',
            display: 'flex',
            gap: '1.5rem',
            flexWrap: 'wrap',
          }}>
            {event.meta?.subject && (
              <span>
                <strong style={{ color: 'var(--color-gray-500)', fontWeight: 500 }}>Subject:</strong>{' '}
                {event.meta.subject}
              </span>
            )}
            {event.meta?.messageStatus && (
              <span style={{ textTransform: 'capitalize' }}>
                <strong style={{ color: 'var(--color-gray-500)', fontWeight: 500 }}>Status:</strong>{' '}
                {event.meta.messageStatus}
              </span>
            )}
            {event.meta?.callDurationSec && (
              <span>
                <strong style={{ color: 'var(--color-gray-500)', fontWeight: 500 }}>Duration:</strong>{' '}
                {formatDuration(event.meta.callDurationSec)}
              </span>
            )}
          </div>
        )}

        {/* Content */}
        <div style={{
          padding: '1rem 1.25rem',
          background: 'var(--color-white)',
        }}>
          <p style={{
            fontSize: '0.9375rem',
            color: 'var(--color-gray-700)',
            margin: 0,
            lineHeight: 1.7,
            whiteSpace: 'pre-wrap',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: isExpanded ? 'unset' : 4,
            WebkitBoxOrient: 'vertical',
          }}>
            {event.content}
          </p>
          {event.content.length > 250 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              style={{
                marginTop: '0.75rem',
                padding: '0.375rem 0',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-primary)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}
            >
              {isExpanded ? (
                <>
                  Show less
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"/>
                  </svg>
                </>
              ) : (
                <>
                  Show more
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </>
              )}
            </button>
          )}
        </div>

        {/* External link */}
        {event.meta?.externalLink && (
          <div style={{
            padding: '0.75rem 1.25rem',
            borderTop: '1px solid var(--color-gray-100)',
            background: 'var(--color-white)',
          }}>
            <a
              href={event.meta.externalLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-primary)',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}
            >
              Open in {CHANNEL_LABELS[event.channel]}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
          </div>
        )}
      </div>
    </div>
  );
};
