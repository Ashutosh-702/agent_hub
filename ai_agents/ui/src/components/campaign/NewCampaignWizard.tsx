import { useState, createContext, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './CampaignWizard.css';
import { Step1LeadGeneration } from './Step1LeadGeneration';
import { Step2LeadQualification } from './Step2LeadQualification';
import { Step3SyncHubspot } from './Step3SyncHubspot';
import { Step4Personalization } from './Step4Personalization';
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
}

export interface Company extends Prospect {
  contacts: Contact[];
  syncStatus: 'not_synced' | 'syncing' | 'synced' | 'failed';
  personalization?: {
    messageStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    deckStatus: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected';
    message?: string;
    deckUrl?: string;
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
  currentStep: number;
  filters: CampaignFilters;
  prospects: Prospect[];
  qualifiedCompanies: Company[];
  qualificationMode: 'manual' | 'ai' | null;
  aiQuestions: string[];
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
  setQualificationMode: (mode: 'manual' | 'ai' | null) => void;
  qualifyCompany: (companyId: string, qualified: boolean) => void;
  bulkQualify: (companyIds: string[], qualified: boolean) => void;
  syncCompany: (companyId: string) => void;
  bulkSync: (companyIds: string[]) => void;
  generatePersonalization: (companyId: string) => void;
  bulkGeneratePersonalization: (companyIds: string[]) => void;
  approvePersonalization: (companyId: string, type: 'message' | 'deck') => void;
  rejectPersonalization: (companyId: string, type: 'message' | 'deck') => void;
  setSelectedSequence: (sequenceId: string) => void;
  enrollToSequence: (companyIds: string[]) => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;
  setLoading: (loading: boolean, message?: string, estimatedCount?: number) => void;
}

const CampaignContext = createContext<CampaignContextType | null>(null);

export const useCampaignWizard = () => {
  const context = useContext(CampaignContext);
  if (!context) {
    throw new Error('useCampaignWizard must be used within NewCampaignWizard');
  }
  return context;
};

const STEPS = [
  { id: 1, title: 'Lead Generation', description: 'Define target criteria' },
  { id: 2, title: 'Lead Qualification', description: 'Qualify prospects' },
  { id: 3, title: 'Sync to CRM', description: 'Sync to HubSpot' },
  { id: 4, title: 'Personalization', description: 'Generate & review' },
];

export const NewCampaignWizard = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<CampaignState>({
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
    qualificationMode: null,
    aiQuestions: [],
    selectedSequence: null,
    isLoading: false,
    loadingMessage: '',
    estimatedCount: 0,
  });

  const [isComplete, setIsComplete] = useState(false);

  const setFilters = useCallback((filters: CampaignFilters) => {
    setState(prev => ({ ...prev, filters }));
  }, []);

  const setProspects = useCallback((prospects: Prospect[]) => {
    setState(prev => ({ ...prev, prospects }));
  }, []);

  const setQualifiedCompanies = useCallback((companies: Company[]) => {
    setState(prev => ({ ...prev, qualifiedCompanies: companies }));
  }, []);

