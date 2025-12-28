import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { API_BASE_URL } from '../../config/api.js';
import { mockCampaigns, mockCampaignCompanies, mockCompanies, mockContacts } from './mockData';

// Enable mock mode when backend is not available
export const USE_MOCK_DATA = false;

// Mock query function that returns mock data based on the endpoint
const mockBaseQuery = async (args: string | { url: string }) => {
  const url = typeof args === 'string' ? args : args.url;
  
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Parse the URL to determine which mock data to return
  if (url.includes('/api/v1/campaigns') && !url.includes('campaign_details')) {
    const urlParams = new URLSearchParams(url.split('?')[1] || '');
    const page = parseInt(urlParams.get('page') || '1');
    const limit = parseInt(urlParams.get('limit') || '10');
    const start = (page - 1) * limit;
    const paginatedData = mockCampaigns.slice(start, start + limit);
    
    return {
      data: {
        success: true,
        data: paginatedData,
        pagination: {
          page_size: limit,
          page_number: page,
          has_next: start + limit < mockCampaigns.length,
          total_records: mockCampaigns.length,
        },
        errors: [],
      },
    };
  }
  
  if (url.includes('/api/v1/campaign_details_with_companies')) {
    const urlParams = new URLSearchParams(url.split('?')[1] || '');
    const campaignId = urlParams.get('campaign_id') || '';
    const page = parseInt(urlParams.get('page') || '1');
    const limit = parseInt(urlParams.get('limit') || '10');
    
    const campaign = mockCampaigns.find(c => c._id === campaignId);
    const companies = mockCampaignCompanies[campaignId] || [];
    const start = (page - 1) * limit;
    const paginatedCompanies = companies.slice(start, start + limit);
    
    if (!campaign) {
      return {
        error: { status: 404, data: 'Campaign not found' },
      };
    }
    
    return {
      data: {
        success: true,
        data: {
          campaign,
          companies: paginatedCompanies,
        },
        pagination: {
          page_size: limit,
          page_number: page,
          has_next: start + limit < companies.length,
          total_records: companies.length,
        },
        errors: [],
      },
    };
  }
  
  if (url.includes('/api/v1/companies') && !url.includes('company_details')) {
    const urlParams = new URLSearchParams(url.split('?')[1] || '');
    const page = parseInt(urlParams.get('page') || '1');
    const limit = parseInt(urlParams.get('limit') || '10');
    const name = urlParams.get('name') || '';
    
    let filteredCompanies = mockCompanies;
    if (name) {
      filteredCompanies = mockCompanies.filter(c => 
        c.identifiers.name.toLowerCase().includes(name.toLowerCase())
      );
    }
    
    const start = (page - 1) * limit;
    const paginatedData = filteredCompanies.slice(start, start + limit);
    
    return {
      data: {
        success: true,
        data: paginatedData,
        pagination: {
          page_size: limit,
          page_number: page,
          has_next: start + limit < filteredCompanies.length,
          total_records: filteredCompanies.length,
        },
        errors: [],
      },
    };
  }
  
  if (url.includes('/api/v1/company_details_with_contacts')) {
    const urlParams = new URLSearchParams(url.split('?')[1] || '');
    const companyId = urlParams.get('company_id') || '';
    const page = parseInt(urlParams.get('page') || '1');
    const limit = parseInt(urlParams.get('limit') || '10');
    
    const company = mockCompanies.find(c => c._id === companyId);
    const contacts = mockContacts[companyId] || [];
    const start = (page - 1) * limit;
    const paginatedContacts = contacts.slice(start, start + limit);
    
    if (!company) {
      return {
        error: { status: 404, data: 'Company not found' },
      };
    }
    
    return {
      data: {
        success: true,
        data: {
          company,
          contacts: paginatedContacts,
        },
        pagination: {
          page_size: limit,
          page_number: page,
          has_next: start + limit < contacts.length,
          total_records: contacts.length,
        },
        errors: [],
      },
    };
  }
  
  // Default: return empty success response
  return {
    data: {
      success: true,
      data: [],
      errors: [],
    },
  };
};

// Real fetch query
const realBaseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  prepareHeaders: (headers) => {
    headers.set('accept', 'application/json');
    headers.set('Content-Type', 'application/json');
    return headers;
  },
});

// Combined query that uses mock or real based on flag
const dynamicBaseQuery: typeof realBaseQuery = async (args, api, extraOptions) => {
  if (USE_MOCK_DATA) {
    return mockBaseQuery(args as string | { url: string });
  }
  return realBaseQuery(args, api, extraOptions);
};

// Base API with common configuration
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: dynamicBaseQuery,
  tagTypes: ['Campaign', 'Company', 'Contact'],
  endpoints: () => ({}),
});
