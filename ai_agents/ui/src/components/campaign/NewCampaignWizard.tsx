import React, { useState, createContext, useContext, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useLazyGetCampaignDetailsQuery, useLazyCompanyQualificationProgressQuery, useLazyContactQualificationProgressQuery } from '../../store';
import './CampaignWizard.css';
import { useSidebar } from '../../context/SidebarContext';
import { CampaignTypeSelection, type CampaignType } from './CampaignTypeSelection';
import { ProductSelection, type ProductSelectionMode } from './ProductSelection';
import { Step1Prospecting } from './Step1Prospecting';
import { Step1ImportCSV } from './Step1ImportCSV';
import { Step1SingleCompany } from './Step1SingleCompany';
import { Step1SimilarCompanies } from './Step1SimilarCompanies';
import { Step1NLFilter } from './Step1NLFilter';
// StepCompanyEnrichment is no longer used - enrichment happens in Kafka during backend processing
// import { StepCompanyEnrichment } from './StepCompanyEnrichment';
import { Step2CompanyQualification } from './Step2CompanyQualification';
import { Step3ContactQualification } from './Step3ContactQualification';
import { Step4SyncHubspot } from './Step4SyncHubspot';
import { Step5Personalization } from './Step5Personalization';
import { Step6EnrollOutreach } from './Step6EnrollOutreach';
import { CampaignComplete } from './CampaignComplete';

// Types for the campaign wizard
export interface Prospect {
  id: string;
  name: string;
  industry: string;
  employeeCount: string;
  revenue: string;
  location: string;
  website: string;
  linkedinUrl?: string;
  isQualified?: boolean;
  qualificationStatus?: 'pending' | 'qualified' | 'rejected';
}

export interface Contact {
  id: string;
  companyId: string;
  companyName?: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  jobTitle: string;
  linkedinUrl?: string;
  isSynced?: boolean;
  qualificationStatus?: 'pending' | 'qualified' | 'rejected';
  aiRejectionReason?: string;
  syncStatus?: 'not_synced' | 'selected' | 'syncing' | 'synced' | 'failed';
  personalization?: {
    messageStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    message?: string;
    deckStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    deckUrl?: string;
    isSelected?: boolean;
  };
}

export interface Company extends Prospect {
  contacts: Contact[];
  syncStatus: 'not_synced' | 'selected' | 'syncing' | 'synced' | 'failed';
  personalization?: {
    messageStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    deckStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    message?: string;
    deckUrl?: string;
    isSelected?: boolean;
  };
}

export interface CampaignFilters {
  industry: string[];
  region: string[];
  employeeCount: string[];
  revenueMin: string;
  revenueMax: string;
  currency: string;
  locationType: string;
  productName: string;
}

export interface CampaignState {
  // New fields for multi-funnel support
  campaignType: CampaignType | null;
  productSelectionMode: ProductSelectionMode | null;
  selectedProducts: string[];
  skipCompanyQualification: boolean;
  wizardPhase: 'type_selection' | 'product_selection' | 'steps';
  
  // Campaign name (required, unique)
  campaignName: string;
  
  // Existing fields
  currentStep: number;
  // Highest step reached for this campaign in the wizard UI.
  // Used so that clicking back to an earlier step doesn't "lock" later completed steps.
  maxStepReached: number;
  filters: CampaignFilters;
  campaignId: string | null;
  prospects: Prospect[];
  qualifiedCompanies: Company[];
  qualifiedContacts: Contact[];
  companyQualificationMode: 'manual' | 'ai' | null;
  contactQualificationMode: 'manual' | 'ai' | null;
  aiQuestions: string[];
  contactAiQuestions: string[];
  selectedSequence: string | null;
  isLoading: boolean;
  loadingMessage: string;
  estimatedCount: number;
}

