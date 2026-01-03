import { baseApi } from './baseApi';

// Meeting types
export interface Meeting {
  id: string;
  meeting_id: string;
  company_domain?: string;
  company_id?: string;
  contact_ids: string[];
  product_ids: string[];
  call_type?: 'google_meeting' | 'phone_call' | 'in_person';
  meeting_name?: string;
  notes?: string;
  status: 'scheduled' | 'prep' | 'live' | 'completed';
  scheduled_at?: string;
  started_at?: string;
  ended_at?: string;
  transcript?: TranscriptEntry[];
  live_insights?: LiveInsight[];
  summary?: string;
  key_discussion_points?: string[];
  action_items?: ActionItem[];
  next_steps?: string[];
  battlecard?: Battlecard;
  reflections?: MeetingReflections;
  created_at?: string;
  updated_at?: string;
}

export interface TranscriptEntry {
  timestamp: number;
  speaker: string;
  text: string;
  is_final: boolean;
}

export interface LiveInsight {
  id: string;
  timestamp: number;
  type: string;
  message: string;
  suggested_response: string;
  evidence: string;
  confidence: number;
  is_pinned: boolean;
  is_action_item: boolean;
}

export interface ActionItem {
  text: string;
  owner?: string;
  due_date?: string;
  completed?: boolean;
}

export interface BattlecardSection {
  title: string;
  content: string;
  bullet_points: string[];
}

export interface Battlecard {
  generated_at?: string;
  company_snapshot?: BattlecardSection;
  contact_snapshot?: BattlecardSection;
  why_now_product_fit?: BattlecardSection;
  talking_points: string[];
  likely_objections: { objection: string; response: string }[];
  discovery_questions: string[];
  proof_points: string[];
  recommended_agenda?: string;
  key_risks: string[];
  suggested_next_steps: string[];
  user_notes?: string;
}

export interface RecommendedFollowUp {
  action: string;
  priority: 'high' | 'medium' | 'low';
  suggested_timeline?: string;
}

export interface AIReflections {
  generated_at?: string;
  what_went_well: string[];
  areas_for_improvement: string[];
  key_learnings: string[];
  relationship_status?: 'cold' | 'warming' | 'engaged' | 'champion';
  deal_health_score?: number;
  recommended_follow_ups: RecommendedFollowUp[];
  competitive_positioning?: string;
  stakeholder_analysis?: string;
  risk_assessment: string[];
}

export interface ManualReflections {
  updated_at?: string;
  personal_notes?: string;
  what_went_well: string[];
  what_to_improve: string[];
  key_takeaways: string[];
  follow_up_commitments: string[];
  internal_action_items: string[];
  confidence_level?: 'low' | 'medium' | 'high';
  next_call_focus?: string;
}

export interface MeetingReflections {
  ai_generated?: AIReflections;
  manual?: ManualReflections;
}

// Request types
export interface CreateMeetingRequest {
  company_id: string;
  contact_ids: string[];
  product_ids: string[];
  meeting_name?: string;
  notes?: string;
  scheduled_at?: string;
}

export interface UpdateMeetingRequest {
  meeting_name?: string;
  notes?: string;
  status?: string;
  scheduled_at?: string;
}

export interface UpdateManualReflectionsRequest {
  personal_notes?: string;
  what_went_well?: string[];
  what_to_improve?: string[];
  key_takeaways?: string[];
  follow_up_commitments?: string[];
  internal_action_items?: string[];
  confidence_level?: string;
  next_call_focus?: string;
}

export interface GetMeetingsParams {
  status?: string;
  company_id?: string;
  page?: number;
  limit?: number;
}

// API Response wrapper
interface ApiResponse<T> {
  success: boolean;
  data: T;
}

interface PaginatedResponse<T> {
  meetings: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}

