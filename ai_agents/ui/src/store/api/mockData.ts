// Mock data for development without backend

import type { Campaign, CampaignCompany } from './campaignApi';
import type { Company, Contact } from './companyApi';

// Mock Campaigns
export const mockCampaigns: Campaign[] = [
  {
    _id: '507f1f77bcf86cd799439011',
    shortlisting_approach: 'ai_driven',
    prompts: {
      web: 'Find companies in the SaaS space that are growing rapidly',
      persona: 'VP of Engineering, CTO, Head of Product',
    },
    segmentation: {
      industry: ['Software', 'Technology'],
      keywords: 'SaaS, B2B, Enterprise',
      categories: 'Cloud Software',
    },
    target: {
      employee_count: ['51-200', '201-500'],
      revenue_min: '1000000',
      revenue_max: '50000000',
      currency: 'USD',
      location: {
        type: 'country',
        names: ['United States', 'Canada'],
      },
    },
    ownership: {
      hubspot_email: 'sales@company.com',
      product_name: 'Enterprise Suite',
      business_team: 'North America',
      user_email: 'john.doe@company.com',
    },
    lifecycle: {
      status: 'active',
    },
    metadata: {
      created_at: '2024-12-20T10:30:00Z',
      updated_at: '2024-12-25T14:20:00Z',
    },
    company_mappings_count: 45,
  },
  {
    _id: '507f1f77bcf86cd799439012',
    shortlisting_approach: 'manual',
    prompts: {
      web: 'Healthcare technology companies focused on patient care',
      persona: 'Healthcare IT Director, Chief Medical Officer',
    },
    segmentation: {
      industry: ['Healthcare', 'Medical Devices'],
      keywords: 'HealthTech, Patient Care, Medical Software',
      categories: 'Healthcare Technology',
    },
    target: {
      employee_count: ['201-500', '501-1000'],
      revenue_min: '5000000',
      revenue_max: '100000000',
      currency: 'USD',
      location: {
        type: 'region',
        names: ['North America', 'Europe'],
      },
    },
    ownership: {
      hubspot_email: 'healthcare@company.com',
      product_name: 'Health Platform',
      business_team: 'Healthcare Division',
      user_email: 'jane.smith@company.com',
    },
    lifecycle: {
      status: 'completed',
    },
    metadata: {
      created_at: '2024-11-15T08:00:00Z',
      updated_at: '2024-12-10T16:45:00Z',
    },
    company_mappings_count: 128,
  },
  {
    _id: '507f1f77bcf86cd799439013',
    shortlisting_approach: 'ai_driven',
    prompts: {
      web: 'Fintech startups disrupting traditional banking',
      persona: 'CEO, CFO, Head of Business Development',
    },
    segmentation: {
      industry: ['Financial Services', 'Fintech'],
      keywords: 'Payments, Banking, Cryptocurrency',
      categories: 'Financial Technology',
    },
    target: {
      employee_count: ['11-50', '51-200'],
      revenue_min: '500000',
      revenue_max: '20000000',
      currency: 'USD',
      location: {
        type: 'country',
        names: ['United Kingdom', 'Germany', 'France'],
      },
    },
    ownership: {
      hubspot_email: 'fintech@company.com',
      product_name: 'Payment Gateway',
      business_team: 'EMEA',
      user_email: 'mike.johnson@company.com',
    },
    lifecycle: {
      status: 'draft',
    },
    metadata: {
      created_at: '2024-12-22T09:15:00Z',
      updated_at: '2024-12-22T09:15:00Z',
    },
    company_mappings_count: 0,
  },
];

