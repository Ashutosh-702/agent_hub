import React from 'react';

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
}

export const CampaignTypeSelection: React.FC<CampaignTypeSelectionProps> = ({
  onSelect,
  selectedType,
}) => {
  return (
    <div className="campaign-type-selection">
      <div className="step-header">
        <h2>Choose Campaign Type</h2>
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