interface CampaignContextType {
  state: CampaignState;
  setFilters: (filters: CampaignFilters) => void;
  setCampaignId: (campaignId: string | null) => void;
  setCampaignName: (name: string) => void;
  setProspects: (prospects: Prospect[]) => void;
  setQualifiedCompanies: (companies: Company[]) => void;
  setQualifiedContacts: (contacts: Contact[]) => void;
  setCompanyQualificationMode: (mode: 'manual' | 'ai' | null) => void;
  setContactQualificationMode: (mode: 'manual' | 'ai' | null) => void;
  qualifyCompany: (companyId: string, qualified: boolean) => void;
  bulkQualify: (companyIds: string[], qualified: boolean) => void;
  qualifyContact: (contactId: string, qualified: boolean) => void;
  bulkQualifyContacts: (contactIds: string[], qualified: boolean) => void;
  syncContact: (contactId: string) => void;
  bulkSyncContacts: (contactIds: string[]) => void;
  generateContactPersonalization: (contactId: string) => void;
  bulkGenerateContactPersonalization: (contactIds: string[]) => void;
  regenerateMessageOnly: (contactId: string) => void;
  approveContactPersonalization: (contactId: string) => void;
  rejectContactPersonalization: (contactId: string) => void;
  approveDeck: (contactId: string) => void;
  rejectDeck: (contactId: string) => void;
  updateDeckUrl: (contactId: string, url: string) => void;
  replaceWithDefaultDeck: (contactId: string) => void;
  setSelectedSequence: (sequenceId: string) => void;
  enrollToSequence: (contactIds: string[]) => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;
  setLoading: (loading: boolean, message?: string, estimatedCount?: number) => void;
  setSkipCompanyQualification: (skip: boolean) => void;
  getStepsForCampaignType: () => StepConfig[];
  getCurrentStepInfo: () => StepConfig | undefined;
}

const CampaignContext = createContext<CampaignContextType | null>(null);

export const useCampaignWizard = () => {
  const context = useContext(CampaignContext);
  if (!context) {
    throw new Error('useCampaignWizard must be used within NewCampaignWizard');
  }
  return context;
};

// Step configuration based on campaign type
interface StepConfig {
  id: string;
  stepNumber: number;
  title: string;
  component: React.FC;
}

// Get steps based on campaign type
const getStepsForType = (
  campaignType: CampaignType | null,
  skipCompanyQual: boolean
): StepConfig[] => {
  if (!campaignType) return [];

  const commonStepsAfterQualification: StepConfig[] = [
    { id: 'contact-qualification', stepNumber: 0, title: 'Contact Qualification', component: Step3ContactQualification },
    { id: 'sync-hubspot', stepNumber: 0, title: 'Sync to Hubspot', component: Step4SyncHubspot },
    { id: 'personalization', stepNumber: 0, title: 'Personalization', component: Step5Personalization },
    { id: 'enroll-outreach', stepNumber: 0, title: 'Enroll for Outreach', component: Step6EnrollOutreach },
  ];

  // enrichmentStep removed - all campaign types now do enrichment in Kafka backend

  const companyQualStep: StepConfig = {
    id: 'company-qualification',
    stepNumber: 0,
    title: 'Company Qualification',
    component: Step2CompanyQualification,
  };

  let steps: StepConfig[] = [];

  switch (campaignType) {
    case 'import_csv':
      // CSV import skips enrichment step - Apollo enrichment is done in Kafka handler during import
      steps = [
        { id: 'import', stepNumber: 1, title: 'Import Companies', component: Step1ImportCSV },
        // No enrichment step - companies are enriched via Apollo during import
        ...(skipCompanyQual ? [] : [companyQualStep]),
        ...commonStepsAfterQualification,
      ];
      break;

    case 'single_company':
      // Single company skips both enrichment AND company qualification
      // Company data comes from Apollo domain search, then goes directly to Contact Qualification
      steps = [
        { id: 'company-input', stepNumber: 1, title: 'Company Input', component: Step1SingleCompany },
        // No enrichment step - company data from Apollo
        // No company qualification - already qualified by user selecting the URL
        ...commonStepsAfterQualification,
      ];
      break;

    case 'wide_prospecting':
      // Wide prospecting does NOT need enrichment step - companies come pre-enriched from Apollo
      steps = [
        { id: 'prospecting', stepNumber: 1, title: 'Lead Generation', component: Step1Prospecting },
        companyQualStep,
        ...commonStepsAfterQualification,
      ];
      break;

    case 'similar_companies':
      // Similar companies skips enrichment step - Apollo enrichment is done in Kafka handler (same as CSV import)
      steps = [
        { id: 'similar-search', stepNumber: 1, title: 'Find Similar', component: Step1SimilarCompanies },
        // No enrichment step - companies are enriched via Apollo during backend processing
        ...(skipCompanyQual ? [] : [companyQualStep]),
        ...commonStepsAfterQualification,
      ];
      break;

    case 'nl_filter':
      // NL Filter skips enrichment step - Apollo enrichment is done in Kafka handler (same as CSV import)
      steps = [
        { id: 'nl-search', stepNumber: 1, title: 'Natural Language Search', component: Step1NLFilter },
        // No enrichment step - companies are enriched via Apollo during backend processing
        ...(skipCompanyQual ? [] : [companyQualStep]),
        ...commonStepsAfterQualification,
      ];
      break;

    default:
      return [];
  }

  // Renumber steps
  return steps.map((step, index) => ({
    ...step,
    stepNumber: index + 1,
  }));
};

