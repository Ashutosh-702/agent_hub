import { baseApi } from './baseApi';

export interface Campaign {
  _id: string;
  // Older UI / mock compatibility (backend may not send these)
  name?: string | null;
  // Selected during campaign creation (optional for backwards compatibility)
  shortlisting_approach?: string | null;
  prompts: {
    web: string;
    persona: string | null;
  };
  segmentation: {
    industry: string[];
    keywords: string | null;
    categories: string | null;
  };
  target: {
    employee_count: string[];
    revenue_min: string;
    revenue_max: string;
    currency: string;
    location: {
      type: string;
      names: string[];
    };
  };
  ownership: {
    hubspot_email: string | null;
    product_name: string | null;
    business_team: string | null;
    user_email: string | null;
  };
  lifecycle: {
    status: string;
  };
  prospecting_cycle?: {
    status: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
  };

  // Aggregates returned by /api/v1/campaigns
  relevant_company_mappings_count?: number;
  total_company_mappings_count?: number;
  contact_runs_count?: number;

  // Older UI / mock compatibility (backend may not send these)
  metrics?: {
    companies_prospected?: number;
    companies_qualified?: number;
    contacts_found?: number;
    contacts_outreached?: number;
  };
  company_mappings_count?: number;
}

export interface Pagination {
  page_size: number;
  page_number: number;
  has_next: boolean;
  total_records: number;
}

export interface CampaignsResponse {
  success: boolean;
  data: Campaign[];
  pagination: Pagination;
  errors: string[];
}

export interface GetCampaignsParams {
  page: number;
  limit: number;
  user_email?: string;
  product_name?: string;
  campaign_id?: string;
  status?: string;
  prospecting_cycle_status?: string;
}

export interface GetProspectingCampaignsParams {
  page: number;
  limit: number;
  prospecting_cycle_status?: string; // e.g., 'prospecting', 'company_qualification', 'contact_qualification', 'contact_enriched'
}

// Form submission payload
export interface CreateCampaignPayload {
  web_prompt: string;
  persona_prompt: string;
  industry: string;
  employee_count: string;
  currency: string;
  revenue_min: string;
  revenue_max: string;
  location: string;
  location_type: string;
  keywords: string;
  categories: string;
  hubspot_email: string;
  product_name: string;
  business_team: string;
  user_email: string;
  shortlisting_approach: string;
}

export interface CreateCampaignResponse {
  success: boolean;
  data?: {
    campaign_id: string;
  };
  message?: string;
}

export interface CreateCampaignFromProspectingJobPayload {
  industry: string;
  employee_count: string; // comma-separated
  revenue_min: string;
  revenue_max: string;
  location_type: string;
  location: string;
  currency: string;
  product_name?: string;
  prospecting_cycle_status: string;
}

export interface CreateCampaignFromProspectingJobResponse {
  success: boolean;
  data?: {
    message?: string;
    campaign_id?: string;
  };
  errors?: string[];
}

// Campaign Details with Companies
export interface CampaignCompany {
  _id: string;
  campaign_id: string;
  company_id: string;
  company_status: boolean;
  linkedin_contact_status: boolean;
  is_relevant: boolean;
  company?: {
    _id?: string;
    identifiers?: {
      name?: string;
      domain?: string;
      source_id?: string;
    };
    profile?: {
      industry?: string | string[];
      employee_count?: string | string[];
      revenue_min?: string;
      revenue_max?: string;
    };
    location?: {
      type?: string;
      name?: string | string[];
    };
    source?: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
    confidence_level?: string;
    key_factors?: string[];
    relevance_reason?: string;
  };
}

export interface CampaignDetailsResponse {
  success: boolean;
  data: {
    campaign: Campaign;
    companies: CampaignCompany[];
  };
  pagination: Pagination | null;
  errors: string[];
}

export interface GetCampaignDetailsParams {
  campaign_id: string;
  company_status?: boolean;
  page: number;
  limit: number;
}

export interface ManualCompanyQualificationPayload {
  campaign_id: string;
  selection_type: 'all' | 'selected' | 'selective';
  is_relevant: boolean;
  company_ids?: string[];
}

export interface ManualCompanyQualificationResponse {
  success: boolean;
  data?: {
    message?: string;
  };
  errors?: string[];
}

