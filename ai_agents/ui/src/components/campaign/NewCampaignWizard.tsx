import React, { useState, createContext, useContext, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './CampaignWizard.css';
import { useSidebar } from '../../context/SidebarContext';
import { CampaignTypeSelection, type CampaignType } from './CampaignTypeSelection';
import { ProductSelection, type ProductSelectionMode } from './ProductSelection';
import { Step1Prospecting } from './Step1Prospecting';
import { Step1ImportCSV } from './Step1ImportCSV';
import { Step1SingleCompany } from './Step1SingleCompany';
import { Step1SimilarCompanies } from './Step1SimilarCompanies';
import { Step1NLFilter } from './Step1NLFilter';
import { StepCompanyEnrichment } from './StepCompanyEnrichment';
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
}

export interface CampaignState {
  // New fields for multi-funnel support
  campaignType: CampaignType | null;
  productSelectionMode: ProductSelectionMode | null;
  selectedProducts: string[];
  skipCompanyQualification: boolean;
  wizardPhase: 'type_selection' | 'product_selection' | 'steps';
  
  // Existing fields
  currentStep: number;
  filters: CampaignFilters;
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

  const enrichmentStep: StepConfig = {
    id: 'enrichment',
    stepNumber: 0,
    title: 'Company Enrichment',
    component: StepCompanyEnrichment,
  };

  const companyQualStep: StepConfig = {
    id: 'company-qualification',
    stepNumber: 0,
    title: 'Company Qualification',
    component: Step2CompanyQualification,
  };

  let steps: StepConfig[] = [];

  switch (campaignType) {
    case 'import_csv':
      steps = [
        { id: 'import', stepNumber: 1, title: 'Import Companies', component: Step1ImportCSV },
        enrichmentStep,
        ...(skipCompanyQual ? [] : [companyQualStep]),
        ...commonStepsAfterQualification,
      ];
      break;

    case 'single_company':
      // Single company skips company qualification entirely
      steps = [
        { id: 'company-input', stepNumber: 1, title: 'Company Input', component: Step1SingleCompany },
        enrichmentStep,
        // Skip company qualification for single company
        ...commonStepsAfterQualification,
      ];
      break;

    case 'wide_prospecting':
      steps = [
        { id: 'prospecting', stepNumber: 1, title: 'Lead Generation', component: Step1Prospecting },
        enrichmentStep,
        companyQualStep,
        ...commonStepsAfterQualification,
      ];
      break;

    case 'similar_companies':
      steps = [
        { id: 'similar-search', stepNumber: 1, title: 'Find Similar', component: Step1SimilarCompanies },
        enrichmentStep,
        companyQualStep,
        ...commonStepsAfterQualification,
      ];
      break;

    case 'nl_filter':
      steps = [
        { id: 'nl-search', stepNumber: 1, title: 'Natural Language Search', component: Step1NLFilter },
        enrichmentStep,
        companyQualStep,
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

// Campaign type labels for display
const CAMPAIGN_TYPE_LABELS: Record<CampaignType, string> = {
  import_csv: 'Import Company List',
  single_company: 'Single Company URL',
  wide_prospecting: 'Wide Prospecting',
  similar_companies: 'Similar Companies',
  nl_filter: 'Natural Language Filter',
};

export const NewCampaignWizard = () => {
  const navigate = useNavigate();
  const { setWizardProgress, clearWizardProgress } = useSidebar();
  const [state, setState] = useState<CampaignState>({
    // New fields
    campaignType: null,
    productSelectionMode: null,
    selectedProducts: [],
    skipCompanyQualification: false,
    wizardPhase: 'type_selection',
    
    // Existing fields
    currentStep: 1,
    filters: {
      industry: [],
      region: [],
      employeeCount: [],
      revenueMin: '',
      revenueMax: '',
    },
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
    setState(prev => ({ ...prev, currentStep: Math.min(prev.currentStep + 1, currentSteps.length) }));
  }, [currentSteps.length]);

  const prevStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) }));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= currentSteps.length) {
      setState(prev => ({ ...prev, currentStep: step }));
    }
  }, [currentSteps.length]);

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
  if (state.wizardPhase === 'type_selection') {
    return (
      <div className="new-campaign-wizard">
        <div className="wizard-header">
          <button className="back-btn" onClick={() => navigate('/campaign')}>
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
          />
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
        {/* Header with back button */}
        <div className="wizard-header">
          <button className="back-btn" onClick={() => navigate('/campaign')}>
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
                className={`stepper-item ${state.currentStep === step.stepNumber ? 'active' : ''} ${state.currentStep > step.stepNumber ? 'completed' : ''}`}
                onClick={() => state.currentStep > step.stepNumber && goToStep(step.stepNumber)}
                role="button"
                tabIndex={state.currentStep > step.stepNumber ? 0 : -1}
              >
                <div className="stepper-circle">
                  {state.currentStep > step.stepNumber ? (
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
