// API exports
export { baseApi } from './baseApi';
export { campaignApi, useGetCampaignsQuery, useCreateCampaignMutation } from './campaignApi';
export type { 
  Campaign, 
  CampaignsResponse, 
  GetCampaignsParams,
  CreateCampaignPayload,
  CreateCampaignResponse,
} from './campaignApi';
export { 
  companyApi, 
  useGetCompaniesQuery, 
  useGetCompanyDetailsQuery,
  useLazyGetCompanyDetailsQuery,
} from './companyApi';
export type { 
  Company, 
  Contact, 
  CompaniesResponse, 
  CompanyDetailsResponse,
  GetCompaniesParams,
  GetCompanyDetailsParams,
  Pagination,
} from './companyApi';