export interface GetApolloContactListParams {
  campaign_id: string;
  enrichment_status: boolean;
}

export interface GetApolloContactListResponse {
  success: boolean;
  data?: {
    message?: string;
    request_id?: string;
    campaign_id?: string;
  };
  errors?: string[];
}

export interface UpdateApolloContactEnrichmentStatusParams {
  campaign_id: string;
  selection_type: 'all' | 'selected';
  is_relevant: boolean;
  contact_ids: string[];
}

export interface UpdateApolloContactEnrichmentStatusResponse {
  success: boolean;
  data?: {
    message?: string;
  };
  errors?: string[];
}

export interface AiCompanyQualificationPayload {
  campaign_id: string;
  web_prompt: string;
}

export interface AiCompanyQualificationResponse {
  success: boolean;
  data?: {
    message?: string;
    campaign_id?: string;
  };
  errors?: string[];
}

export interface CompanyQualificationProgressData {
  campaign_id: string;
  status: 'not_started' | 'queued' | 'running' | 'completed' | 'failed';
  request_id?: string | null;
  started_at?: string | null;
  updated_at?: string | null;
  error?: string | null;
  progress: {
    total: number;
    processed: number;
    relevant: number;
  };
}

export interface CompanyQualificationProgressResponse {
  success: boolean;
  data?: CompanyQualificationProgressData;
  errors?: string[];
}

export interface HubspotSyncCandidate {
  contact_id: string;
  company_id?: string | null;
  company_name: string;
  first_name: string;
  last_name: string;
  designation: string;
  is_relevant?: boolean;
  email: string | null;
  phone: string | null;
}

export interface GetHubspotSyncCandidatesParams {
  campaign_id: string;
  page: number;
  limit: number;
}

export interface GetHubspotSyncCandidatesResponse {
  success: boolean;
  data: {
    campaign_id: string;
    contacts: HubspotSyncCandidate[];
  };
  pagination: Pagination | null;
  errors: string[];
}

export interface CampaignContactListItem {
  _id: string;
  campaign_id: string;
  company_id: string;
  contact_id: string;
  is_relevant: boolean;
  enrichment_status?: boolean;
  metadata?: {
    created_at?: string;
    updated_at?: string;
    raw_data?: unknown;
  };
  contact_data?: {
    firstname?: string;
    lastname?: string;
    email?: string[];
    phone?: string[];
    jobtitle?: string;
    company?: string;
    source_id?: string;
  };
  linkedin_data?: {
    linkedin_url?: string | null;
    source?: string;
  };
}

export interface GetCampaignContactListParams {
  campaign_id: string;
  page: number;
  limit: number;
}

export interface GetCampaignContactListResponse {
  success: boolean;
  data: {
    campaign: Campaign;
    contacts: CampaignContactListItem[];
  };
  pagination: Pagination | null;
  errors: string[];
}