// Default deck URL - used when user wants to replace AI-generated deck with default
const DEFAULT_DECK_URL = 'https://decks.example.com/default/standard-company-deck.pdf';
const WIZARD_SESSION_KEY = 'agent_hub_campaign_wizard_session_v1';

// Derive wizard step from prospecting_cycle.status (ONLY - lifecycle.status is ignored)
const deriveStepFromCycleStatus = (cycleStatus?: string): number => {
  // Step 6: Enrollment complete or ready for enrollment
  if (cycleStatus === 'enrolled_to_sequence') return 6;
  if (cycleStatus === 'personalization_completed') return 6;
  
  // Step 5: Personalization
  if (cycleStatus === 'hubspot_sync_completed') return 5;
  
  // Step 4: HubSpot Sync
  if (cycleStatus === 'hubspot_sync_in_progress') return 4;
  if (cycleStatus === 'hubspot_sync_failed') return 4;
  if (cycleStatus === 'contact_enriched') return 4;
  
  // Step 3: Contact Qualification (all contact_qualification_* statuses)
  if (cycleStatus === 'contact_qualification') return 3;
  if (cycleStatus === 'contact_qualification_select') return 3;
  if (cycleStatus === 'contact_qualification_ai_started') return 3;
  
  // Step 2: Company Qualification (all company_qualification_* statuses)
  if (cycleStatus === 'company_qualification') return 2;
  if (cycleStatus === 'company_qualification_select') return 2;
  if (cycleStatus === 'company_qualification_ai_started') return 2;
  
  // Step 1: Prospecting
  if (cycleStatus === 'prospecting') return 1;
  
  return 1; // Default to step 1
};

// Derive company qualification mode from status
const deriveCompanyQualificationMode = (cycleStatus?: string): 'manual' | 'ai' | null => {
  if (cycleStatus === 'company_qualification_select') return null; // Show mode selection
  if (cycleStatus === 'company_qualification_ai_started') return 'ai'; // AI in progress
  if (cycleStatus === 'company_qualification') return null; // Could be manual or AI completed - check AI progress
  return null;
};

// Derive contact qualification mode from status
const deriveContactQualificationMode = (cycleStatus?: string): 'manual' | 'ai' | null => {
  if (cycleStatus === 'contact_qualification_select') return null; // Show mode selection
  if (cycleStatus === 'contact_qualification_ai_started') return 'ai'; // AI in progress
  if (cycleStatus === 'contact_qualification') return null; // Could be manual or AI completed - check AI progress
  return null;
};

// Campaign type labels for display
const CAMPAIGN_TYPE_LABELS: Record<CampaignType, string> = {
  import_csv: 'Import Company List',
  single_company: 'Single Company URL',
  wide_prospecting: 'Wide Prospecting',
  similar_companies: 'Similar Companies',
  nl_filter: 'Natural Language Filter',
};

