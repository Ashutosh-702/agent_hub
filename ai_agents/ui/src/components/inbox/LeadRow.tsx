import React from 'react';
import type { LeadSummary, Channel } from '../../types/inbox';
import { CHANNEL_LABELS, TEMPERATURE_LABELS, LEAD_STATUS_LABELS } from '../../types/inbox';

interface LeadRowProps {
  lead: LeadSummary;
  isSelected: boolean;
  onClick: () => void;
  showAttentionReasons?: boolean;
}

// Channel icons
const ChannelIcon = ({ channel, size = 14 }: { channel: Channel; size?: number }) => {
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

// Temperature badge colors
const tempColors = {
  cold: { bg: 'rgba(59, 130, 246, 0.1)', text: '#2563eb' },
  warm: { bg: 'rgba(245, 158, 11, 0.1)', text: '#d97706' },
  hot: { bg: 'rgba(239, 68, 68, 0.1)', text: '#dc2626' },
};

// Status badge colors
const statusColors: Record<string, { bg: string; text: string }> = {
  new: { bg: 'rgba(107, 114, 128, 0.1)', text: '#4b5563' },
  contacted: { bg: 'rgba(59, 130, 246, 0.1)', text: '#2563eb' },
  in_conversation: { bg: 'rgba(16, 185, 129, 0.1)', text: '#059669' },
  waiting_on_lead: { bg: 'rgba(245, 158, 11, 0.1)', text: '#d97706' },
  waiting_on_us: { bg: 'rgba(239, 68, 68, 0.1)', text: '#dc2626' },
  meeting_scheduled: { bg: 'rgba(139, 92, 246, 0.1)', text: '#7c3aed' },
  deal_open: { bg: 'rgba(16, 185, 129, 0.1)', text: '#059669' },
  closed_won: { bg: 'rgba(16, 185, 129, 0.15)', text: '#047857' },
  closed_lost: { bg: 'rgba(107, 114, 128, 0.1)', text: '#6b7280' },
  dormant: { bg: 'rgba(107, 114, 128, 0.08)', text: '#9ca3af' },
};

// Relative time formatting
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return date.toLocaleDateString();
}

export const LeadRow = ({ lead, isSelected, onClick, showAttentionReasons }: LeadRowProps) => {
  const tempStyle = tempColors[lead.temperature];
  const statusStyle = statusColors[lead.status] || statusColors.new;

  return (
    <div
      onClick={onClick}
      style={{
        padding: '1rem 1.25rem',
        borderBottom: '1px solid var(--color-gray-100)',
        cursor: 'pointer',
        background: isSelected ? 'var(--color-primary-lighter)' : 'transparent',
        borderLeft: isSelected ? '3px solid var(--color-primary)' : '3px solid transparent',
        transition: 'all 0.15s ease',
      }}
      onMouseOver={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'var(--color-gray-50)';
      }}
      onMouseOut={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'transparent';
      }}
    >
      {/* Top row: Company + Unread */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '0.375rem',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}>
            <span style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: 'var(--color-gray-900)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {lead.company.name}
            </span>
            {lead.company.domain && (
              <span style={{
                fontSize: '0.75rem',
                color: 'var(--color-gray-400)',
              }}>
                {lead.company.domain}
              </span>
            )}
          </div>
          <div style={{
            fontSize: '0.8125rem',
            color: 'var(--color-gray-600)',
            marginTop: '0.125rem',
          }}>
            {lead.contact.name}
            {lead.contact.title && (
              <span style={{ color: 'var(--color-gray-400)' }}> · {lead.contact.title}</span>
            )}
          </div>
        </div>

        {/* Unread badge */}
        {lead.unreadCount > 0 && (
          <span style={{
            padding: '0.125rem 0.5rem',
            fontSize: '0.6875rem',
            fontWeight: 700,
            background: 'var(--color-primary)',
            color: 'white',
            borderRadius: '10px',
            marginLeft: '0.5rem',
          }}>
            {lead.unreadCount}
          </span>
        )}
      </div>

      {/* Channel chips + badges */}
      <div style={{
        display: 'flex',
        gap: '0.375rem',
        flexWrap: 'wrap',
        marginBottom: '0.5rem',
      }}>
        {/* Channels */}
        <div style={{
          display: 'flex',
          gap: '0.25rem',
        }}>
          {lead.channelsPresent.map(channel => (
            <span
              key={channel}
              title={CHANNEL_LABELS[channel]}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '22px',
                height: '22px',
                background: 'var(--color-gray-100)',
                borderRadius: '4px',
                color: 'var(--color-gray-600)',
              }}
            >
              <ChannelIcon channel={channel} size={12} />
            </span>
          ))}
        </div>

        {/* Temperature badge */}
        <span
          title={lead.temperatureDrivers.join(', ')}
          style={{
            padding: '0.125rem 0.5rem',
            fontSize: '0.6875rem',
            fontWeight: 600,
            background: tempStyle.bg,
            color: tempStyle.text,
            borderRadius: '4px',
            textTransform: 'capitalize',
          }}
        >
          {TEMPERATURE_LABELS[lead.temperature]}
        </span>

        {/* Status badge */}
        <span style={{
          padding: '0.125rem 0.5rem',
          fontSize: '0.6875rem',
          fontWeight: 600,
          background: statusStyle.bg,
          color: statusStyle.text,
          borderRadius: '4px',
        }}>
          {LEAD_STATUS_LABELS[lead.status]}
        </span>
      </div>

      {/* Sequence chip */}
      {lead.inSequence && lead.sequence && (
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--color-gray-500)',
          marginBottom: '0.375rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
          <span style={{ fontWeight: 500 }}>{lead.sequence.outreachCampaignName}</span>
          <span>· Step {lead.sequence.currentStage.stepNumber}: {lead.sequence.currentStage.stepName}</span>
        </div>
      )}

      {/* Last touch */}
      {lead.lastTouch && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
          fontSize: '0.75rem',
          color: 'var(--color-gray-500)',
        }}>
          <ChannelIcon channel={lead.lastTouch.channel} size={12} />
          <span style={{
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {lead.lastTouch.snippet}
          </span>
          <span style={{
            flexShrink: 0,
            color: 'var(--color-gray-400)',
          }}>
            {formatRelativeTime(lead.lastTouch.at)}
          </span>
        </div>
      )}

      {/* Attention reasons (when in attention tab) */}
      {showAttentionReasons && lead.attentionReasons && lead.attentionReasons.length > 0 && (
        <div style={{
          marginTop: '0.5rem',
          display: 'flex',
          gap: '0.375rem',
          flexWrap: 'wrap',
        }}>
          {lead.attentionReasons.map((reason, idx) => (
            <span
              key={idx}
              style={{
                padding: '0.125rem 0.5rem',
                fontSize: '0.6875rem',
                fontWeight: 600,
                background: 'var(--color-error-light)',
                color: 'var(--color-error)',
                borderRadius: '4px',
              }}
            >
              {reason.message}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

