import { createContext, useContext, useState, type ReactNode } from 'react';
import type { CampaignType } from '../components/campaign';

export interface WizardProgress {
  isActive: boolean;
  campaignType: CampaignType | null;
  currentStep: number;
  totalSteps: number;
  steps: Array<{ id: string; title: string; stepNumber: number }>;
}

interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  wizardProgress: WizardProgress;
  setWizardProgress: (progress: WizardProgress) => void;
  clearWizardProgress: () => void;
}

const defaultWizardProgress: WizardProgress = {
  isActive: false,
  campaignType: null,
  currentStep: 0,
  totalSteps: 0,
  steps: [],
};

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const SidebarProvider = ({ children }: { children: ReactNode }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [wizardProgress, setWizardProgressState] = useState<WizardProgress>(defaultWizardProgress);

  const toggleSidebar = () => setIsCollapsed(prev => !prev);

  const setWizardProgress = (progress: WizardProgress) => {
    setWizardProgressState(progress);
  };

  const clearWizardProgress = () => {
    setWizardProgressState(defaultWizardProgress);
  };

  return (
    <SidebarContext.Provider value={{ 
      isCollapsed, 
      toggleSidebar, 
      wizardProgress, 
      setWizardProgress,
      clearWizardProgress,
    }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};
