// Inbox Utility Functions

import type { LeadSummary, AttentionReason, Channel, Temperature, LeadStatus } from '../types/inbox';

/**
 * Format a date as relative time (e.g., "2m ago", "3h ago", "5d ago")
 */
export function formatRelativeTime(dateString: string): string {
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

/**
 * Format a date as absolute time (e.g., "Jan 5, 2024 at 3:45 PM")
 */
export function formatAbsoluteTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }) + ' at ' + date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Format call duration (e.g., "5m 30s")
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * Compute reasons why a lead needs attention
 */
export function computeNeedsAttention(lead: LeadSummary): AttentionReason[] {
  const reasons: AttentionReason[] = [];

  // Unread replies
  if (lead.unreadCount > 0) {
    reasons.push({
      type: 'unread_reply',
      message: `${lead.unreadCount} unread message${lead.unreadCount > 1 ? 's' : ''}`,
    });
  }

  // Waiting on us
  if (lead.status === 'waiting_on_us') {
    reasons.push({
      type: 'waiting_on_us',
      message: 'Lead is waiting for your response',
    });
  }

  // Overdue sequence step
  if (lead.inSequence && lead.nextStepAt) {
    const nextStep = new Date(lead.nextStepAt);
    if (nextStep < new Date()) {
      reasons.push({
        type: 'overdue_step',
        message: 'Sequence step is overdue',
      });
    }
  }

  // Hot lead gone stale
  if (lead.temperature === 'hot' && lead.lastTouch) {
    const lastTouchDate = new Date(lead.lastTouch.at);
    const daysSince = Math.floor((Date.now() - lastTouchDate.getTime()) / (1000 * 60 * 60 * 24));
    if (daysSince > 3) {
      reasons.push({
        type: 'hot_stale',
        message: `Hot lead with no activity for ${daysSince} days`,
      });
    }
  }

  return reasons;
}

/**
 * Get badge variant for temperature
 */
export function getTemperatureBadgeVariant(temp: Temperature): 'info' | 'warning' | 'error' {
  switch (temp) {
    case 'cold':
      return 'info';
    case 'warm':
      return 'warning';
    case 'hot':
      return 'error';
    default:
      return 'info';
  }
}

/**
 * Get badge variant for status
 */
export function getStatusBadgeVariant(status: LeadStatus): 'default' | 'info' | 'success' | 'warning' | 'error' {
  switch (status) {
    case 'new':
      return 'default';
    case 'contacted':
      return 'info';
    case 'in_conversation':
      return 'success';
    case 'waiting_on_lead':
      return 'warning';
    case 'waiting_on_us':
      return 'error';
    case 'meeting_scheduled':
      return 'info';
    case 'deal_open':
      return 'success';
    case 'closed_won':
      return 'success';
    case 'closed_lost':
      return 'default';
    case 'dormant':
      return 'default';
    default:
      return 'default';
  }
}

/**
 * Get channel color
 */
export function getChannelColor(channel: Channel): string {
  switch (channel) {
    case 'email':
      return '#3b82f6';
    case 'linkedin':
      return '#0077b5';
    case 'whatsapp':
      return '#25d366';
    case 'call':
      return '#8b5cf6';
    default:
      return '#6b7280';
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Generate initials from name
 */
export function getInitials(name: string): string {
  const parts = name.split(' ').filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

