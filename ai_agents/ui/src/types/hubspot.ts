// HubSpot Module Types

// ============ Company Types ============
export interface CompanyEnrichment {
  companyName: string;
  legalEntityName: string;
  industry?: string;
  employeeBand?: string;
  hqLocation?: string;
  registeredAddress?: string;
  website?: string;
  linkedIn?: string;
  confidence: Record<string, 'high' | 'medium' | 'low'>;
}

export interface HubSpotCompany {
  id: string;
  name: string;
  domain?: string;
  legalEntityName?: string;
  ownerEmail?: string;
}

export interface CompanyDraft {
  url: string;
  canonicalDomain: string;
  ownerEmail: string;
  enriched?: CompanyEnrichment;
  matchResults?: HubSpotCompany[];
  decision?: 'link' | 'create';
  selectedExistingCompanyId?: string;
}

// ============ Contact Types ============
export interface ContactEnrichment {
  phone?: string;
  linkedIn?: string;
  title?: string;
  department?: string;
  confidence: Record<string, 'high' | 'medium' | 'low'>;
}

export interface HubSpotContact {
  id: string;
  name: string;
  email: string;
  phone?: string;
}

export interface ContactDraft {
  firstName: string;
  lastName: string;
  email: string;
  associateType: 'company' | 'deal';
  associateId: string;
  enriched?: ContactEnrichment;
  matchResults?: HubSpotContact[];
  decision?: 'link' | 'create';
  selectedExistingContactId?: string;
}

// ============ Deal Types ============
export interface HubSpotDeal {
  id: string;
  name: string;
  companyId: string;
  product: string;
  stage: string;
  amount?: number;
}

export interface DealDraft {
  product: string;
  companyId: string;
  contactIds: string[];
  ownerEmail?: string;
  matchResults?: HubSpotDeal[];
  decision?: 'link' | 'create';
  selectedExistingDealId?: string;
  stage?: string;
  amount?: number;
}

// ============ Wizard Types ============
export type WizardStep = 'input' | 'match' | 'enrich' | 'review' | 'done';

export interface WizardState<T> {
  currentStep: WizardStep;
  draft: T;
  isLoading: boolean;
  error: string | null;
  result?: HubSpotCompany | HubSpotContact | HubSpotDeal;
}

// ============ Mock Data Types ============
export interface MockProduct {
  id: string;
  name: string;
}

export interface MockStage {
  id: string;
  name: string;
}

