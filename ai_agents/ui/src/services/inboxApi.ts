// Inbox API Service
// Calls backend API endpoints
// Falls back to mock API in development mode

import type {
  ListLeadsParams,
  ListLeadsResponse,
  LeadDetail,
  UpdateLeadRequest,
} from '../types/inbox';
import * as mockApi from './mockInboxApi';

const API_BASE = '/api/v1/inbox';

// Check if we should use mock API
// Default to mock mode unless explicitly set to use real API
const USE_MOCK = import.meta.env.VITE_USE_REAL_API !== 'true';

// ============ API Functions ============

export async function listLeads(params: ListLeadsParams = {}): Promise<ListLeadsResponse> {
  if (USE_MOCK) {
    return mockApi.listLeads(params);
  }

  const searchParams = new URLSearchParams();
  
  if (params.query) searchParams.set('query', params.query);
  if (params.channel) searchParams.set('channel', params.channel);
  if (params.temperature) searchParams.set('temperature', params.temperature);
  if (params.status) searchParams.set('status', params.status);
  if (params.inSequence) searchParams.set('in_sequence', params.inSequence);
  if (params.stageStatus) searchParams.set('stage_status', params.stageStatus);
  if (params.ownerEmail) searchParams.set('owner_email', params.ownerEmail);
  if (params.sort) searchParams.set('sort', params.sort);
  if (params.tab) searchParams.set('tab', params.tab);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));

  const response = await fetch(`${API_BASE}/leads?${searchParams.toString()}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch leads: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Transform snake_case to camelCase
  return {
    leads: data.leads.map(transformLeadSummary),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    hasNext: data.has_next,
  };
}

export async function getLeadDetail(leadId: string): Promise<LeadDetail | null> {
  if (USE_MOCK) {
    return mockApi.getLeadDetail(leadId);
  }

  const response = await fetch(`${API_BASE}/leads/${leadId}`);
  
  if (response.status === 404) {
    return null;
  }
  
  if (!response.ok) {
    throw new Error(`Failed to fetch lead detail: ${response.statusText}`);
  }

  const data = await response.json();
  
  return {
    summary: transformLeadSummary(data.summary),
    events: data.events.map(transformEvent),
    notes: data.notes.map(transformNote),
  };
}

export async function updateLead(leadId: string, update: UpdateLeadRequest): Promise<void> {
  if (USE_MOCK) {
    return mockApi.updateLead(leadId, update);
  }

  const response = await fetch(`${API_BASE}/leads/${leadId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      temperature: update.temperature,
      status: update.status,
      temperature_drivers: update.temperatureDrivers,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to update lead: ${response.statusText}`);
  }
}

export async function markLeadRead(leadId: string): Promise<void> {
  if (USE_MOCK) {
    return mockApi.markLeadRead(leadId);
  }

  const response = await fetch(`${API_BASE}/leads/${leadId}/read`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to mark lead as read: ${response.statusText}`);
  }
}

export async function updateSequence(leadId: string, update: { stageStatus?: string }): Promise<void> {
  if (USE_MOCK) {
    return mockApi.updateSequence(leadId, update);
  }

  const response = await fetch(`${API_BASE}/leads/${leadId}/sequence`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stage_status: update.stageStatus,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to update sequence: ${response.statusText}`);
  }
}

export async function addNote(leadId: string, text: string): Promise<void> {
  if (USE_MOCK) {
    return mockApi.addNote(leadId, text);
  }

  const response = await fetch(`${API_BASE}/leads/${leadId}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Failed to add note: ${response.statusText}`);
  }
}

export async function triggerSync(fullSync: boolean = false): Promise<{ stats: Record<string, number> }> {
  if (USE_MOCK) {
    // Mock sync
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { stats: { inboxes_fetched: 10, leads_created: 5, events_created: 25 } };
  }

  const response = await fetch(`${API_BASE}/sync?full_sync=${fullSync}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to trigger sync: ${response.statusText}`);
  }

  return response.json();
}

// ============ Transform Functions ============

function transformLeadSummary(data: any): any {
  return {
    leadId: data.lead_id,
    company: data.company,
    contact: {
      id: data.contact?.id,
      name: data.contact?.name,
      title: data.contact?.title,
      email: data.contact?.email,
      phone: data.contact?.phone,
      linkedin: data.contact?.linkedin,
    },
    owner: data.owner,
    channelsPresent: data.channels_present,
    temperature: data.temperature,
    temperatureDrivers: data.temperature_drivers || [],
    status: data.status,
    inSequence: data.in_sequence,
    sequence: data.sequence ? {
      outreachCampaignId: data.sequence.outreach_campaign_id,
      outreachCampaignName: data.sequence.outreach_campaign_name,
      currentStage: data.sequence.current_stage ? {
        stepName: data.sequence.current_stage.step_name,
        channel: data.sequence.current_stage.channel,
        stepNumber: data.sequence.current_stage.step_number,
      } : undefined,
      stageStatus: data.sequence.stage_status,
      lastStepAt: data.sequence.last_step_at,
      nextStepAt: data.sequence.next_step_at,
      exitReason: data.sequence.exit_reason,
    } : undefined,
    lastTouch: data.last_touch ? {
      channel: data.last_touch.channel,
      direction: data.last_touch.direction,
      snippet: data.last_touch.snippet,
      at: data.last_touch.at,
    } : undefined,
    nextStepAt: data.next_step_at,
    unreadCount: data.unread_count || 0,
    attentionReasons: data.attention_reasons?.map((r: any) => ({
      type: r.type,
      message: r.message,
    })),
  };
}

function transformEvent(data: any): any {
  return {
    id: data.id,
    leadId: data.lead_id,
    channel: data.channel,
    direction: data.direction,
    at: data.at,
    title: data.title,
    content: data.content,
    meta: data.meta ? {
      subject: data.meta.subject,
      messageStatus: data.meta.message_status,
      callDurationSec: data.meta.call_duration_sec,
      meetingId: data.meta.meeting_id,
      sequence: data.meta.sequence,
      externalLink: data.meta.external_link,
    } : undefined,
  };
}

function transformNote(data: any): any {
  return {
    id: data.id,
    at: data.at,
    author: data.author,
    text: data.text,
  };
}

// Re-export mock owners for filters
export { MOCK_OWNERS } from './mockInboxApi';
export { computeNeedsAttention } from './mockInboxApi';

