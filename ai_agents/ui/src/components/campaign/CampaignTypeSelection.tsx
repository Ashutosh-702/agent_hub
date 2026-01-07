import React, { useState, useEffect, useCallback } from 'react';
import { useCheckCampaignNameMutation } from '../../store';

export type CampaignType = 
  | 'import_csv' 
  | 'single_company' 
  | 'wide_prospecting' 
  | 'similar_companies' 
  | 'nl_filter';

interface CampaignTypeOption {
  id: CampaignType;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const campaignTypes: CampaignTypeOption[] = [
  {
    id: 'import_csv',
    title: 'Import Company List',
    description: 'Upload a CSV file with company names and domains/URLs',
    icon: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    ),
  },
  {
    id: 'single_company',
    title: 'Single Company URL',
    description: 'Already-qualified company - fetch contacts directly',
    icon: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
      </svg>
    ),
  },
  {
    id: 'wide_prospecting',
    title: 'Wide Prospecting',
    description: 'Apollo search with filters to find matching companies',
    icon: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
    ),
  },
  {
    id: 'similar_companies',
    title: 'Similar Companies Search',
    description: 'Find companies similar to a given company URL',
    icon: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
      </svg>
    ),
  },
  {
    id: 'nl_filter',
    title: 'Find All - Natural Language',
    description: 'Describe your ideal companies in plain English',
    icon: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
];

interface CampaignTypeSelectionProps {
  onSelect: (type: CampaignType) => void;
  selectedType: CampaignType | null;
  campaignName: string;
  onCampaignNameChange: (name: string) => void;
  onCampaignNameValidated: (isValid: boolean) => void;
}

export const CampaignTypeSelection: React.FC<CampaignTypeSelectionProps> = ({
  onSelect,
  selectedType,
  campaignName,
  onCampaignNameChange,
  onCampaignNameValidated,
}) => {
  const [checkCampaignName] = useCheckCampaignNameMutation();
  const [nameError, setNameError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isNameValid, setIsNameValid] = useState(false);

  // Debounced validation
  const validateCampaignName = useCallback(async (name: string) => {
    // Reset states
    setNameError(null);
    setIsNameValid(false);
    
    // Basic validation
    if (!name || !name.trim()) {
      setNameError('Campaign name is required');
      onCampaignNameValidated(false);
      return;
    }
    
    const trimmedName = name.trim();
    if (trimmedName.length < 3) {
      setNameError('Campaign name must be at least 3 characters');
      onCampaignNameValidated(false);
      return;
    }
    
    if (trimmedName.length > 100) {
      setNameError('Campaign name must be less than 100 characters');
      onCampaignNameValidated(false);
      return;
    }

    // Check uniqueness via API
    setIsChecking(true);
    try {
      const result = await checkCampaignName({ campaign_name: trimmedName }).unwrap();
      if (result.data?.exists) {
        setNameError('Campaign name already exists. Please choose a different name.');
        setIsNameValid(false);
        onCampaignNameValidated(false);
      } else {
        setNameError(null);
        setIsNameValid(true);
        onCampaignNameValidated(true);
      }
    } catch {
      setNameError('Failed to validate campaign name. Please try again.');
      setIsNameValid(false);
      onCampaignNameValidated(false);
    } finally {
      setIsChecking(false);
    }
  }, [checkCampaignName, onCampaignNameValidated]);

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      if (campaignName) {
        validateCampaignName(campaignName);
      } else {
        setNameError(null);
        setIsNameValid(false);
        onCampaignNameValidated(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [campaignName, validateCampaignName, onCampaignNameValidated]);

  return (
    <div className="campaign-type-selection">
      <div className="step-header">
        <h2>Create New Campaign</h2>
        <p>Name your campaign and select how you want to source your target companies</p>
      </div>

      {/* Campaign Name Input */}
      <div className="campaign-name-section">
        <label htmlFor="campaign-name" className="campaign-name-label">
          Campaign Name <span className="required">*</span>
        </label>
        <div className="campaign-name-input-wrapper">
          <input
            id="campaign-name"
            type="text"
            className={`campaign-name-input ${nameError ? 'error' : ''} ${isNameValid ? 'valid' : ''}`}
            placeholder="Enter a unique campaign name"
            value={campaignName}
            onChange={(e) => onCampaignNameChange(e.target.value)}
            maxLength={100}
          />
          {isChecking && (
            <span className="input-status checking">
              <svg className="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" strokeOpacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
              </svg>
            </span>
          )}
          {!isChecking && isNameValid && (
            <span className="input-status valid">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
          )}
        </div>
        {nameError && <p className="campaign-name-error">{nameError}</p>}
        <p className="campaign-name-hint">This name will help you identify your campaign later</p>
      </div>

      <div className="step-header" style={{ marginTop: '32px' }}>
        <h3>Choose Campaign Type</h3>
        <p>Select how you want to source your target companies</p>
      </div>

      <div className="campaign-type-grid">
        {campaignTypes.map((type) => (
          <button
            key={type.id}
            className={`campaign-type-card ${selectedType === type.id ? 'selected' : ''}`}
            onClick={() => onSelect(type.id)}
          >
            <div className="campaign-type-icon">{type.icon}</div>
            <h3 className="campaign-type-title">{type.title}</h3>
            <p className="campaign-type-description">{type.description}</p>
            {selectedType === type.id && (
              <div className="selected-indicator">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default CampaignTypeSelection;

