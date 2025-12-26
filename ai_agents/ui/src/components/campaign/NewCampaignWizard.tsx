import { useState, createContext, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './CampaignWizard.css';
import { Step1Prospecting } from './Step1Prospecting';
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
  approveContactPersonalization: (contactId: string) => void;
  rejectContactPersonalization: (contactId: string) => void;
  setSelectedSequence: (sequenceId: string) => void;
  enrollToSequence: (contactIds: string[]) => void;
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
  { id: 1, title: 'Prospecting' },
  { id: 2, title: 'Company Qualification' },
  { id: 3, title: 'Contact Qualification' },
  { id: 4, title: 'Sync to Hubspot' },
  { id: 5, title: 'Personalization' },
  { id: 6, title: 'Enroll for Outreach' },
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

  const generateContactPersonalization = useCallback((contactId: string) => {
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
                  messageStatus: 'generating',
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
                    messageStatus: 'generated',
                    message: `Hi ${c.firstName},\n\nI noticed ${company?.name || 'your company'} is doing great work in ${company?.industry || 'your industry'}. As ${c.jobTitle}, I thought you might be interested in how we help companies like yours achieve 3x better results.\n\nWould love to schedule a quick call to discuss how we can help.\n\nBest regards`,
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
                      messageStatus: 'generated',
                      message: `Hi ${c.firstName},\n\nI noticed ${company?.name || 'your company'} is doing great work in ${company?.industry || 'your industry'}. As ${c.jobTitle}, I thought you might be interested in how we help companies like yours achieve 3x better results.\n\nWould love to schedule a quick call to discuss how we can help.\n\nBest regards`,
                    },
                  }
                : c
            ),
          };
        });
      }, 2000 + index * 500);
    });
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
    setState(prev => ({ ...prev, currentStep: Math.min(prev.currentStep + 1, 6) }));
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) }));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= 6) {
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
    approveContactPersonalization,
    rejectContactPersonalization,
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
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : (
                  step.id
                )}
              </div>
              <span className="stepper-title">{step.title}</span>
              {index < STEPS.length - 1 && <div className="stepper-line" />}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-content">
          {state.currentStep === 1 && <Step1Prospecting />}
          {state.currentStep === 2 && <Step2CompanyQualification />}
          {state.currentStep === 3 && <Step3ContactQualification />}
          {state.currentStep === 4 && <Step4SyncHubspot />}
          {state.currentStep === 5 && <Step5Personalization />}
          {state.currentStep === 6 && <Step6EnrollOutreach />}
        </div>
      </div>
    </CampaignContext.Provider>
  );
};

