import { baseApi } from './baseApi';

export interface Company {
  _id: string;
  identifiers: {
    source_id: string;
    name: string;
  };
  profile: {
    industry: string[];
    revenue_min: string | null;
    revenue_max: string | null;
    employee_count: string[] | null;
  };
  location: {
    type: string;
    name: string | string[];
  };
  source: string;
  metadata: {
    created_at: string;
    updated_at: string;
    api_response: {
      primary_domain?: string;
      website_url?: string;
      [key: string]: unknown;
    };
  };
  contact_count: number;
}

export interface Contact {
  _id: string;
  company_id: string;
  contact_data: {
    firstname: string;
    lastname: string;
    email: string[];
    phone: string[];
    jobtitle: string;
    company: string;
  };
  linkedin_data: {
    linkedin_url: string;
    source: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
  };
}

export interface Pagination {
  page_size: number;
  page_number: number;
  has_next: boolean;
  total_records: number;
}

export interface CompaniesResponse {
  success: boolean;
  data: Company[];
  pagination: Pagination;
  errors: string[];
}

export interface CompanyDetailsResponse {
  success: boolean;
  data: {
    company: Company;
    contacts: Contact[];
  };
  pagination: Pagination | null;
  errors: string[];
}

export interface GetCompaniesParams {
  page: number;
  limit: number;
  name?: string;
}

export interface GetCompanyDetailsParams {
  company_id: string;
  page: number;
  limit: number;
}

export const companyApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCompanies: builder.query<CompaniesResponse, GetCompaniesParams>({
      query: ({ page, limit, name }) => {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
        });
        
        if (name) params.append('name', name);
        
        return `/api/v1/companies?${params}`;
      },
      providesTags: ['Company'],
    }),
    
    getCompanyDetails: builder.query<CompanyDetailsResponse, GetCompanyDetailsParams>({
      query: ({ company_id, page, limit }) => {
        const params = new URLSearchParams({
          company_id,
          page: page.toString(),
          limit: limit.toString(),
        });
        
        return `/api/v1/company_details_with_contacts?${params}`;
      },
      providesTags: ['Company', 'Contact'],
    }),
  }),
});

export const { 
  useGetCompaniesQuery, 
  useGetCompanyDetailsQuery,
  useLazyGetCompanyDetailsQuery,
} = companyApi;