// Mock Campaign Companies
export const mockCampaignCompanies: Record<string, CampaignCompany[]> = {
  '507f1f77bcf86cd799439011': [
    {
      _id: 'cc001',
      campaign_id: '507f1f77bcf86cd799439011',
      company_id: 'comp001',
      company_status: true,
      linkedin_contact_status: true,
      is_relevant: true,
      metadata: {
        created_at: '2024-12-20T11:00:00Z',
        updated_at: '2024-12-21T14:30:00Z',
        confidence_level: 'high',
        key_factors: ['Industry match', 'Size fit', 'Growth stage'],
        relevance_reason: 'Strong alignment with target criteria and growth trajectory',
      },
    },
    {
      _id: 'cc002',
      campaign_id: '507f1f77bcf86cd799439011',
      company_id: 'comp002',
      company_status: true,
      linkedin_contact_status: false,
      is_relevant: true,
      metadata: {
        created_at: '2024-12-20T11:05:00Z',
        updated_at: '2024-12-21T15:00:00Z',
        confidence_level: 'medium',
        key_factors: ['Industry match', 'Revenue fit'],
        relevance_reason: 'Good industry and revenue alignment',
      },
    },
    {
      _id: 'cc003',
      campaign_id: '507f1f77bcf86cd799439011',
      company_id: 'comp003',
      company_status: false,
      linkedin_contact_status: false,
      is_relevant: false,
      metadata: {
        created_at: '2024-12-20T11:10:00Z',
        updated_at: '2024-12-21T16:00:00Z',
        confidence_level: 'low',
        key_factors: [],
        relevance_reason: 'Does not meet minimum revenue requirements',
      },
    },
  ],
};

// Mock Companies
export const mockCompanies: Company[] = [
  {
    _id: 'comp001',
    identifiers: {
      source_id: 'lusha_12345',
      name: 'TechVentures Inc.',
    },
    profile: {
      industry: ['Software', 'SaaS'],
      revenue_min: '10000000',
      revenue_max: '25000000',
      employee_count: ['101-200'],
    },
    location: {
      type: 'country',
      name: 'United States',
    },
    source: 'lusha',
    metadata: {
      created_at: '2024-12-01T10:00:00Z',
      updated_at: '2024-12-20T14:30:00Z',
      api_response: {
        primary_domain: 'techventures.com',
        website_url: 'https://www.techventures.com',
      },
    },
    contact_count: 12,
  },
  {
    _id: 'comp002',
    identifiers: {
      source_id: 'apollo_67890',
      name: 'CloudScale Solutions',
    },
    profile: {
      industry: ['Cloud Computing', 'Infrastructure'],
      revenue_min: '5000000',
      revenue_max: '15000000',
      employee_count: ['51-100'],
    },
    location: {
      type: 'country',
      name: 'Canada',
    },
    source: 'apollo',
    metadata: {
      created_at: '2024-11-15T08:00:00Z',
      updated_at: '2024-12-18T11:20:00Z',
      api_response: {
        primary_domain: 'cloudscale.io',
        website_url: 'https://cloudscale.io',
      },
    },
    contact_count: 8,
  },
  {
    _id: 'comp003',
    identifiers: {
      source_id: 'lusha_11111',
      name: 'DataDriven Analytics',
    },
    profile: {
      industry: ['Analytics', 'Business Intelligence'],
      revenue_min: '2000000',
      revenue_max: '8000000',
      employee_count: ['21-50'],
    },
    location: {
      type: 'country',
      name: 'United Kingdom',
    },
    source: 'lusha',
    metadata: {
      created_at: '2024-10-20T09:00:00Z',
      updated_at: '2024-12-15T16:45:00Z',
      api_response: {
        primary_domain: 'datadriven.co.uk',
        website_url: 'https://www.datadriven.co.uk',
      },
    },
    contact_count: 5,
  },
  {
    _id: 'comp004',
    identifiers: {
      source_id: 'apollo_22222',
      name: 'HealthFirst Technologies',
    },
    profile: {
      industry: ['Healthcare', 'Medical Software'],
      revenue_min: '15000000',
      revenue_max: '40000000',
      employee_count: ['201-500'],
    },
    location: {
      type: 'country',
      name: 'United States',
    },
    source: 'apollo',
    metadata: {
      created_at: '2024-09-10T07:30:00Z',
      updated_at: '2024-12-22T10:00:00Z',
      api_response: {
        primary_domain: 'healthfirst.com',
        website_url: 'https://www.healthfirst.com',
      },
    },
    contact_count: 24,
  },
];