// Meetings API endpoints
export const meetingsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Create a new meeting
    createMeeting: builder.mutation<ApiResponse<Meeting>, CreateMeetingRequest>({
      query: (body) => ({
        url: '/meetings',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Meetings'],
    }),

    // Get all meetings with optional filters
    getMeetings: builder.query<ApiResponse<PaginatedResponse<Meeting>>, GetMeetingsParams>({
      query: (params) => ({
        url: '/meetings',
        params,
      }),
      providesTags: ['Meetings'],
    }),

    // Get completed meetings (for reflections history)
    getCompletedMeetings: builder.query<ApiResponse<Meeting[]>, void>({
      query: () => '/meetings/completed',
      providesTags: ['Meetings'],
    }),

    // Get meetings by company
    getMeetingsByCompany: builder.query<ApiResponse<Meeting[]>, string>({
      query: (companyId) => `/meetings/by-company/${companyId}`,
      providesTags: ['Meetings'],
    }),

    // Get a specific meeting by ID
    getMeeting: builder.query<ApiResponse<Meeting>, string>({
      query: (meetingId) => `/meetings/${meetingId}`,
      providesTags: (result, error, id) => [{ type: 'Meetings', id }],
    }),

    // Get a meeting by UUID
    getMeetingByUuid: builder.query<ApiResponse<Meeting>, string>({
      query: (meetingUuid) => `/meetings/by-uuid/${meetingUuid}`,
      providesTags: ['Meetings'],
    }),

    // Update a meeting
    updateMeeting: builder.mutation<ApiResponse<Meeting>, { meetingId: string; data: UpdateMeetingRequest }>({
      query: ({ meetingId, data }) => ({
        url: `/meetings/${meetingId}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { meetingId }) => [{ type: 'Meetings', id: meetingId }],
    }),

    // Delete a meeting
    deleteMeeting: builder.mutation<ApiResponse<{ message: string }>, string>({
      query: (meetingId) => ({
        url: `/meetings/${meetingId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Meetings'],
    }),

    // Start a meeting (get WebSocket info)
    startMeeting: builder.mutation<ApiResponse<{ meeting_id: string; meeting_uuid: string; websocket_url: string }>, string>({
      query: (meetingId) => ({
        url: `/meetings/${meetingId}/start`,
        method: 'POST',
      }),
    }),

    // Generate battlecard for a meeting
    generateBattlecard: builder.mutation<ApiResponse<Battlecard>, string>({
      query: (meetingId) => ({
        url: `/meetings/${meetingId}/battlecard`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, meetingId) => [{ type: 'Meetings', id: meetingId }],
    }),

    // Get battlecard for a meeting
    getBattlecard: builder.query<ApiResponse<Battlecard>, string>({
      query: (meetingId) => `/meetings/${meetingId}/battlecard`,
      providesTags: (result, error, id) => [{ type: 'Meetings', id }],
    }),

    // Generate AI reflections for a meeting
    generateReflections: builder.mutation<ApiResponse<AIReflections>, string>({
      query: (meetingId) => ({
        url: `/meetings/${meetingId}/reflections/generate`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, meetingId) => [{ type: 'Meetings', id: meetingId }],
    }),

    // Get reflections for a meeting
    getReflections: builder.query<ApiResponse<MeetingReflections | null>, string>({
      query: (meetingId) => `/meetings/${meetingId}/reflections`,
      providesTags: (result, error, id) => [{ type: 'Meetings', id }],
    }),

    // Update manual reflections
    updateManualReflections: builder.mutation<ApiResponse<ManualReflections>, { meetingId: string; data: UpdateManualReflectionsRequest }>({
      query: ({ meetingId, data }) => ({
        url: `/meetings/${meetingId}/reflections/manual`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { meetingId }) => [{ type: 'Meetings', id: meetingId }],
    }),

    // Get meeting context for a live call
    getMeetingContext: builder.query<ApiResponse<MeetingContext>, string>({
      query: (meetingId) => `/meetings/${meetingId}/context`,
      providesTags: (result, error, id) => [{ type: 'Meetings', id }],
    }),

    // Generate post-call summary
    generateSummary: builder.mutation<ApiResponse<MeetingSummary>, string>({
      query: (meetingId) => ({
        url: `/meetings/${meetingId}/summary`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, meetingId) => [{ type: 'Meetings', id: meetingId }],
    }),

    // Get meeting summary
    getMeetingSummary: builder.query<ApiResponse<MeetingSummary>, string>({
      query: (meetingId) => `/meetings/${meetingId}/summary`,
      providesTags: (result, error, id) => [{ type: 'Meetings', id }],
    }),
  }),
});

// Context and Summary types
export interface MeetingContext {
  company: {
    name: string;
    industry: string;
    size: string;
    website: string;
  };
  contacts: Array<{ name: string; title: string }>;
  products: string[];
  painPoints: string[];
  previousMeetings: number;
  dealStage: string;
}

export interface MeetingSummary {
  summary: string;
  keyPoints: string[];
  objections: Array<{ objection: string; resolution: string }>;
  actionItems: Array<{ item: string; owner: string; dueDate: string }>;
  nextSteps: string[];
  followUpMessages?: Array<{
    contact: string;
    email: string;
    subject: string;
    draft: string;
  }>;
}

// Export hooks
export const {
  useCreateMeetingMutation,
  useGetMeetingsQuery,
  useGetCompletedMeetingsQuery,
  useGetMeetingsByCompanyQuery,
  useGetMeetingQuery,
  useGetMeetingByUuidQuery,
  useUpdateMeetingMutation,
  useDeleteMeetingMutation,
  useStartMeetingMutation,
  useGenerateBattlecardMutation,
  useGetBattlecardQuery,
  useGenerateReflectionsMutation,
  useGetReflectionsQuery,
  useUpdateManualReflectionsMutation,
  useGetMeetingContextQuery,
  useGenerateSummaryMutation,
  useGetMeetingSummaryQuery,
} = meetingsApi;

