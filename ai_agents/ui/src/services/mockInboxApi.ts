// Mock Inbox API Service
// Provides mock data for development/demo mode
// Designed to be swapped with real API later

import type {
  LeadSummary,
  LeadDetail,
  EngagementEvent,
  Note,
  ListLeadsParams,
  ListLeadsResponse,
  UpdateLeadRequest,
  Channel,
  Temperature,
  LeadStatus,
  Direction,
  AttentionReason,
} from '../types/inbox';

// ============ Mock Data Generation ============

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const generateId = () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const COMPANIES = [
  { name: 'Acme Corp', domain: 'acme.com' },
  { name: 'TechStart Inc', domain: 'techstart.io' },
  { name: 'Global Retail', domain: 'globalretail.com' },
  { name: 'Fashion Forward', domain: 'fashionforward.co' },
  { name: 'E-Commerce Pro', domain: 'ecommercepro.com' },
  { name: 'Digital Solutions', domain: 'digitalsolutions.tech' },
  { name: 'CloudScale', domain: 'cloudscale.io' },
  { name: 'DataDriven', domain: 'datadriven.ai' },
  { name: 'SmartRetail', domain: 'smartretail.com' },
  { name: 'NextGen Systems', domain: 'nextgensystems.com' },
  { name: 'InnovateTech', domain: 'innovatetech.io' },
  { name: 'Quantum Labs', domain: 'quantumlabs.dev' },
  { name: 'Apex Industries', domain: 'apexindustries.com' },
  { name: 'Summit Solutions', domain: 'summitsolutions.co' },
  { name: 'Velocity Corp', domain: 'velocitycorp.io' },
];

const FIRST_NAMES = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'Chris', 'Amanda', 'Robert', 'Lisa', 'James', 'Jennifer', 'William', 'Ashley', 'Daniel'];
const LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Moore'];
const TITLES = ['CEO', 'CTO', 'VP of Sales', 'Head of Operations', 'Director of Engineering', 'Marketing Director', 'Product Manager', 'Sales Manager', 'COO', 'CFO'];

const OWNERS = [
  { name: 'Alex Thompson', email: 'alex@company.com' },
  { name: 'Jordan Lee', email: 'jordan@company.com' },
  { name: 'Casey Morgan', email: 'casey@company.com' },
  { name: 'Taylor Swift', email: 'taylor@company.com' },
];

const CHANNELS: Channel[] = ['email', 'linkedin', 'whatsapp', 'call'];
const TEMPERATURES: Temperature[] = ['cold', 'warm', 'hot'];
const STATUSES: LeadStatus[] = ['new', 'contacted', 'in_conversation', 'waiting_on_lead', 'waiting_on_us', 'meeting_scheduled', 'deal_open', 'closed_won', 'closed_lost', 'dormant'];

const TEMPERATURE_DRIVERS = {
  cold: ['No previous engagement', 'New prospect', 'Outbound only'],
  warm: ['Opened emails', 'Clicked links', 'Previous interaction', 'Downloaded content'],
  hot: ['Replied positively', 'Requested demo', 'Multiple engagements', 'Expressed interest', 'Budget confirmed'],
};

const EMAIL_SUBJECTS = [
  'Re: Partnership Opportunity',
  'Following up on our conversation',
  'Quick question about your product',
  'Interested in learning more',
  'Demo request',
  'Pricing inquiry',
  'Meeting confirmation',
  'Thank you for reaching out',
];

const EMAIL_SNIPPETS = [
  'Thank you for reaching out. I would be interested in learning more about your platform...',
  'I have been looking for a solution like this. Can we schedule a call this week?',
  'We are currently evaluating several options. Could you send me more details?',
  'This looks promising. Let me discuss with my team and get back to you.',
  'I am not the right person for this. You should contact our procurement team.',
  'We already have a solution in place. Maybe next quarter?',
  'Sounds interesting! What is your pricing like for enterprise?',
  'Can you send me a case study from a similar company in our industry?',
];

const LINKEDIN_SNIPPETS = [
  'Thanks for connecting! I saw your company is doing interesting work...',
  'Hi, I came across your profile and thought we could explore synergies.',
  'Appreciate the connection. Happy to chat if you have time.',
  'Interesting! Let me take a look at your website.',
];

const CALL_TRANSCRIPTS = [
  'Discussed product features and pricing. They are interested in a demo next week.',
  'Quick discovery call. They have budget allocated for Q2. Following up with proposal.',
  'Left voicemail. Will try again tomorrow.',
  'Great conversation about their pain points. They are evaluating 3 vendors.',
];