// Mock Contacts
export const mockContacts: Record<string, Contact[]> = {
  'comp001': [
    {
      _id: 'contact001',
      company_id: 'comp001',
      contact_data: {
        firstname: 'Sarah',
        lastname: 'Chen',
        email: ['sarah.chen@techventures.com'],
        phone: ['+1-555-0101'],
        jobtitle: 'VP of Engineering',
        company: 'TechVentures Inc.',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/sarahchen',
        source: 'lusha',
      },
      metadata: {
        created_at: '2024-12-01T10:30:00Z',
        updated_at: '2024-12-20T14:30:00Z',
      },
    },
    {
      _id: 'contact002',
      company_id: 'comp001',
      contact_data: {
        firstname: 'Michael',
        lastname: 'Roberts',
        email: ['michael.roberts@techventures.com'],
        phone: ['+1-555-0102'],
        jobtitle: 'CTO',
        company: 'TechVentures Inc.',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/michaelroberts',
        source: 'lusha',
      },
      metadata: {
        created_at: '2024-12-01T10:35:00Z',
        updated_at: '2024-12-20T14:35:00Z',
      },
    },
    {
      _id: 'contact003',
      company_id: 'comp001',
      contact_data: {
        firstname: 'Emily',
        lastname: 'Watson',
        email: ['emily.watson@techventures.com'],
        phone: ['+1-555-0103'],
        jobtitle: 'Head of Product',
        company: 'TechVentures Inc.',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/emilywatson',
        source: 'lusha',
      },
      metadata: {
        created_at: '2024-12-01T10:40:00Z',
        updated_at: '2024-12-20T14:40:00Z',
      },
    },
  ],
  'comp002': [
    {
      _id: 'contact004',
      company_id: 'comp002',
      contact_data: {
        firstname: 'James',
        lastname: 'Morrison',
        email: ['james.morrison@cloudscale.io'],
        phone: ['+1-555-0201'],
        jobtitle: 'CEO',
        company: 'CloudScale Solutions',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/jamesmorrison',
        source: 'apollo',
      },
      metadata: {
        created_at: '2024-11-15T08:30:00Z',
        updated_at: '2024-12-18T11:30:00Z',
      },
    },
    {
      _id: 'contact005',
      company_id: 'comp002',
      contact_data: {
        firstname: 'Lisa',
        lastname: 'Park',
        email: ['lisa.park@cloudscale.io'],
        phone: ['+1-555-0202'],
        jobtitle: 'VP of Sales',
        company: 'CloudScale Solutions',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/lisapark',
        source: 'apollo',
      },
      metadata: {
        created_at: '2024-11-15T08:35:00Z',
        updated_at: '2024-12-18T11:35:00Z',
      },
    },
  ],
  'comp003': [
    {
      _id: 'contact006',
      company_id: 'comp003',
      contact_data: {
        firstname: 'David',
        lastname: 'Thompson',
        email: ['david.thompson@datadriven.co.uk'],
        phone: ['+44-20-7123-4567'],
        jobtitle: 'Managing Director',
        company: 'DataDriven Analytics',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/davidthompson',
        source: 'lusha',
      },
      metadata: {
        created_at: '2024-10-20T09:30:00Z',
        updated_at: '2024-12-15T16:50:00Z',
      },
    },
  ],
  'comp004': [
    {
      _id: 'contact007',
      company_id: 'comp004',
      contact_data: {
        firstname: 'Jennifer',
        lastname: 'Martinez',
        email: ['jennifer.martinez@healthfirst.com'],
        phone: ['+1-555-0401'],
        jobtitle: 'Chief Medical Officer',
        company: 'HealthFirst Technologies',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/jennifermartinez',
        source: 'apollo',
      },
      metadata: {
        created_at: '2024-09-10T08:00:00Z',
        updated_at: '2024-12-22T10:15:00Z',
      },
    },
    {
      _id: 'contact008',
      company_id: 'comp004',
      contact_data: {
        firstname: 'Robert',
        lastname: 'Kim',
        email: ['robert.kim@healthfirst.com'],
        phone: ['+1-555-0402'],
        jobtitle: 'VP of Engineering',
        company: 'HealthFirst Technologies',
      },
      linkedin_data: {
        linkedin_url: 'https://linkedin.com/in/robertkim',
        source: 'apollo',
      },
      metadata: {
        created_at: '2024-09-10T08:05:00Z',
        updated_at: '2024-12-22T10:20:00Z',
      },
    },
  ],
};