  const setQualificationMode = useCallback((mode: 'manual' | 'ai' | null) => {
    setState(prev => ({ ...prev, qualificationMode: mode }));
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

  const syncCompany = useCallback((companyId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        c.id === companyId ? { ...c, syncStatus: 'syncing' } : c
      ),
    }));
    // Simulate sync
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        qualifiedCompanies: prev.qualifiedCompanies.map(c =>
          c.id === companyId ? { ...c, syncStatus: 'synced' } : c
        ),
      }));
    }, 1500);
  }, []);

  const bulkSync = useCallback((companyIds: string[]) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        companyIds.includes(c.id) ? { ...c, syncStatus: 'syncing' } : c
      ),
    }));
    // Simulate bulk sync
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        qualifiedCompanies: prev.qualifiedCompanies.map(c =>
          companyIds.includes(c.id) ? { ...c, syncStatus: 'synced' } : c
        ),
      }));
    }, 2000);
  }, []);

  const generatePersonalization = useCallback((companyId: string) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        c.id === companyId
          ? {
              ...c,
              personalization: {
                ...c.personalization,
                messageStatus: 'generating',
                deckStatus: 'generating',
              } as Company['personalization'],
            }
          : c
      ),
    }));
    // Simulate generation
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        qualifiedCompanies: prev.qualifiedCompanies.map(c =>
          c.id === companyId
            ? {
                ...c,
                personalization: {
                  messageStatus: 'generated',
                  deckStatus: 'generated',
                  message: `Hi Team at ${c.name},\n\nI noticed your company is doing great work in ${c.industry}. We help companies like yours achieve 3x better results with our platform.\n\nWould love to schedule a quick call to discuss how we can help ${c.name} grow even faster.\n\nBest regards`,
                  deckUrl: 'https://example.com/deck.pdf',
                },
              }
            : c
        ),
      }));
    }, 3000);
  }, []);

  const bulkGeneratePersonalization = useCallback((companyIds: string[]) => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        companyIds.includes(c.id)
          ? {
              ...c,
              personalization: {
                ...c.personalization,
                messageStatus: 'generating',
                deckStatus: 'generating',
              } as Company['personalization'],
            }
          : c
      ),
    }));
    // Simulate bulk generation with staggered completion
    companyIds.forEach((id, index) => {
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          qualifiedCompanies: prev.qualifiedCompanies.map(c =>
            c.id === id
              ? {
                  ...c,
                  personalization: {
                    messageStatus: 'generated',
                    deckStatus: 'generated',
                    message: `Hi Team at ${c.name},\n\nI noticed your company is doing great work in ${c.industry}. We help companies like yours achieve 3x better results with our platform.\n\nWould love to schedule a quick call to discuss how we can help ${c.name} grow even faster.\n\nBest regards`,
                    deckUrl: 'https://example.com/deck.pdf',
                  },
                }
              : c
          ),
        }));
      }, 2000 + index * 1000);
    });
  }, []);

  const approvePersonalization = useCallback((companyId: string, type: 'message' | 'deck') => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        c.id === companyId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                [type === 'message' ? 'messageStatus' : 'deckStatus']: 'approved',
              },
            }
          : c
      ),
    }));
  }, []);

  const rejectPersonalization = useCallback((companyId: string, type: 'message' | 'deck') => {
    setState(prev => ({
      ...prev,
      qualifiedCompanies: prev.qualifiedCompanies.map(c =>
        c.id === companyId
          ? {
              ...c,
              personalization: {
                ...c.personalization!,
                [type === 'message' ? 'messageStatus' : 'deckStatus']: 'rejected',
              },
            }
          : c
      ),
    }));
  }, []);

  const setSelectedSequence = useCallback((sequenceId: string) => {
    setState(prev => ({ ...prev, selectedSequence: sequenceId }));
  }, []);

  const enrollToSequence = useCallback((_companyIds: string[]) => {
    // Simulate enrollment
    setState(prev => ({ ...prev, isLoading: true, loadingMessage: 'Enrolling leads to sequence...' }));
    setTimeout(() => {
      setState(prev => ({ ...prev, isLoading: false }));
      setIsComplete(true);
    }, 2000);
  }, []);

  const nextStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.min(prev.currentStep + 1, 4) }));
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) }));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= 4) {
      setState(prev => ({ ...prev, currentStep: step }));
    }
  }, []);

  const setLoading = useCallback((loading: boolean, message = '', estimatedCount = 0) => {
    setState(prev => ({ ...prev, isLoading: loading, loadingMessage: message, estimatedCount }));
  }, []);

  const contextValue: CampaignContextType = {
    state,
    setFilters,
    setProspects,
    setQualifiedCompanies,
    setQualificationMode,
    qualifyCompany,
    bulkQualify,
    syncCompany,
    bulkSync,
    generatePersonalization,
    bulkGeneratePersonalization,
    approvePersonalization,
    rejectPersonalization,
    setSelectedSequence,
    enrollToSequence,
    nextStep,
    prevStep,
    goToStep,
    setLoading,
  };

  if (isComplete) {
    return <CampaignComplete sequenceName={state.selectedSequence || 'Default Sequence'} />;
  }

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
        </div>

        {/* Progress Stepper */}
        <div className="wizard-stepper">
          {STEPS.map((step, index) => (
            <div
              key={step.id}
              className={`stepper-item ${state.currentStep === step.id ? 'active' : ''} ${state.currentStep > step.id ? 'completed' : ''}`}
              onClick={() => state.currentStep > step.id && goToStep(step.id)}
              role="button"
              tabIndex={state.currentStep > step.id ? 0 : -1}
            >
              <div className="stepper-circle">
                {state.currentStep > step.id ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : (
                  step.id
                )}
              </div>
              <div className="stepper-content">
                <span className="stepper-title">{step.title}</span>
                <span className="stepper-description">{step.description}</span>
              </div>
              {index < STEPS.length - 1 && <div className="stepper-line" />}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-content">
          {state.currentStep === 1 && <Step1LeadGeneration />}
          {state.currentStep === 2 && <Step2LeadQualification />}
          {state.currentStep === 3 && <Step3SyncHubspot />}
          {state.currentStep === 4 && <Step4Personalization />}
        </div>
      </div>
    </CampaignContext.Provider>
  );
};

