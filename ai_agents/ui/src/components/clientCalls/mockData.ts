/**
 * Shared mock data for Client Calls module
 * Used for development and testing when API data is not available
 */

// Products list (Fynd product catalog)
export const PRODUCTS = [
  { id: 'GaaS', name: 'Fynd Platform (GaaS)', description: 'Complete e-commerce platform' },
  { id: 'OMS', name: 'Fynd OMS', description: 'Order management system' },
  { id: 'WMS', name: 'Fynd WMS', description: 'Warehouse management system' },
  { id: 'Storefront', name: 'Fynd Storefront', description: 'Headless commerce storefront' },
  { id: 'StoreOS', name: 'Fynd StoreOS', description: 'Point-of-sale solution' },
  { id: 'Konnect', name: 'Fynd Konnect', description: 'Integration platform' },
  { id: 'PixelBin', name: 'PixelBin', description: 'Image optimization platform' },
  { id: 'GlamAR', name: 'GlamAR', description: 'AR/VR virtual try-on' },
];

// Contact interface
export interface MockContact {
  id: string;
  firstName: string;
  lastName: string;
  jobTitle: string;
  email?: string;
}

// Company interface
export interface MockCompany {
  id: string;
  name: string;
  domain: string;
}

// Mock companies for testing (using valid 24-character MongoDB ObjectId hex strings)
export const MOCK_COMPANIES: MockCompany[] = [
  { id: '507f1f77bcf86cd799439011', name: 'Acme Retail Ltd', domain: 'acme-retail.com' },
  { id: '507f1f77bcf86cd799439012', name: 'TechStart Inc', domain: 'techstart.io' },
  { id: '507f1f77bcf86cd799439013', name: 'Fashion Hub India', domain: 'fashionhub.in' },
  { id: '507f1f77bcf86cd799439014', name: 'Metro Groceries', domain: 'metrogroceries.com' },
  { id: '507f1f77bcf86cd799439015', name: 'Urban Lifestyle Co', domain: 'urbanlifestyle.co' },
];

// Mock contacts by company ID (using valid ObjectIds)
export const MOCK_CONTACTS_BY_COMPANY: Record<string, MockContact[]> = {
  '507f1f77bcf86cd799439011': [
    { id: '607f1f77bcf86cd799439001', firstName: 'Rajesh', lastName: 'Kumar', jobTitle: 'VP Operations', email: 'rajesh@acme-retail.com' },
    { id: '607f1f77bcf86cd799439002', firstName: 'Priya', lastName: 'Sharma', jobTitle: 'Chief Technology Officer', email: 'priya@acme-retail.com' },
    { id: '607f1f77bcf86cd799439003', firstName: 'Amit', lastName: 'Patel', jobTitle: 'Head of E-commerce', email: 'amit@acme-retail.com' },
  ],
  '507f1f77bcf86cd799439012': [
    { id: '607f1f77bcf86cd799439004', firstName: 'Vikram', lastName: 'Singh', jobTitle: 'CEO', email: 'vikram@techstart.io' },
    { id: '607f1f77bcf86cd799439005', firstName: 'Ananya', lastName: 'Reddy', jobTitle: 'CTO', email: 'ananya@techstart.io' },
  ],
  '507f1f77bcf86cd799439013': [
    { id: '607f1f77bcf86cd799439006', firstName: 'Neha', lastName: 'Kapoor', jobTitle: 'Head of Digital', email: 'neha@fashionhub.in' },
    { id: '607f1f77bcf86cd799439007', firstName: 'Arjun', lastName: 'Mehta', jobTitle: 'Supply Chain Director', email: 'arjun@fashionhub.in' },
    { id: '607f1f77bcf86cd799439008', firstName: 'Kavita', lastName: 'Joshi', jobTitle: 'Marketing Head', email: 'kavita@fashionhub.in' },
  ],
  '507f1f77bcf86cd799439014': [
    { id: '607f1f77bcf86cd799439009', firstName: 'Suresh', lastName: 'Iyer', jobTitle: 'Operations Director', email: 'suresh@metrogroceries.com' },
    { id: '607f1f77bcf86cd799439010', firstName: 'Deepa', lastName: 'Nair', jobTitle: 'IT Manager', email: 'deepa@metrogroceries.com' },
  ],
  '507f1f77bcf86cd799439015': [
    { id: '607f1f77bcf86cd799439011', firstName: 'Rohit', lastName: 'Bansal', jobTitle: 'Founder & CEO', email: 'rohit@urbanlifestyle.co' },
    { id: '607f1f77bcf86cd799439012', firstName: 'Megha', lastName: 'Agarwal', jobTitle: 'VP Product', email: 'megha@urbanlifestyle.co' },
  ],
};

// Default mock contacts for any company not in the list
export const DEFAULT_MOCK_CONTACTS: MockContact[] = [
  { id: '607f1f77bcf86cd799439101', firstName: 'Rajesh', lastName: 'Kumar', jobTitle: 'VP Operations', email: 'rajesh@company.com' },
  { id: '607f1f77bcf86cd799439102', firstName: 'Priya', lastName: 'Sharma', jobTitle: 'Chief Technology Officer', email: 'priya@company.com' },
  { id: '607f1f77bcf86cd799439103', firstName: 'Amit', lastName: 'Patel', jobTitle: 'Head of E-commerce', email: 'amit@company.com' },
  { id: '607f1f77bcf86cd799439104', firstName: 'Sneha', lastName: 'Gupta', jobTitle: 'Director of Supply Chain', email: 'sneha@company.com' },
];

// Helper function to get contacts for a company
export const getContactsForCompany = (companyId: string): MockContact[] => {
  return MOCK_CONTACTS_BY_COMPANY[companyId] || DEFAULT_MOCK_CONTACTS;
};

// Meeting context for live meeting screen
export interface MeetingContextData {
  company: {
    name: string;
    industry: string;
    size: string;
    website: string;
  };
  contacts: Array<{ name: string; title: string }>;
  products: string[];
  painPoints: string[];
  previousMeetings: number;
  dealStage: string;
}

// Default mock context when real data is not available
export const DEFAULT_MEETING_CONTEXT: MeetingContextData = {
  company: {
    name: 'Unknown Company',
    industry: 'Unknown',
    size: 'Unknown',
    website: '',
  },
  contacts: [],
  products: [],
  painPoints: [],
  previousMeetings: 0,
  dealStage: 'Unknown',
};

// Mock meeting summary data
export interface MeetingSummaryData {
  id: string;
  meetingName: string;
  company: string;
  date: string;
  duration: number;
  attendees: string[];
  products: string[];
  summary: string;
  keyPoints: string[];
  objections: Array<{ objection: string; resolution: string }>;
  actionItems: Array<{ item: string; owner: string; dueDate: string }>;
  nextSteps: string[];
  followUpMessages: Array<{
    contact: string;
    email: string;
    subject: string;
    draft: string;
  }>;
}

// Default mock summary when real data is not available
export const DEFAULT_MEETING_SUMMARY: MeetingSummaryData = {
  id: '',
  meetingName: 'Meeting',
  company: 'Unknown Company',
  date: new Date().toISOString(),
  duration: 0,
  attendees: [],
  products: [],
  summary: 'Meeting summary not available.',
  keyPoints: [],
  objections: [],
  actionItems: [],
  nextSteps: [],
  followUpMessages: [],
};

