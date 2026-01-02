// Mock HubSpot API Services
// These simulate real API calls with delays and mock data
// Designed to be easily swapped with real APIs later

import type {
  HubSpotCompany,
  HubSpotContact,
  HubSpotDeal,
  CompanyEnrichment,
  ContactEnrichment,
  MockProduct,
  MockStage,
} from '../types/hubspot';

// ============ Mock Data ============
export const MOCK_PRODUCTS: MockProduct[] = [
  { id: 'prod_1', name: 'Fynd Platform' },
  { id: 'prod_2', name: 'Fynd OMS' },
  { id: 'prod_3', name: 'Fynd WMS' },
  { id: 'prod_4', name: 'Uniket' },
  { id: 'prod_5', name: 'Fynd Commerce' },
];

export const MOCK_STAGES: MockStage[] = [
  { id: 'stage_1', name: 'Qualification' },
  { id: 'stage_2', name: 'Discovery' },
  { id: 'stage_3', name: 'Proposal' },
  { id: 'stage_4', name: 'Negotiation' },
  { id: 'stage_5', name: 'Closed Won' },
  { id: 'stage_6', name: 'Closed Lost' },
];

const MOCK_COMPANIES: HubSpotCompany[] = [
  { id: 'comp_1', name: 'Acme Corp', domain: 'acme.com', legalEntityName: 'Acme Corporation Inc.', ownerEmail: 'john@fynd.com' },
  { id: 'comp_2', name: 'TechStart Inc', domain: 'techstart.io', legalEntityName: 'TechStart Inc.', ownerEmail: 'jane@fynd.com' },
  { id: 'comp_3', name: 'Global Retail', domain: 'globalretail.com', legalEntityName: 'Global Retail Limited', ownerEmail: 'john@fynd.com' },
  { id: 'comp_4', name: 'Fashion Forward', domain: 'fashionforward.co', legalEntityName: 'Fashion Forward Pvt Ltd', ownerEmail: 'sarah@fynd.com' },
  { id: 'comp_5', name: 'E-Commerce Pro', domain: 'ecommercepro.com', legalEntityName: 'E-Commerce Pro LLC', ownerEmail: 'mike@fynd.com' },
];

const MOCK_CONTACTS: HubSpotContact[] = [
  { id: 'contact_1', name: 'John Smith', email: 'john.smith@acme.com', phone: '+1-555-0101' },
  { id: 'contact_2', name: 'Jane Doe', email: 'jane.doe@techstart.io', phone: '+1-555-0102' },
  { id: 'contact_3', name: 'Bob Wilson', email: 'bob@globalretail.com', phone: '+1-555-0103' },
  { id: 'contact_4', name: 'Alice Brown', email: 'alice@fashionforward.co', phone: '+1-555-0104' },
  { id: 'contact_5', name: 'Charlie Davis', email: 'charlie@ecommercepro.com', phone: '+1-555-0105' },
];

const MOCK_DEALS: HubSpotDeal[] = [
  { id: 'deal_1', name: 'Acme - Fynd Platform Deal', companyId: 'comp_1', product: 'Fynd Platform', stage: 'Proposal', amount: 50000 },
  { id: 'deal_2', name: 'TechStart - OMS Implementation', companyId: 'comp_2', product: 'Fynd OMS', stage: 'Negotiation', amount: 75000 },
  { id: 'deal_3', name: 'Global Retail - Commerce Suite', companyId: 'comp_3', product: 'Fynd Commerce', stage: 'Discovery', amount: 120000 },
];