// Generate mock leads
function generateMockLeads(count: number): LeadSummary[] {
  const leads: LeadSummary[] = [];
  
  for (let i = 0; i < count; i++) {
    const company = COMPANIES[i % COMPANIES.length];
    const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
    const lastName = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
    const temperature = TEMPERATURES[Math.floor(Math.random() * TEMPERATURES.length)];
    const status = STATUSES[Math.floor(Math.random() * STATUSES.length)];
    
    // Determine channels (1-3 channels)
    const numChannels = Math.floor(Math.random() * 3) + 1;
    const shuffledChannels = [...CHANNELS].sort(() => Math.random() - 0.5);
    const channelsPresent = shuffledChannels.slice(0, numChannels);
    
    // Last touch
    const lastChannel = channelsPresent[Math.floor(Math.random() * channelsPresent.length)];
    const isInbound = Math.random() > 0.5;
    const daysAgo = Math.floor(Math.random() * 14);
    const lastTouchDate = new Date();
    lastTouchDate.setDate(lastTouchDate.getDate() - daysAgo);
    
    let snippet = '';
    if (lastChannel === 'email') snippet = EMAIL_SNIPPETS[Math.floor(Math.random() * EMAIL_SNIPPETS.length)];
    else if (lastChannel === 'linkedin') snippet = LINKEDIN_SNIPPETS[Math.floor(Math.random() * LINKEDIN_SNIPPETS.length)];
    else if (lastChannel === 'call') snippet = CALL_TRANSCRIPTS[Math.floor(Math.random() * CALL_TRANSCRIPTS.length)];
    else snippet = 'Recent message...';
    
    // Sequence
    const inSequence = Math.random() > 0.6;
    
    // Unread (more likely for inbound recent touches)
    let unreadCount = 0;
    if (isInbound && daysAgo < 3) {
      unreadCount = Math.random() > 0.5 ? Math.floor(Math.random() * 3) + 1 : 0;
    }
    
    leads.push({
      leadId: `lead_${generateId()}`,
      company,
      contact: {
        id: `contact_${generateId()}`,
        name: `${firstName} ${lastName}`,
        title: TITLES[Math.floor(Math.random() * TITLES.length)],
        email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${company.domain}`,
        phone: `+1-555-${String(Math.floor(Math.random() * 9000) + 1000)}`,
        linkedin: `https://linkedin.com/in/${firstName.toLowerCase()}${lastName.toLowerCase()}`,
      },
      owner: OWNERS[Math.floor(Math.random() * OWNERS.length)],
      channelsPresent,
      temperature,
      temperatureDrivers: TEMPERATURE_DRIVERS[temperature].slice(0, Math.floor(Math.random() * 3) + 1),
      status,
      inSequence,
      sequence: inSequence ? {
        outreachCampaignId: `campaign_${Math.floor(Math.random() * 5) + 1}`,
        outreachCampaignName: `Outreach Campaign ${Math.floor(Math.random() * 5) + 1}`,
        currentStage: {
          stepName: ['Initial Email', 'Follow-up 1', 'Follow-up 2', 'LinkedIn Connect', 'Final Touch'][Math.floor(Math.random() * 5)],
          channel: channelsPresent[0],
          stepNumber: Math.floor(Math.random() * 5) + 1,
        },
        stageStatus: ['active', 'paused', 'completed', 'exited'][Math.floor(Math.random() * 4)] as any,
        lastStepAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        nextStepAt: Math.random() > 0.3 ? new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000 - 2 * 24 * 60 * 60 * 1000).toISOString() : undefined,
      } : undefined,
      lastTouch: {
        channel: lastChannel,
        direction: isInbound ? 'inbound' : 'outbound',
        snippet: snippet.substring(0, 100),
        at: lastTouchDate.toISOString(),
      },
      nextStepAt: inSequence && Math.random() > 0.3 ? new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000 - 2 * 24 * 60 * 60 * 1000).toISOString() : undefined,
      unreadCount,
    });
  }
  
  return leads;
}

