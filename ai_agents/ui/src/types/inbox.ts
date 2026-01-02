// Inbox Module Types

export type Channel = 'email' | 'linkedin' | 'whatsapp' | 'call';

export type Temperature = 'cold' | 'warm' | 'hot';

export type LeadStatus =
  | 'new'
  | 'contacted'
  | 'in_conversation'
  | 'waiting_on_lead'
  | 'waiting_on_us'
  | 'meeting_scheduled'
  | 'deal_open'
  | 'closed_won'
  | 'closed_lost'
  | 'dormant';

export type StageStatus = 'active' | 'paused' | 'completed' | 'exited';

export type Direction = 'inbound' | 'outbound';

export type MessageStatus = 'sent' | 'delivered' | 'read' | 'failed';

export type AttentionReasonType = 'unread_reply' | 'overdue_step' | 'waiting_on_us' | 'hot_stale';

// ============ Embedded Types ============

export interface Company {
  name: string;
  domain?: string;
}

export interface Contact {
  id: string;
  name: string;
  title?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
}

export interface Owner {
  name: string;
  email: string;
}

export interface SequenceStep {
  stepName: string;
  channel: Channel;
  stepNumber: number;
}

export interface SequenceEnrollment {
  outreachCampaignId: string;
  outreachCampaignName: string;
  currentStage: SequenceStep;
  stageStatus: StageStatus;
  lastStepAt?: string;
  nextStepAt?: string;
  exitReason?: 'replied' | 'bounced' | 'manual_stop' | 'converted';
}

export interface LastTouch {
  channel: Channel;
  direction: Direction;
  snippet: string;
  at: string; // ISO string
}

export interface EventMeta {
  subject?: string;
  messageStatus?: MessageStatus;
  callDurationSec?: number;
  meetingId?: string;
  sequence?: {
    outreachCampaignId: string;
    stepName: string;
    stepNumber: number;
  };
  externalLink?: string;
}

export interface Note {
  id: string;
  at: string;
  author: string;
  text: string;
}

export interface AttentionReason {
  type: AttentionReasonType;
  message: string;
}

// ============ Main Types ============

export interface LeadSummary {
  leadId: string;
  company: Company;
  contact: Contact;
  owner: Owner;
  channelsPresent: Channel[];
  temperature: Temperature;
  temperatureDrivers: string[];
  status: LeadStatus;
  inSequence: boolean;
  sequence?: SequenceEnrollment;
  lastTouch?: LastTouch;
  nextStepAt?: string;
  unreadCount: number;
  attentionReasons?: AttentionReason[];
}

export interface EngagementEvent {
  id: string;
  leadId: string;
  channel: Channel;
  direction: Direction;
  at: string; // ISO string
  title?: string;
  content: string;
  meta?: EventMeta;
}

export interface LeadDetail {
  summary: LeadSummary;
  events: EngagementEvent[];
  notes: Note[];
}

// ============ API Types ============

export interface ListLeadsParams {
  query?: string;
  channel?: Channel;
  temperature?: Temperature;
  status?: LeadStatus;
  inSequence?: 'any' | 'yes' | 'no';
  stageStatus?: StageStatus;
  ownerEmail?: string;
  sort?: 'recent' | 'attention' | 'hot';
  tab?: 'all' | 'attention' | 'sequence';
  page?: number;
  pageSize?: number;
}

export interface ListLeadsResponse {
  leads: LeadSummary[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

export interface UpdateLeadRequest {
  temperature?: Temperature;
  status?: LeadStatus;
  temperatureDrivers?: string[];
}

export interface UpdateSequenceRequest {
  stageStatus?: StageStatus;
}

export interface AddNoteRequest {
  text: string;
}

// ============ UI Helper Types ============

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  new: 'New',
  contacted: 'Contacted',
  in_conversation: 'In Conversation',
  waiting_on_lead: 'Waiting on Lead',
  waiting_on_us: 'Waiting on Us',
  meeting_scheduled: 'Meeting Scheduled',
  deal_open: 'Deal Open',
  closed_won: 'Closed Won',
  closed_lost: 'Closed Lost',
  dormant: 'Dormant',
};

export const TEMPERATURE_LABELS: Record<Temperature, string> = {
  cold: 'Cold',
  warm: 'Warm',
  hot: 'Hot',
};

export const CHANNEL_LABELS: Record<Channel, string> = {
  email: 'Email',
  linkedin: 'LinkedIn',
  whatsapp: 'WhatsApp',
  call: 'Call',
};

export const STAGE_STATUS_LABELS: Record<StageStatus, string> = {
  active: 'Active',
  paused: 'Paused',
  completed: 'Completed',
  exited: 'Exited',
};

