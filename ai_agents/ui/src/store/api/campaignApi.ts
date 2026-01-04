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
  single_company?: {
    domain?: string;
    status?: 'pending' | 'processing' | 'completed' | 'failed' | 'not_found';
    company_id?: string;
    company_name?: string;
    error?: string;
  };
  csv_import?: {
    domains?: string[];
    total_count?: number;
    processed_count?: number;
    existing_count?: number;
    already_enriched_count?: number;  // Companies that already had Apollo data (skipped Apollo search)
    new_count?: number;
    success_count?: number;
    failed_count?: number;
    status?: 'pending' | 'processing' | 'completed' | 'failed';
    error?: string;
  };
  campaign_type?: string;
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
  campaign_type?: string; // Type of campaign (wide_prospecting, import_csv, etc.)
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

// Single Company Campaign
export interface CreateCampaignFromSingleCompanyPayload {
  company_domain: string;
  product_name?: string;
  campaign_type?: string;
  prospecting_cycle_status?: string;
}

export interface CreateCampaignFromSingleCompanyResponse {
  success: boolean;
  data?: {
    message?: string;
    campaign_id?: string;
    request_id?: string | null;
    company_exists?: boolean;
    company_id?: string;
  };
  errors?: string[];
}

// CSV Import Campaign
export interface CreateCampaignFromCSVImportPayload {
  company_domains: string[];
  product_name?: string;
  campaign_type?: string;
  prospecting_cycle_status?: string;
}

