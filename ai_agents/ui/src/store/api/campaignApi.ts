import { baseApi } from './baseApi';

export interface Campaign {
  _id: string;
  prompts: {
    web: string;
    persona: string;
  };
  segmentation: {
    industry: string[];
    keywords: string;
    categories: string;
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
    hubspot_email: string;
    product_name: string;
    business_team: string;
    user_email: string;
  };
  lifecycle: {
    status: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
  };
  company_mappings_count: number;
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
}

export interface CreateCampaignResponse {
  success: boolean;
  data?: {
    campaign_id: string;
  };
  message?: string;
}

// Campaign Details with Companies
export interface CampaignCompany {
  _id: string;
  campaign_id: string;
  company_id: string;
  company_status: boolean;
  linkedin_contact_status: boolean;
  is_relevant: boolean;
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
  }),
});

export const { 
  useGetCampaignsQuery, 
  useCreateCampaignMutation,
  useGetCampaignDetailsQuery,
} = campaignApi;

