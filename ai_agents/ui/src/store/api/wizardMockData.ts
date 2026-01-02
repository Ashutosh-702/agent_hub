import type { CampaignFilters, Contact, Prospect } from '../../components/campaign/NewCampaignWizard';

export const WIZARD_INDUSTRIES = [
  'Software & Technology',
  'Healthcare & Medical',
  'Financial Services',
  'E-commerce & Retail',
  'Manufacturing',
  'Professional Services',
  'Education',
  'Media & Entertainment',
];

export const WIZARD_REGIONS = [
  'North America',
  'Europe',
  'Asia Pacific',
  'Latin America',
  'Middle East & Africa',
  'United States',
  'United Kingdom',
  'Germany',
  'India',
  'Australia',
];

export const WIZARD_EMPLOYEE_COUNTS = [
  '1-10',
  '11-50',
  '51-200',
  '201-500',
  '501-1000',
  '1001-5000',
  '5000+',
];

type BaseCompany = {
  name: string;
  industry: string;
  location: string;
  revenue: string;
  employeeCount: string;
};

const BASE_COMPANIES: BaseCompany[] = [
  { name: 'TechFlow Solutions', industry: 'Software & Technology', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'MedCore Systems', industry: 'Healthcare & Medical', location: 'United Kingdom', revenue: '$10M - $25M', employeeCount: '201-500' },
  { name: 'FinanceHub Inc', industry: 'Financial Services', location: 'Germany', revenue: '$25M - $50M', employeeCount: '501-1000' },
  { name: 'CloudScale Pro', industry: 'Software & Technology', location: 'United States', revenue: '$2M - $5M', employeeCount: '11-50' },
  { name: 'DataDriven Analytics', industry: 'Software & Technology', location: 'India', revenue: '$1M - $2M', employeeCount: '51-200' },
  { name: 'HealthBridge Tech', industry: 'Healthcare & Medical', location: 'Australia', revenue: '$5M - $10M', employeeCount: '201-500' },
  { name: 'RetailGenius', industry: 'E-commerce & Retail', location: 'United States', revenue: '$10M - $25M', employeeCount: '201-500' },
  { name: 'ManufactPro', industry: 'Manufacturing', location: 'Germany', revenue: '$50M - $100M', employeeCount: '1001-5000' },
  { name: 'EduLearn Platform', industry: 'Education', location: 'United Kingdom', revenue: '$2M - $5M', employeeCount: '51-200' },
  { name: 'MediaStream Co', industry: 'Media & Entertainment', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'ConsultPro Services', industry: 'Professional Services', location: 'North America', revenue: '$1M - $2M', employeeCount: '11-50' },
  { name: 'InnovateTech Labs', industry: 'Software & Technology', location: 'Europe', revenue: '$10M - $25M', employeeCount: '201-500' },
  { name: 'NextGen AI', industry: 'Software & Technology', location: 'United States', revenue: '$10M - $25M', employeeCount: '51-200' },
  { name: 'BioHealth Labs', industry: 'Healthcare & Medical', location: 'United States', revenue: '$25M - $50M', employeeCount: '201-500' },
  { name: 'CapitalFlow', industry: 'Financial Services', location: 'United Kingdom', revenue: '$50M - $100M', employeeCount: '501-1000' },
  { name: 'ShopSmart', industry: 'E-commerce & Retail', location: 'Germany', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'BuildRight Corp', industry: 'Manufacturing', location: 'United States', revenue: '$25M - $50M', employeeCount: '501-1000' },
  { name: 'LearnHub', industry: 'Education', location: 'India', revenue: '$1M - $2M', employeeCount: '11-50' },
  { name: 'ContentPro', industry: 'Media & Entertainment', location: 'United Kingdom', revenue: '$2M - $5M', employeeCount: '51-200' },
  { name: 'LegalEase', industry: 'Professional Services', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'CyberShield', industry: 'Software & Technology', location: 'Germany', revenue: '$10M - $25M', employeeCount: '201-500' },
  { name: 'MedTech Plus', industry: 'Healthcare & Medical', location: 'Australia', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'WealthWise', industry: 'Financial Services', location: 'United States', revenue: '$100M+', employeeCount: '1001-5000' },
  { name: 'QuickCommerce', industry: 'E-commerce & Retail', location: 'India', revenue: '$2M - $5M', employeeCount: '51-200' },
  { name: 'SteelForge', industry: 'Manufacturing', location: 'Germany', revenue: '$50M - $100M', employeeCount: '1001-5000' },
  { name: 'SkillUp Academy', industry: 'Education', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
  { name: 'StreamNow', industry: 'Media & Entertainment', location: 'United States', revenue: '$25M - $50M', employeeCount: '201-500' },
  { name: 'AdvisoryPro', industry: 'Professional Services', location: 'United Kingdom', revenue: '$2M - $5M', employeeCount: '11-50' },
  { name: 'CloudNine Tech', industry: 'Software & Technology', location: 'United States', revenue: '$25M - $50M', employeeCount: '201-500' },
  { name: 'PharmaCare', industry: 'Healthcare & Medical', location: 'Germany', revenue: '$100M+', employeeCount: '5000+' },
  { name: 'InsureMax', industry: 'Financial Services', location: 'Australia', revenue: '$50M - $100M', employeeCount: '501-1000' },
  { name: 'FashionFirst', industry: 'E-commerce & Retail', location: 'United Kingdom', revenue: '$10M - $25M', employeeCount: '201-500' },
  { name: 'AutoParts Global', industry: 'Manufacturing', location: 'United States', revenue: '$100M+', employeeCount: '5000+' },
  { name: 'CodeCamp', industry: 'Education', location: 'India', revenue: '$1M - $2M', employeeCount: '11-50' },
  { name: 'GameStudio X', industry: 'Media & Entertainment', location: 'United States', revenue: '$10M - $25M', employeeCount: '51-200' },
  { name: 'TaxPro Services', industry: 'Professional Services', location: 'United States', revenue: '$5M - $10M', employeeCount: '51-200' },
];

function matchesFilters(company: BaseCompany, filters: Pick<CampaignFilters, 'industry' | 'region' | 'employeeCount'>): boolean {
  const industryMatch = filters.industry.length === 0 || filters.industry.some((i) => company.industry.includes(i));
  const regionMatch =
    filters.region.length === 0 ||
    filters.region.some((r) => company.location.includes(r) || r.includes(company.location));
  const employeeMatch = filters.employeeCount.length === 0 || filters.employeeCount.includes(company.employeeCount);
  return industryMatch && regionMatch && employeeMatch;
}

function stableHash(input: string): number {
  // Simple deterministic hash (djb2)
  let hash = 5381;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 33) ^ input.charCodeAt(i);
  }
  // force positive 32-bit
  return hash >>> 0;
}

