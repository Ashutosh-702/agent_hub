// API exports
export { baseApi } from './baseApi';
export { 
  campaignApi, 
  useGetCampaignsQuery, 
  useCreateCampaignMutation,
  useGetCampaignDetailsQuery,
  useUpdateCampaignCompanyRunMutation,
  useUpdateCampaignContactRunMutation,
} from './campaignApi';
export type { 
  Campaign, 
  CampaignsResponse, 
  GetCampaignsParams,
  CreateCampaignPayload,
  CreateCampaignResponse,
  CampaignCompany,
  CampaignDetailsResponse,
  GetCampaignDetailsParams,
  UpdateCampaignCompanyRunParams,
  UpdateCampaignCompanyRunResponse,
  UpdateCampaignContactRunParams,
  UpdateCampaignContactRunResponse,
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