export interface CreateCampaignFromCSVImportResponse {
  success: boolean;
  data?: {
    message?: string;
    campaign_id?: string;
    request_id?: string | null;
    total_companies?: number;
    // These are now populated asynchronously via Kafka and available in campaign details
    existing_companies?: number;
    new_companies?: number;
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
      source_domain?: string;
      source_id?: string;
      website_url?: string;
    };
    profile?: {
      industry?: string | string[];
      employee_count?: string | string[];
      revenue_min?: string;
      revenue_max?: string;
    };
    location?: {
      name?: string;
      type?: string;
    };
    source?: string;
    metadata?: {
      created_at?: string;
      updated_at?: string;
      api_response?: Record<string, unknown>;
    };
  };
  // Company details from Apollo domain search (for single company flow)
  company_details?: {
    name?: string;
    website_url?: string;
    primary_domain?: string;
    linkedin_url?: string;
    phone?: string;
    industry?: string;
    employee_count?: number;
    revenue?: number;
    revenue_printed?: string;
    logo_url?: string;
    location?: {
      city?: string;
      state?: string;
      country?: string;
    };
    apollo_id?: string;
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
  // Personalization fields (populated after Step 5 saves)
  personalization_status?: 'pending' | 'approved' | 'rejected';
  personalized_message?: string;
  ai_generated_deck?: string;
  email_id?: string;
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

    createCampaignFromSingleCompany: builder.mutation<
      CreateCampaignFromSingleCompanyResponse,
      CreateCampaignFromSingleCompanyPayload
    >({
      query: (payload) => ({
        url: '/api/v1/create_campaign_from_single_company',
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: ['Campaign'],
    }),

    createCampaignFromCSVImport: builder.mutation<
      CreateCampaignFromCSVImportResponse,
      CreateCampaignFromCSVImportPayload
    >({
      query: (payload) => ({
        url: '/api/v1/create_campaign_from_csv_import',
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

    syncToHubspot: builder.mutation<
      { success: boolean; data: { message: string; request_id: string; campaign_id: string } },
      { campaign_id: string }
    >({
      query: (body) => ({
        url: '/api/v1/sync_to_hubspot',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    getHubspotSyncProgress: builder.query<
      {
        success: boolean;
        data: {
          _id: string;
          prospecting_cycle?: {
            status: string;
          };
          synced_hubspot_companies_count: number;
          total_hubspot_companies_count: number;
          campaign_id: string;
        };
      },
      { campaign_id: string }
    >({
      query: ({ campaign_id }) => ({
        url: `/api/v1/get_hubspot_syncd_companies?campaign_id=${campaign_id}`,
        method: 'GET',
      }),
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Personalization API - generates personalized content for contacts
    generatePersonalization: builder.mutation<
      {
        success: boolean;
        data: {
          message: string;
          request_id: string;
          campaign_id: string;
        };
      },
      {
        campaign_id: string;
        contact_ids: string[];
      }
    >({
      query: (body) => ({
        url: '/api/v1/generate_personalization',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Get personalization status/results for contacts
    getPersonalizationResults: builder.query<
      {
        success: boolean;
        data: {
          campaign_id: string;
          status: 'queued' | 'processing' | 'completed' | 'failed';
          results: Array<{
            contact_id: string;
            email_id: string;
            text_message: string;
            deck_url: string; // Public URL of cloud storage
            status: 'pending' | 'generated' | 'approved' | 'rejected';
          }>;
        };
      },
      { campaign_id: string }
    >({
      query: ({ campaign_id }) => ({
        url: `/api/v1/personalization_results?campaign_id=${campaign_id}`,
        method: 'GET',
      }),
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Save personalization for a single contact
    saveContactPersonalization: builder.mutation<
      {
        success: boolean;
        data: {
          message: string;
          campaign_id: string;
          contact_id: string;
        };
      },
      {
        campaign_id: string;
        contact_id: string;
        email_id: string;
        personalized_message: string;
        ai_generated_deck: string;
      }
    >({
      query: (body) => ({
        url: '/api/v1/save_contact_personalization',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Bulk save personalization for multiple contacts
    bulkSaveContactPersonalization: builder.mutation<
      {
        success: boolean;
        data: {
          message: string;
          campaign_id: string;
          saved_count: number;
        };
      },
      {
        campaign_id: string;
        personalizations: Array<{
          contact_id: string;
          email_id: string;
          personalized_message: string;
          ai_generated_deck: string;
        }>;
      }
    >({
      query: (body) => ({
        url: '/api/v1/bulk_save_contact_personalization',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Get enrollment contacts with full details and metadata
    getEnrollmentContacts: builder.query<
      {
        success: boolean;
        data: {
          campaign: Record<string, unknown>;
          contacts: Array<{
            campaign_contact_run_id: string;
            campaign_id: string;
            company_id: string | null;
            contact_id: string | null;
            is_relevant: boolean;
            enrichment_status: string | null;
            personalization_status: string;
            personalized_message: string;
            ai_generated_deck: string;
            email_id: string;
            campaign_contact_run_metadata: Record<string, unknown>;
            contact_data: {
              firstname: string;
              lastname: string;
              email: string[];
              phone: string[];
              jobtitle: string;
              company: string;
              source_id: string;
            } | null;
            linkedin_data: {
              linkedin_url: string | null;
              source: string;
            } | null;
            contact_metadata: Record<string, unknown> | null;
            company_data: {
              name: string | null;
              domain: string | null;
              website: string | null;
              industry: string | null;
              employee_count: string | null;
              revenue: string | null;
              location: string | null;
              description: string | null;
              company_metadata: Record<string, unknown> | null;
            } | null;
          }>;
          pagination: {
            page_size: number;
            page_number: number;
            has_next: boolean;
            total_records: number;
          };
          total_enrollment_ready: number;
        };
        pagination: Record<string, unknown>;
      },
      { campaign_id: string; page?: number; limit?: number }
    >({
      query: ({ campaign_id, page = 1, limit = 100 }) => ({
        url: `/api/v1/enrollment_contacts?campaign_id=${campaign_id}&page=${page}&limit=${limit}`,
        method: 'GET',
      }),
      providesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),

    // Fetch available Lemlist campaigns/sequences
    getLemlistCampaigns: builder.query<
      {
        success: boolean;
        data: {
          campaigns: Array<{
            id: string;
            name: string;
            labels: string[];
            status: string;
            steps: number | null;
            created_at: string | null;
            updated_at: string | null;
          }>;
          total: number;
        };
      },
      void
    >({
      query: () => ({
        url: '/api/v1/lemlist_campaigns',
        method: 'GET',
      }),
      providesTags: ['Campaign'],
    }),

    // Enroll contacts to a Lemlist sequence
    enrollContactsToSequence: builder.mutation<
      {
        success: boolean;
        data: {
          message: string;
          campaign_id: string;
          sequence_id: string;
          sequence_name: string;
          enrolled_count: number;
          enrolled_contacts: Array<{
            contact_id: string;
            email: string;
            first_name: string | null;
            last_name: string | null;
            job_title: string | null;
            phone: string[];
            linkedin_url: string | null;
            company_name: string | null;
            company_domain: string | null;
            company_website: string | null;
            company_industry: string | null;
            company_size: string | null;
            company_location: string | null;
            personalized_message: string;
            ai_generated_deck: string;
            campaign_contact_run_metadata: Record<string, unknown>;
            contact_metadata: Record<string, unknown> | null;
            company_metadata: Record<string, unknown> | null;
            contact_source_data: Record<string, unknown> | null;
            linkedin_data: Record<string, unknown> | null;
          }>;
        };
      },
      {
        campaign_id: string;
        sequence_id: string;
        sequence_name: string;
        contact_ids?: string[];
      }
    >({
      query: (body) => ({
        url: '/api/v1/enroll_contacts_to_sequence',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, { campaign_id }) => [{ type: 'Campaign', id: campaign_id }],
    }),
  }),
});

export const { 
  useGetCampaignsQuery, 
  useGetProspectingCampaignsQuery,
  useCreateCampaignMutation,
  useCreateCampaignFromProspectingJobMutation,
  useCreateCampaignFromSingleCompanyMutation,
  useCreateCampaignFromCSVImportMutation,
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
  useSyncToHubspotMutation,
  useLazyGetHubspotSyncProgressQuery,
  useGeneratePersonalizationMutation,
  useLazyGetPersonalizationResultsQuery,
  useSaveContactPersonalizationMutation,
  useBulkSaveContactPersonalizationMutation,
  useGetEnrollmentContactsQuery,
  useLazyGetEnrollmentContactsQuery,
  useEnrollContactsToSequenceMutation,
  useGetLemlistCampaignsQuery,
} = campaignApi;