function pickFrom<T>(arr: T[], seed: number): T {
  return arr[seed % arr.length]!;
}

export function getMockProspects(filters: Pick<CampaignFilters, 'industry' | 'region' | 'employeeCount'>): Prospect[] {
  // Expand base set to give enough items for pagination testing
  const prefixes = ['Global', 'Premier', 'Elite', 'Prime'];
  const expanded: BaseCompany[] = [
    ...BASE_COMPANIES,
    ...prefixes.flatMap((prefix) => BASE_COMPANIES.slice(0, 10).map((c) => ({ ...c, name: `${prefix} ${c.name}` }))),
  ];

  return expanded
    .filter((c) => matchesFilters(c, filters))
    .map((c, index) => ({
      id: `prospect-${index + 1}`,
      name: c.name,
      industry: c.industry,
      employeeCount: c.employeeCount,
      revenue: c.revenue,
      location: c.location,
      website: `https://${c.name.toLowerCase().replace(/\s+/g, '')}.com`,
      linkedinUrl: `https://linkedin.com/company/${c.name.toLowerCase().replace(/\s+/g, '-')}`,
      isQualified: undefined,
      qualificationStatus: 'pending',
    }));
}

export function getMockContacts(companyId: string, companyName: string): Contact[] {
  const titles = ['CEO', 'CTO', 'VP of Sales', 'Head of Marketing', 'Director of Operations'];
  const firstNames = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Priya', 'Arjun', 'Sophia'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Davis', 'Patel', 'Sharma', 'Miller'];

  const seed = stableHash(`${companyId}:${companyName}`);
  const numContacts = 3 + (seed % 3); // 3-5, deterministic

  return Array.from({ length: numContacts }, (_, i) => {
    const fn = pickFrom(firstNames, seed + i * 7);
    const ln = pickFrom(lastNames, seed + i * 11);
    const title = pickFrom(titles, seed + i * 13);
    const domain = companyName.toLowerCase().replace(/\s+/g, '');

    return {
      id: `${companyId}-contact-${i + 1}`,
      companyId,
      firstName: fn,
      lastName: ln,
      email: `${fn.toLowerCase()}.${ln.toLowerCase()}@${domain}.com`,
      phone: `+1-555-${String(1000 + ((seed + i * 17) % 9000)).padStart(4, '0')}`,
      jobTitle: title,
      linkedinUrl: `https://linkedin.com/in/${fn.toLowerCase()}${ln.toLowerCase()}`,
      isSynced: false,
    };
  });
}

export const MOCK_LEMLIST_SEQUENCES = [
  {
    id: 'seq-1',
    name: 'Enterprise Outreach - Q1 2025',
    description: 'Multi-touch sequence for enterprise prospects with personalized follow-ups',
    steps: 5,
    avgOpenRate: 42,
    avgReplyRate: 8,
  },
  {
    id: 'seq-2',
    name: 'SMB Cold Outreach',
    description: 'Quick and direct sequence for small and medium businesses',
    steps: 3,
    avgOpenRate: 38,
    avgReplyRate: 12,
  },
  {
    id: 'seq-3',
    name: 'Healthcare Decision Makers',
    description: 'Tailored sequence for healthcare industry executives',
    steps: 4,
    avgOpenRate: 35,
    avgReplyRate: 6,
  },
  {
    id: 'seq-4',
    name: 'Tech Founders Sequence',
    description: 'Casual, founder-to-founder outreach for tech startups',
    steps: 4,
    avgOpenRate: 45,
    avgReplyRate: 15,
  },
  {
    id: 'seq-5',
    name: 'Re-engagement Campaign',
    description: 'Win-back sequence for previously contacted prospects',
    steps: 3,
    avgOpenRate: 28,
    avgReplyRate: 5,
  },
];