// Generate mock events for a lead
function generateMockEvents(leadId: string, channels: Channel[], count: number): EngagementEvent[] {
  const events: EngagementEvent[] = [];
  
  for (let i = 0; i < count; i++) {
    const channel = channels[Math.floor(Math.random() * channels.length)];
    const direction: Direction = Math.random() > 0.5 ? 'inbound' : 'outbound';
    const daysAgo = Math.floor(Math.random() * 30);
    const eventDate = new Date();
    eventDate.setDate(eventDate.getDate() - daysAgo);
    eventDate.setHours(Math.floor(Math.random() * 12) + 8);
    
    let title = '';
    let content = '';
    
    if (channel === 'email') {
      title = direction === 'inbound' ? 'Email received' : 'Email sent';
      content = direction === 'inbound' 
        ? EMAIL_SNIPPETS[Math.floor(Math.random() * EMAIL_SNIPPETS.length)]
        : 'Hi, I wanted to follow up on our previous conversation about how we can help your team...';
    } else if (channel === 'linkedin') {
      title = direction === 'inbound' ? 'LinkedIn message received' : 'LinkedIn message sent';
      content = LINKEDIN_SNIPPETS[Math.floor(Math.random() * LINKEDIN_SNIPPETS.length)];
    } else if (channel === 'whatsapp') {
      title = direction === 'inbound' ? 'WhatsApp message received' : 'WhatsApp message sent';
      content = 'Quick message via WhatsApp...';
    } else {
      title = 'Call completed';
      content = CALL_TRANSCRIPTS[Math.floor(Math.random() * CALL_TRANSCRIPTS.length)];
    }
    
    events.push({
      id: `event_${generateId()}`,
      leadId,
      channel,
      direction,
      at: eventDate.toISOString(),
      title,
      content,
      meta: channel === 'email' ? {
        subject: EMAIL_SUBJECTS[Math.floor(Math.random() * EMAIL_SUBJECTS.length)],
        messageStatus: ['sent', 'delivered', 'read'][Math.floor(Math.random() * 3)] as any,
      } : channel === 'call' ? {
        callDurationSec: Math.floor(Math.random() * 1800) + 60,
      } : undefined,
    });
  }
  
  // Sort by date descending
  return events.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
}

// Generate mock notes
function generateMockNotes(_leadId: string, count: number): Note[] {
  const notes: Note[] = [];
  const noteTexts = [
    'Spoke with them today, they are very interested in our enterprise plan.',
    'Need to follow up next week after their board meeting.',
    'They mentioned budget constraints, consider offering a discount.',
    'Decision maker is on vacation until the 15th.',
    'Competitor is also in the running, need to highlight our differentiators.',
  ];
  
  for (let i = 0; i < count; i++) {
    const daysAgo = Math.floor(Math.random() * 14);
    const noteDate = new Date();
    noteDate.setDate(noteDate.getDate() - daysAgo);
    
    notes.push({
      id: `note_${generateId()}`,
      at: noteDate.toISOString(),
      author: OWNERS[Math.floor(Math.random() * OWNERS.length)].name,
      text: noteTexts[Math.floor(Math.random() * noteTexts.length)],
    });
  }
  
  return notes.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
}

// ============ Mock Data Store ============

let mockLeads: LeadSummary[] = generateMockLeads(40);
const mockEventsMap: Map<string, EngagementEvent[]> = new Map();
const mockNotesMap: Map<string, Note[]> = new Map();

// Pre-generate events and notes for each lead
mockLeads.forEach(lead => {
  const eventCount = Math.floor(Math.random() * 18) + 8; // 8-25 events
  mockEventsMap.set(lead.leadId, generateMockEvents(lead.leadId, lead.channelsPresent, eventCount));
  mockNotesMap.set(lead.leadId, generateMockNotes(lead.leadId, Math.floor(Math.random() * 3)));
});

// ============ Utility Functions ============

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

// ============ Mock API Functions ============