export const campaignApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCampaigns: builder.query<CampaignsResponse, GetCampaignsParams>({
      query: ({ page, limit, ...filters }) => {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
        });
        
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
        
        return `/api/v1/campaigns?${params}`;
      },
      providesTags: ['Campaign'],
    }),

    getProspectingCampaigns: builder.query<CampaignsResponse, GetProspectingCampaignsParams>({
      query: ({ page, limit, prospecting_cycle_status }) => {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
        });
        
        if (prospecting_cycle_status) {
          params.append('prospecting_cycle_status', prospecting_cycle_status);
        }
        
        return `/api/v1/prospecting_campaigns?${params}`;
      },
      providesTags: ['Campaign'],
    }),
    
    createCampaign: builder.mutation<CreateCampaignResponse, CreateCampaignPayload>({
      query: (payload) => ({
        url: '/api/v1/sheets/upload_data_from_form',
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: ['Campaign'],
    }),

    createCampaignFromProspectingJob: builder.mutation<
      CreateCampaignFromProspectingJobResponse,
      CreateCampaignFromProspectingJobPayload
    >({
      query: (payload) => ({
        url: '/api/v1/create_campaign_from_prospecting_job',
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: ['Campaign'],
    }),
    
    getCampaignDetails: builder.query<CampaignDetailsResponse, GetCampaignDetailsParams>({
      query: ({ campaign_id, company_status, page, limit }) => {
        const params = new URLSearchParams({
          campaign_id,
          page: page.toString(),
          limit: limit.toString(),
        });
        
        // Only add company_status if it's explicitly true or false
        if (company_status !== undefined) {
          params.append('company_status', company_status.toString());
        }
        
        return `/api/v1/campaign_details_with_companies?${params}`;
      },
      providesTags: (_result, _error, { campaign_id }) => [
        { type: 'Campaign', id: campaign_id },
      ],
    }),

    manualCompanyQualification: builder.mutation<
      ManualCompanyQualificationResponse,
      ManualCompanyQualificationPayload
    >({
      query: (payload) => ({
        url: '/api/v1/manual_company_qualification',
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    getApolloContactList: builder.mutation<GetApolloContactListResponse, GetApolloContactListParams>({
      query: ({ campaign_id, enrichment_status }) => {
        const params = new URLSearchParams({
          campaign_id,
          enrichment_status: String(enrichment_status),
        });
        return {
          url: `/api/v1/get_apollo_contact_list?${params}`,
          method: 'POST',
        };
      },
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    enrichApolloContactList: builder.mutation<GetApolloContactListResponse, GetApolloContactListParams>({
      query: ({ campaign_id, enrichment_status }) => {
        const params = new URLSearchParams({
          campaign_id,
          enrichment_status: String(enrichment_status),
        });
        return {
          url: `/api/v1/enrich_apollo_contact_list?${params}`,
          method: 'POST',
        };
      },
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    updateApolloContactEnrichmentStatus: builder.mutation<
      UpdateApolloContactEnrichmentStatusResponse,
      UpdateApolloContactEnrichmentStatusParams
    >({
      query: ({ campaign_id, selection_type, is_relevant, contact_ids }) => {
        const params = new URLSearchParams({
          campaign_id,
          selection_type,
          is_relevant: String(is_relevant),
        });
        return {
          url: `/api/v1/update_apollo_contact_enrichment_status?${params}`,
          method: 'POST',
          body: contact_ids, // API accepts JSON array body (see curl)
        };
      },
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    aiCompanyQualification: builder.mutation<AiCompanyQualificationResponse, AiCompanyQualificationPayload>({
      query: (payload) => ({
        url: '/api/v1/ai_company_qualification',
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    companyQualificationProgress: builder.query<CompanyQualificationProgressResponse, { campaign_id: string }>({
      query: ({ campaign_id }) => {
        const params = new URLSearchParams({ campaign_id });
        return {
          url: `/api/v1/company_qualification_progress?${params}`,
          method: 'GET',
        };
      },
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    getCampaignContactList: builder.query<GetCampaignContactListResponse, GetCampaignContactListParams>({
      query: ({ campaign_id, page, limit }) => {
        const params = new URLSearchParams({
          campaign_id,
          page: String(page),
          limit: String(limit),
        });
        return {
          url: `/api/v1/get_campaign_contact_list?${params}`,
          method: 'GET',
        };
      },
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    getHubspotSyncCandidates: builder.query<GetHubspotSyncCandidatesResponse, GetHubspotSyncCandidatesParams>({
      query: ({ campaign_id, page, limit }) => {
        const params = new URLSearchParams({
          campaign_id,
          page: String(page),
          limit: String(limit),
        });
        return {
          url: `/api/v1/hubspot_sync_candidates?${params}`,
          method: 'GET',
        };
      },
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),
  }),
});

export const { 
  useGetCampaignsQuery, 
  useGetProspectingCampaignsQuery,
  useCreateCampaignMutation,
  useCreateCampaignFromProspectingJobMutation,
  useGetCampaignDetailsQuery,
  useLazyGetCampaignDetailsQuery,
  useManualCompanyQualificationMutation,
  useGetApolloContactListMutation,
  useEnrichApolloContactListMutation,
  useUpdateApolloContactEnrichmentStatusMutation,
  useAiCompanyQualificationMutation,
  useCompanyQualificationProgressQuery,
  useGetCampaignContactListQuery,
  useLazyGetCampaignContactListQuery,
  useGetHubspotSyncCandidatesQuery,
  useLazyGetHubspotSyncCandidatesQuery,
} = campaignApi;