export const NewCampaignWizard = () => {
  const location = useLocation();
  const [fetchCampaignDetails] = useLazyGetCampaignDetailsQuery();
  const [fetchCompanyQualificationProgress] = useLazyCompanyQualificationProgressQuery();
  const [fetchContactQualificationProgress] = useLazyContactQualificationProgressQuery();
  
  // Check if we're resuming an existing campaign (has campaign_id in URL)
  const urlCampaignId = new URLSearchParams(location.search).get('campaign_id');
  const isResumingCampaign = !!urlCampaignId;
  
  // Track campaign name validation state
  const [isCampaignNameValid, setIsCampaignNameValid] = useState(false);
  
  const { setWizardProgress, clearWizardProgress } = useSidebar();
  const [state, setState] = useState<CampaignState>({
    // New fields
    campaignType: null,
    productSelectionMode: null,
    selectedProducts: [],
    skipCompanyQualification: false,
    wizardPhase: 'type_selection',
    
    // Campaign name (required, unique)
    campaignName: '',
    
    // Existing fields
    currentStep: 1,
    maxStepReached: 1,
    filters: {
      industry: [],
      region: [],
      employeeCount: [],
      revenueMin: '',
      revenueMax: '',
      currency: 'USD',
      locationType: 'country',
      productName: '',
    },
    campaignId: null,
    prospects: [],
    qualifiedCompanies: [],
    qualifiedContacts: [],
    companyQualificationMode: null,
    contactQualificationMode: null,
    aiQuestions: [],
    contactAiQuestions: [],
    selectedSequence: null,
    isLoading: false,
    loadingMessage: '',
    estimatedCount: 0,
  });

  const [isComplete, setIsComplete] = useState(false);

  // Restore wizard progress (campaignId + step) on refresh - ONLY when resuming a campaign.
  // When creating a NEW campaign (no campaign_id in URL), start fresh.
  useEffect(() => {
    try {
      // If NOT resuming a campaign (no campaign_id in URL), clear session storage and start fresh
      if (!isResumingCampaign) {
        window.sessionStorage.removeItem(WIZARD_SESSION_KEY);
        return;
      }
      
      const raw = window.sessionStorage.getItem(WIZARD_SESSION_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as
        | { campaignId?: string | null; currentStep?: number; maxStepReached?: number }
        | null;
      if (!parsed) return;

      // Only restore if the saved campaignId matches the URL campaign_id
      const MAX_STEPS = 6; // Maximum possible steps in the wizard
      if (parsed.campaignId === urlCampaignId && !state.campaignId) {
        setState((prev) => ({
          ...prev,
          campaignId: parsed.campaignId || null,
          currentStep:
            typeof parsed.currentStep === 'number' && parsed.currentStep >= 1 && parsed.currentStep <= MAX_STEPS
              ? parsed.currentStep
              : prev.currentStep,
          maxStepReached:
            typeof parsed.maxStepReached === 'number' &&
            parsed.maxStepReached >= 1 &&
            parsed.maxStepReached <= MAX_STEPS
              ? parsed.maxStepReached
              : typeof parsed.currentStep === 'number' &&
                  parsed.currentStep >= 1 &&
                  parsed.currentStep <= MAX_STEPS
                ? parsed.currentStep
                : prev.maxStepReached,
        }));
      }
    } catch {
      // ignore storage corruption
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isResumingCampaign, urlCampaignId]);

  // When resuming a campaign, fetch its details and derive the correct step from prospecting_cycle.status
  // ALSO check AI qualification status for both company and contact to avoid skipping review
  useEffect(() => {
    if (!isResumingCampaign || !urlCampaignId) return;
    
    let cancelled = false;
    const fetchAndSetStep = async () => {
      try {
        // Fetch campaign details and AI qualification progress (both company and contact) in parallel
        const [campaignRes, companyAiProgressRes, contactAiProgressRes] = await Promise.all([
          fetchCampaignDetails({ campaign_id: urlCampaignId, page: 1, limit: 1 }).unwrap(),
          fetchCompanyQualificationProgress({ campaign_id: urlCampaignId }).unwrap().catch(() => null),
          fetchContactQualificationProgress({ campaign_id: urlCampaignId }).unwrap().catch(() => null),
        ]);
        
        if (cancelled) return;
        
        const campaign = campaignRes?.data?.campaign;
        const cycleStatus = campaign?.prospecting_cycle?.status;
        const derivedStep = deriveStepFromCycleStatus(cycleStatus);
        
        // Derive qualification modes from backend status (primary source of truth)
        let derivedCompanyMode = deriveCompanyQualificationMode(cycleStatus);
        let derivedContactMode = deriveContactQualificationMode(cycleStatus);
        
        // Check AI job status for additional context (for completed AI jobs)
        const companyAiJobStatus = companyAiProgressRes?.data?.status;
        const contactAiJobStatus = contactAiProgressRes?.data?.status;
        
        // If status is 'company_qualification' and AI job completed, set AI mode for review
        if (cycleStatus === 'company_qualification' && companyAiJobStatus === 'completed') {
          derivedCompanyMode = 'ai';
        }
        
        // If status is 'contact_qualification' and AI job completed, set AI mode for review
        if (cycleStatus === 'contact_qualification' && contactAiJobStatus === 'completed') {
          derivedContactMode = 'ai';
        }
        
        // If AI is actively running (status shows _ai_started), ensure AI mode
        if (cycleStatus === 'company_qualification_ai_started') {
          derivedCompanyMode = 'ai';
        }
        if (cycleStatus === 'contact_qualification_ai_started') {
          derivedContactMode = 'ai';
        }
        
        // Derive campaign type from campaign data
        let derivedCampaignType: CampaignType = 'wide_prospecting'; // Default for prospecting campaigns
        
        console.log('[Resume] cycleStatus:', cycleStatus, 'derivedStep:', derivedStep, 
          'companyMode:', derivedCompanyMode, 'contactMode:', derivedContactMode);
        
        setState((prev) => ({
          ...prev,
          campaignId: urlCampaignId,
          campaignType: derivedCampaignType,
          wizardPhase: 'steps', // IMPORTANT: Set to 'steps' so wizard renders the actual steps
          currentStep: derivedStep,
          maxStepReached: Math.max(prev.maxStepReached, derivedStep),
          companyQualificationMode: derivedCompanyMode,
          contactQualificationMode: derivedContactMode,
        }));
      } catch (err) {
        // If fetch fails, still set the campaignId but stay on step 1
        if (!cancelled) {
          setState((prev) => ({
            ...prev,
            campaignId: urlCampaignId,
            campaignType: 'wide_prospecting',
            wizardPhase: 'steps',
          }));
        }
      }
    };
    
    void fetchAndSetStep();
    
    return () => {
      cancelled = true;
    };
  }, [isResumingCampaign, urlCampaignId, fetchCampaignDetails, fetchCompanyQualificationProgress, fetchContactQualificationProgress]);

  // Persist wizard progress (minimal) so refresh doesn't reset to step 1.
  useEffect(() => {
    try {
      window.sessionStorage.setItem(
        WIZARD_SESSION_KEY,
        JSON.stringify({
          campaignId: state.campaignId,
          currentStep: state.currentStep,
          maxStepReached: state.maxStepReached,
        })
      );
    } catch {
      // ignore storage failures
    }
  }, [state.campaignId, state.currentStep, state.maxStepReached]);

  // Get current steps based on campaign type
  const currentSteps = getStepsForType(state.campaignType, state.skipCompanyQualification);

  // Scroll to top on mount and when step changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [state.currentStep, state.wizardPhase]);

  // Sync wizard progress with sidebar
  useEffect(() => {
    if (state.wizardPhase === 'steps' && currentSteps.length > 0) {
      setWizardProgress({
        isActive: true,
        campaignType: state.campaignType,
        currentStep: state.currentStep,
        totalSteps: currentSteps.length,
        steps: currentSteps.map(s => ({ id: s.id, title: s.title, stepNumber: s.stepNumber })),
      });
    } else if (state.wizardPhase !== 'steps') {
      setWizardProgress({
        isActive: true,
        campaignType: state.campaignType,
        currentStep: 0,
        totalSteps: 0,
        steps: [],
      });
    }

    // Clear wizard progress when component unmounts
    return () => {
      clearWizardProgress();
    };
  }, [state.wizardPhase, state.currentStep, state.campaignType, currentSteps, setWizardProgress, clearWizardProgress]);

  // Handle campaign type selection
  const handleTypeSelect = (type: CampaignType) => {
    // Only allow type selection if campaign name is valid
    if (!isCampaignNameValid) {
      // Just set the type but don't proceed to next phase
      setState(prev => ({
        ...prev,
        campaignType: type,
      }));
      return;
    }
    
    setState(prev => ({
      ...prev,
      campaignType: type,
      wizardPhase: 'product_selection',
    }));
  };

  // Handle product selection completion
  const handleProductComplete = (mode: ProductSelectionMode, products: string[]) => {
    setState(prev => ({
      ...prev,
      productSelectionMode: mode,
      selectedProducts: products,
      wizardPhase: 'steps',
      currentStep: 1,
    }));
  };

  // Go back to type selection
  const handleBackToTypeSelection = () => {
    setState(prev => ({
      ...prev,
      wizardPhase: 'type_selection',
      campaignType: null,
    }));
  };

  const setFilters = useCallback((filters: CampaignFilters) => {
    setState(prev => ({ ...prev, filters }));
  }, []);

  const setCampaignId = useCallback((campaignId: string | null) => {
    setState(prev => ({ ...prev, campaignId }));
  }, []);

  const setCampaignName = useCallback((name: string) => {
    setState(prev => ({ ...prev, campaignName: name }));
  }, []);

  const setProspects = useCallback((prospects: Prospect[]) => {
    setState(prev => ({ ...prev, prospects }));
  }, []);

  const setQualifiedCompanies = useCallback((companies: Company[]) => {
    setState(prev => ({ ...prev, qualifiedCompanies: companies }));
  }, []);

  const setQualifiedContacts = useCallback((contacts: Contact[]) => {
    setState(prev => ({ ...prev, qualifiedContacts: contacts }));
  }, []);

  const setCompanyQualificationMode = useCallback((mode: 'manual' | 'ai' | null) => {
    setState(prev => ({ ...prev, companyQualificationMode: mode }));
  }, []);

  const setContactQualificationMode = useCallback((mode: 'manual' | 'ai' | null) => {
    setState(prev => ({ ...prev, contactQualificationMode: mode }));
  }, []);

  const setSkipCompanyQualification = useCallback((skip: boolean) => {
    setState(prev => ({ ...prev, skipCompanyQualification: skip }));
  }, []);

  const qualifyCompany = useCallback((companyId: string, qualified: boolean) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        c.id === companyId
          ? { ...c, isQualified: qualified, qualificationStatus: qualified ? 'qualified' : 'rejected' }
          : c
      ),
    }));
  }, []);

  const bulkQualify = useCallback((companyIds: string[], qualified: boolean) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        companyIds.includes(c.id)
          ? { ...c, isQualified: qualified, qualificationStatus: qualified ? 'qualified' : 'rejected' }
          : c
      ),
    }));
  }, []);

  const qualifyContact = useCallback((contactId: string, qualified: boolean) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? { ...c, qualificationStatus: qualified ? 'qualified' : 'rejected' }
          : c
      ),
    }));
  }, []);

  const bulkQualifyContacts = useCallback((contactIds: string[], qualified: boolean) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        contactIds.includes(c.id)
          ? { ...c, qualificationStatus: qualified ? 'qualified' : 'rejected' }
          : c
      ),
    }));
  }, []);

  const syncContact = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId ? { ...c, syncStatus: 'syncing' } : c
      ),
    }));
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        qualifiedContacts: prev.qualifiedContacts.map(c =>
          c.id === contactId ? { ...c, syncStatus: 'synced' } : c
        ),
      }));
    }, 1500);
  }, []);

  const bulkSyncContacts = useCallback((contactIds: string[]) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        contactIds.includes(c.id) ? { ...c, syncStatus: 'syncing' } : c
      ),
    }));
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        qualifiedContacts: prev.qualifiedContacts.map(c =>
          contactIds.includes(c.id) ? { ...c, syncStatus: 'synced' } : c
        ),
      }));
    }, 2000);
  }, []);

  const generateContactPersonalization = useCallback((contactId: string) => {
    setState(prev => {
      return {
        ...prev,
        qualifiedContacts: prev.qualifiedContacts.map(c =>
          c.id === contactId
            ? {
                ...c,
                personalization: {
                  ...c.personalization,
                  messageStatus: 'generating',
                  deckStatus: 'generating',
                } as Contact['personalization'],
              }
            : c
        ),
      };
    });
    // Simulate generation
    setTimeout(() => {
      setState(prev => {
        const contact = prev.qualifiedContacts.find(c => c.id === contactId);
        const company = prev.qualifiedCompanies.find(comp => comp.id === contact?.companyId);
        return {
          ...prev,
          qualifiedContacts: prev.qualifiedContacts.map(c =>
            c.id === contactId
              ? {
                  ...c,
                  personalization: {
                    ...c.personalization,
                    messageStatus: 'generated',
                    message: `Hi ${c.firstName},\n\nI noticed ${company?.name || 'your company'} is doing great work in ${company?.industry || 'your industry'}. As ${c.jobTitle}, I thought you might be interested in how we help companies like yours achieve 3x better results.\n\nWould love to schedule a quick call to discuss how we can help.\n\nBest regards`,
                    deckStatus: 'generated',
                    deckUrl: `https://decks.example.com/personalized/${c.id}/${company?.name?.toLowerCase().replace(/\s+/g, '-') || 'company'}-deck.pdf`,
                  },
                }
              : c
          ),
        };
      });
    }, 3000);
  }, []);

  const bulkGenerateContactPersonalization = useCallback((contactIds: string[]) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        contactIds.includes(c.id)
          ? {
              ...c,
              personalization: {
                ...c.personalization,
                messageStatus: 'generating',
                deckStatus: 'generating',
              } as Contact['personalization'],
            }
          : c
      ),
    }));
    // Simulate bulk generation with staggered completion
    contactIds.forEach((id, index) => {
      setTimeout(() => {
        setState(prev => {
          const contact = prev.qualifiedContacts.find(c => c.id === id);
          const company = prev.qualifiedCompanies.find(comp => comp.id === contact?.companyId);
          return {
            ...prev,
            qualifiedContacts: prev.qualifiedContacts.map(c =>
              c.id === id
                ? {
                    ...c,
                    personalization: {
                      ...c.personalization,
                      messageStatus: 'generated',
                      message: `Hi ${c.firstName},\n\nI noticed ${company?.name || 'your company'} is doing great work in ${company?.industry || 'your industry'}. As ${c.jobTitle}, I thought you might be interested in how we help companies like yours achieve 3x better results.\n\nWould love to schedule a quick call to discuss how we can help.\n\nBest regards`,
                      deckStatus: 'generated',
                      deckUrl: `https://decks.example.com/personalized/${c.id}/${company?.name?.toLowerCase().replace(/\s+/g, '-') || 'company'}-deck.pdf`,
                    },
                  }
                : c
            ),
          };
        });
      }, 2000 + index * 500);
    });
  }, []);

  // Regenerate only the message (not the deck)
  const regenerateMessageOnly = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                messageStatus: 'generating',
                // Keep deck status and URL unchanged
              },
            }
          : c
      ),
    }));
    // Simulate message regeneration
    setTimeout(() => {
      setState(prev => {
        const contact = prev.qualifiedContacts.find(c => c.id === contactId);
        const company = prev.qualifiedCompanies.find(comp => comp.id === contact?.companyId);
        return {
          ...prev,
          qualifiedContacts: prev.qualifiedContacts.map(c =>
            c.id === contactId
              ? {
                  ...c,
                  personalization: {
                    ...c.personalization!,
                    messageStatus: 'generated',
                    message: `Hi ${c.firstName},\n\nI came across ${company?.name || 'your company'} and was impressed by your work in ${company?.industry || 'your industry'}. As ${c.jobTitle}, you might find our solution particularly valuable for achieving better outcomes.\n\nI'd love to connect and share how we've helped similar companies succeed.\n\nLooking forward to hearing from you!`,
                    // Deck remains unchanged
                  },
                }
              : c
          ),
        };
      });
    }, 2500);
  }, []);

  const approveContactPersonalization = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                messageStatus: 'approved',
              },
            }
          : c
      ),
    }));
  }, []);

  const rejectContactPersonalization = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                messageStatus: 'rejected',
              },
            }
          : c
      ),
    }));
  }, []);

  const approveDeck = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                deckStatus: 'approved',
              },
            }
          : c
      ),
    }));
  }, []);

  const rejectDeck = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                deckStatus: 'rejected',
              },
            }
          : c
      ),
    }));
  }, []);

  const updateDeckUrl = useCallback((contactId: string, url: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                deckUrl: url,
                deckStatus: 'generated', // Reset to generated when URL is manually updated
              },
            }
          : c
      ),
    }));
  }, []);

  const replaceWithDefaultDeck = useCallback((contactId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedContacts: prev.qualifiedContacts.map(c =>
        c.id === contactId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                deckUrl: DEFAULT_DECK_URL,
                deckStatus: 'generated', // Reset to generated when replaced with default
              },
            }
          : c
      ),
    }));
  }, []);

  const setSelectedSequence = useCallback((sequenceId: string) => {
    setState(prev => ({ ...prev, selectedSequence: sequenceId }));
  }, []);

  const enrollToSequence = useCallback((_contactIds: string[]) => {
    // Simulate enrollment
    setState(prev => ({ ...prev, isLoading: true, loadingMessage: 'Enrolling contacts to sequence...' }));
    setTimeout(() => {
      setState(prev => ({ ...prev, isLoading: false }));
      setIsComplete(true);
    }, 2000);
  }, []);

  const nextStep = useCallback(() => {
    setState(prev => {
      const next = Math.min(prev.currentStep + 1, 6);
      return { ...prev, currentStep: next, maxStepReached: Math.max(prev.maxStepReached, next) };
    });
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) }));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step < 1 || step > 6) return;
    setState(prev => {
      if (step > prev.maxStepReached) return prev;
      return { ...prev, currentStep: step };
    });
  }, []);

  const setLoading = useCallback((loading: boolean, message = '', estimatedCount = 0) => {
    setState(prev => ({ ...prev, isLoading: loading, loadingMessage: message, estimatedCount }));
  }, []);

  const getStepsForCampaignType = useCallback(() => {
    return currentSteps;
  }, [currentSteps]);

  const getCurrentStepInfo = useCallback(() => {
    return currentSteps.find(s => s.stepNumber === state.currentStep);
  }, [currentSteps, state.currentStep]);

  const contextValue: CampaignContextType = {
    state,
    setFilters,
    setCampaignId,
    setCampaignName,
    setProspects,
    setQualifiedCompanies,
    setQualifiedContacts,
    setCompanyQualificationMode,
    setContactQualificationMode,
    qualifyCompany,
    bulkQualify,
    qualifyContact,
    bulkQualifyContacts,
    syncContact,
    bulkSyncContacts,
    generateContactPersonalization,
    bulkGenerateContactPersonalization,
    regenerateMessageOnly,
    approveContactPersonalization,
    rejectContactPersonalization,
    approveDeck,
    rejectDeck,
    updateDeckUrl,
    replaceWithDefaultDeck,
    setSelectedSequence,
    enrollToSequence,
    nextStep,
    prevStep,
    goToStep,
    setLoading,
    setSkipCompanyQualification,
    getStepsForCampaignType,
    getCurrentStepInfo,
  };

  if (isComplete) {
    return <CampaignComplete sequenceName={state.selectedSequence || 'Default Sequence'} />;
  }

  // Render campaign type selection
  // Force instant navigation - uses onMouseDown to bypass React's event batching
  const handleBackToCampaigns = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Hide UI immediately for instant visual feedback
    const root = document.getElementById('root');
    if (root) root.style.visibility = 'hidden';
    
    // Navigate immediately - page reload clears all state
    window.location.href = '/campaign';
  };

  if (state.wizardPhase === 'type_selection') {
    return (
      <div className="new-campaign-wizard">
        <div className="wizard-header">
          <button type="button" className="back-btn" onMouseDown={handleBackToCampaigns}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back to Campaigns
          </button>
          <h1 className="wizard-title">Create New Campaign</h1>
        </div>
        <div className="wizard-content">
          <CampaignTypeSelection
            onSelect={handleTypeSelect}
            selectedType={state.campaignType}
            campaignName={state.campaignName}
            onCampaignNameChange={setCampaignName}
            onCampaignNameValidated={setIsCampaignNameValid}
          />
          {/* Show warning if trying to proceed without valid campaign name */}
          {state.campaignType && !isCampaignNameValid && (
            <div className="campaign-name-warning">
              Please enter a valid campaign name before proceeding
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render product selection
  if (state.wizardPhase === 'product_selection' && state.campaignType) {
    return (
      <div className="new-campaign-wizard">
        <div className="wizard-header">
          <button className="back-btn" onClick={handleBackToTypeSelection}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back
          </button>
          <h1 className="wizard-title">Create New Campaign</h1>
          <div className="campaign-type-badge">
            {CAMPAIGN_TYPE_LABELS[state.campaignType]}
          </div>
        </div>
        <div className="wizard-content">
          <ProductSelection
            campaignType={state.campaignType}
            onComplete={handleProductComplete}
            onBack={handleBackToTypeSelection}
          />
        </div>
      </div>
    );
  }

  // Get current step component
  const CurrentStepComponent = currentSteps.find(s => s.stepNumber === state.currentStep)?.component;

  return (
    <CampaignContext.Provider value={contextValue}>
      <div className="new-campaign-wizard">
        {/* Header with back button - uses onMouseDown for instant response */}
        <div className="wizard-header">
          <button type="button" className="back-btn" onMouseDown={handleBackToCampaigns}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back to Campaigns
          </button>
          <h1 className="wizard-title">Create New Campaign</h1>
          {state.campaignType && (
            <div className="campaign-type-badge">
              {CAMPAIGN_TYPE_LABELS[state.campaignType]}
            </div>
          )}
        </div>

        {/* Progress Stepper */}
        <div className="wizard-stepper">
          {currentSteps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div
                className={`stepper-item ${state.currentStep === step.stepNumber ? 'active' : ''} ${state.maxStepReached > step.stepNumber ? 'completed' : ''}`}
                onClick={() => step.stepNumber <= state.maxStepReached && goToStep(step.stepNumber)}
                role="button"
                tabIndex={step.stepNumber <= state.maxStepReached ? 0 : -1}
              >
                <div className="stepper-circle">
                  {state.maxStepReached > step.stepNumber ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  ) : (
                    step.stepNumber
                  )}
                </div>
                <span className="stepper-title">{step.title}</span>
              </div>
              {index < currentSteps.length - 1 && <div className="stepper-connector" />}
            </React.Fragment>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-content">
          {CurrentStepComponent && <CurrentStepComponent />}
        </div>
      </div>
    </CampaignContext.Provider>
  );
};