// ============ Utility Functions ============
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const generateId = () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// ============ Company APIs ============
export async function canonicalizeDomain(url: string): Promise<string> {
  await delay(300);
  
  try {
    // Extract domain from URL
    let domain = url.toLowerCase().trim();
    
    // Remove protocol
    domain = domain.replace(/^https?:\/\//, '');
    
    // Remove www.
    domain = domain.replace(/^www\./, '');
    
    // Remove path and query
    domain = domain.split('/')[0].split('?')[0];
    
    return domain;
  } catch {
    return url;
  }
}

export async function searchHubspotCompanies(params: { domain?: string; name?: string }): Promise<HubSpotCompany[]> {
  await delay(800);
  
  const { domain, name } = params;
  
  return MOCK_COMPANIES.filter(company => {
    if (domain && company.domain?.includes(domain)) return true;
    if (name && company.name.toLowerCase().includes(name.toLowerCase())) return true;
    return false;
  });
}

export async function enrichCompany(params: { url: string; domain: string }): Promise<CompanyEnrichment> {
  await delay(1500);
  
  // Simulate enrichment based on domain
  const domainPart = params.domain.split('.')[0];
  
  return {
    companyName: domainPart.charAt(0).toUpperCase() + domainPart.slice(1) + ' Inc.',
    legalEntityName: '',
    industry: ['Technology', 'E-Commerce', 'Retail', 'Fashion'][Math.floor(Math.random() * 4)],
    employeeBand: ['1-50', '51-200', '201-500', '501-1000', '1000+'][Math.floor(Math.random() * 5)],
    hqLocation: ['San Francisco, CA', 'New York, NY', 'Mumbai, India', 'London, UK'][Math.floor(Math.random() * 4)],
    registeredAddress: '123 Business Park, Suite 100',
    website: `https://${params.domain}`,
    linkedIn: `https://linkedin.com/company/${domainPart}`,
    confidence: {
      companyName: 'high',
      legalEntityName: 'low',
      industry: 'medium',
      employeeBand: 'medium',
      hqLocation: 'high',
      registeredAddress: 'low',
      website: 'high',
      linkedIn: 'medium',
    },
  };
}

export async function createHubspotCompany(payload: {
  name: string;
  domain: string;
  legalEntityName: string;
  ownerEmail: string;
  industry?: string;
  employeeBand?: string;
  hqLocation?: string;
  website?: string;
  linkedIn?: string;
}): Promise<HubSpotCompany> {
  await delay(1000);
  
  const newCompany: HubSpotCompany = {
    id: `comp_${generateId()}`,
    name: payload.name,
    domain: payload.domain,
    legalEntityName: payload.legalEntityName,
    ownerEmail: payload.ownerEmail,
  };
  
  // In a real app, this would be persisted
  MOCK_COMPANIES.push(newCompany);
  
  return newCompany;
}

export async function linkExistingCompany(
  existingCompanyId: string,
  _payloadMeta: Record<string, unknown>
): Promise<HubSpotCompany> {
  await delay(600);
  
  const company = MOCK_COMPANIES.find(c => c.id === existingCompanyId);
  if (!company) {
    throw new Error('Company not found');
  }
  
  return company;
}

// ============ Contact APIs ============
export async function searchHubspotContacts(params: { email: string }): Promise<HubSpotContact[]> {
  await delay(700);
  
  return MOCK_CONTACTS.filter(contact =>
    contact.email.toLowerCase().includes(params.email.toLowerCase())
  );
}

export async function enrichContact(params: { email: string }): Promise<ContactEnrichment> {
  await delay(1200);
  
  const emailParts = params.email.split('@');
  const nameParts = emailParts[0].split('.');
  
  return {
    phone: `+1-555-${Math.floor(1000 + Math.random() * 9000)}`,
    linkedIn: `https://linkedin.com/in/${nameParts.join('-')}`,
    title: ['CEO', 'CTO', 'VP of Sales', 'Head of Operations', 'Director of Engineering'][Math.floor(Math.random() * 5)],
    department: ['Executive', 'Engineering', 'Sales', 'Operations', 'Marketing'][Math.floor(Math.random() * 5)],
    confidence: {
      phone: 'medium',
      linkedIn: 'high',
      title: 'medium',
      department: 'high',
    },
  };
}

export async function createHubspotContact(payload: {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  linkedIn?: string;
  title?: string;
  department?: string;
  associateType: 'company' | 'deal';
  associateId: string;
}): Promise<HubSpotContact> {
  await delay(1000);
  
  const newContact: HubSpotContact = {
    id: `contact_${generateId()}`,
    name: `${payload.firstName} ${payload.lastName}`,
    email: payload.email,
    phone: payload.phone,
  };
  
  MOCK_CONTACTS.push(newContact);
  
  return newContact;
}

export async function linkExistingContact(
  existingContactId: string,
  _payloadMeta: Record<string, unknown>
): Promise<HubSpotContact> {
  await delay(600);
  
  const contact = MOCK_CONTACTS.find(c => c.id === existingContactId);
  if (!contact) {
    throw new Error('Contact not found');
  }
  
  return contact;
}

// ============ Deal APIs ============
export async function searchHubspotDeals(params: { companyId: string; product: string }): Promise<HubSpotDeal[]> {
  await delay(700);
  
  return MOCK_DEALS.filter(deal =>
    deal.companyId === params.companyId && deal.product === params.product
  );
}

export async function createHubspotDeal(payload: {
  product: string;
  companyId: string;
  contactIds: string[];
  ownerEmail?: string;
  stage?: string;
  amount?: number;
}): Promise<HubSpotDeal> {
  await delay(1000);
  
  const company = MOCK_COMPANIES.find(c => c.id === payload.companyId);
  
  const newDeal: HubSpotDeal = {
    id: `deal_${generateId()}`,
    name: `${company?.name || 'New Company'} - ${payload.product} Deal`,
    companyId: payload.companyId,
    product: payload.product,
    stage: payload.stage || 'Qualification',
    amount: payload.amount,
  };
  
  MOCK_DEALS.push(newDeal);
  
  return newDeal;
}

export async function linkExistingDeal(
  existingDealId: string,
  _payloadMeta: Record<string, unknown>
): Promise<HubSpotDeal> {
  await delay(600);
  
  const deal = MOCK_DEALS.find(d => d.id === existingDealId);
  if (!deal) {
    throw new Error('Deal not found');
  }
  
  return deal;
}

// ============ Utility APIs ============
export async function getCompanyById(id: string): Promise<HubSpotCompany | null> {
  await delay(300);
  return MOCK_COMPANIES.find(c => c.id === id) || null;
}

export async function getContactById(id: string): Promise<HubSpotContact | null> {
  await delay(300);
  return MOCK_CONTACTS.find(c => c.id === id) || null;
}

export async function searchCompaniesForDropdown(query: string): Promise<HubSpotCompany[]> {
  await delay(400);
  
  if (!query) {
    return MOCK_COMPANIES.slice(0, 5);
  }
  
  return MOCK_COMPANIES.filter(c =>
    c.name.toLowerCase().includes(query.toLowerCase()) ||
    c.domain?.toLowerCase().includes(query.toLowerCase())
  );
}

export async function getContactsByCompany(companyId: string): Promise<HubSpotContact[]> {
  await delay(400);
  
  // Simulate contacts associated with a company based on domain matching
  const company = MOCK_COMPANIES.find(c => c.id === companyId);
  if (!company?.domain) {
    return [];
  }
  
  return MOCK_CONTACTS.filter(c => 
    c.email.includes(company.domain!.split('.')[0])
  );
}

