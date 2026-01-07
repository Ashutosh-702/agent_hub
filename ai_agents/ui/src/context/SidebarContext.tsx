import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from 'react';
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

  const toggleSidebar = useCallback(() => setIsCollapsed(prev => !prev), []);

  const setWizardProgress = useCallback((newProgress: WizardProgress) => {
    setWizardProgressState(newProgress);
  }, []);

  const clearWizardProgress = useCallback(() => {
    setWizardProgressState(defaultWizardProgress);
  }, []);

  const value = useMemo(() => ({
    isCollapsed,
    toggleSidebar,
    wizardProgress,
    setWizardProgress,
    clearWizardProgress,
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [isCollapsed, toggleSidebar, clearWizardProgress]); // Intentionally minimal deps to prevent freeze on navigation

  return (
    <SidebarContext.Provider value={value}>
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