export async function listLeads(params: ListLeadsParams = {}): Promise<ListLeadsResponse> {
  await delay(300 + Math.random() * 200);
  
  let filtered = [...mockLeads];
  
  // Apply filters
  if (params.query) {
    const q = params.query.toLowerCase();
    filtered = filtered.filter(lead =>
      lead.company.name.toLowerCase().includes(q) ||
      lead.contact.name.toLowerCase().includes(q) ||
      lead.contact.email?.toLowerCase().includes(q)
    );
  }
  
  if (params.channel) {
    filtered = filtered.filter(lead => lead.channelsPresent.includes(params.channel!));
  }
  
  if (params.temperature) {
    filtered = filtered.filter(lead => lead.temperature === params.temperature);
  }
  
  if (params.status) {
    filtered = filtered.filter(lead => lead.status === params.status);
  }
  
  if (params.inSequence === 'yes') {
    filtered = filtered.filter(lead => lead.inSequence);
  } else if (params.inSequence === 'no') {
    filtered = filtered.filter(lead => !lead.inSequence);
  }
  
  if (params.stageStatus && params.inSequence !== 'no') {
    filtered = filtered.filter(lead => lead.sequence?.stageStatus === params.stageStatus);
  }
  
  if (params.ownerEmail) {
    filtered = filtered.filter(lead => lead.owner.email === params.ownerEmail);
  }
  
  // Tab filters
  if (params.tab === 'attention') {
    filtered = filtered.filter(lead => computeNeedsAttention(lead).length > 0);
  } else if (params.tab === 'sequence') {
    filtered = filtered.filter(lead => lead.inSequence);
  }
  
  // Sorting
  if (params.sort === 'recent' || !params.sort) {
    filtered.sort((a, b) => {
      const aDate = a.lastTouch ? new Date(a.lastTouch.at).getTime() : 0;
      const bDate = b.lastTouch ? new Date(b.lastTouch.at).getTime() : 0;
      return bDate - aDate;
    });
  } else if (params.sort === 'attention') {
    filtered.sort((a, b) => {
      const aReasons = computeNeedsAttention(a).length;
      const bReasons = computeNeedsAttention(b).length;
      if (bReasons !== aReasons) return bReasons - aReasons;
      const aDate = a.lastTouch ? new Date(a.lastTouch.at).getTime() : 0;
      const bDate = b.lastTouch ? new Date(b.lastTouch.at).getTime() : 0;
      return aDate - bDate; // Oldest first
    });
  } else if (params.sort === 'hot') {
    const tempOrder = { hot: 3, warm: 2, cold: 1 };
    filtered.sort((a, b) => tempOrder[b.temperature] - tempOrder[a.temperature]);
  }
  
  // Add attention reasons
  filtered = filtered.map(lead => ({
    ...lead,
    attentionReasons: computeNeedsAttention(lead),
  }));
  
  // Pagination
  const page = params.page || 1;
  const pageSize = params.pageSize || 50;
  const start = (page - 1) * pageSize;
  const paged = filtered.slice(start, start + pageSize);
  
  return {
    leads: paged,
    total: filtered.length,
    page,
    pageSize,
    hasNext: start + pageSize < filtered.length,
  };
}

export async function getLeadDetail(leadId: string): Promise<LeadDetail | null> {
  await delay(200 + Math.random() * 150);
  
  const lead = mockLeads.find(l => l.leadId === leadId);
  if (!lead) return null;
  
  const events = mockEventsMap.get(leadId) || [];
  const notes = mockNotesMap.get(leadId) || [];
  
  return {
    summary: {
      ...lead,
      attentionReasons: computeNeedsAttention(lead),
    },
    events,
    notes,
  };
}

export async function updateLead(leadId: string, update: UpdateLeadRequest): Promise<void> {
  await delay(150);
  
  const index = mockLeads.findIndex(l => l.leadId === leadId);
  if (index === -1) throw new Error('Lead not found');
  
  if (update.temperature) {
    mockLeads[index].temperature = update.temperature;
  }
  if (update.status) {
    mockLeads[index].status = update.status;
  }
  if (update.temperatureDrivers) {
    mockLeads[index].temperatureDrivers = update.temperatureDrivers;
  }
}

export async function markLeadRead(leadId: string): Promise<void> {
  await delay(100);
  
  const index = mockLeads.findIndex(l => l.leadId === leadId);
  if (index === -1) throw new Error('Lead not found');
  
  mockLeads[index].unreadCount = 0;
}

export async function updateSequence(leadId: string, update: { stageStatus?: string }): Promise<void> {
  await delay(150);
  
  const index = mockLeads.findIndex(l => l.leadId === leadId);
  if (index === -1) throw new Error('Lead not found');
  
  if (mockLeads[index].sequence && update.stageStatus) {
    mockLeads[index].sequence!.stageStatus = update.stageStatus as any;
  }
}

export async function addNote(leadId: string, text: string): Promise<void> {
  await delay(150);
  
  const lead = mockLeads.find(l => l.leadId === leadId);
  if (!lead) throw new Error('Lead not found');
  
  const notes = mockNotesMap.get(leadId) || [];
  notes.unshift({
    id: `note_${generateId()}`,
    at: new Date().toISOString(),
    author: 'Current User',
    text,
  });
  mockNotesMap.set(leadId, notes);
}

// Export owners for filter dropdown
export const MOCK_OWNERS = OWNERS;

