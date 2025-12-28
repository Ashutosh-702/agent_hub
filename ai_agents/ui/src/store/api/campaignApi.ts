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
  }),
});

export const { 
  useGetCampaignsQuery, 
  useCreateCampaignMutation,
  useCreateCampaignFromProspectingJobMutation,
  useGetCampaignDetailsQuery,
  useLazyGetCampaignDetailsQuery,
  useManualCompanyQualificationMutation,
} = campaignApi;

