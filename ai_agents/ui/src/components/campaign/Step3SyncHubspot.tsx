import { useState } from 'react';
import { useCampaignWizard, type Company } from './NewCampaignWizard';

export const Step3SyncHubspot = () => {
  const { state, syncCompany, bulkSync, nextStep, prevStep, setQualifiedCompanies } = useCampaignWizard();

  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);

  const companies = state.qualifiedCompanies;
  const selectedCount = companies.filter(c => c.syncStatus === 'selected' || c.syncStatus === 'synced').length;

  // Toggle company selection for sync
  const toggleCompanySelection = (companyId: string) => {
    setQualifiedCompanies(companies.map(c => 
      c.id === companyId 
        ? { ...c, syncStatus: c.syncStatus === 'selected' ? 'not_synced' : 'selected' as const }
        : c
    ));
  };

  // Select/Deselect all companies
  const handleSelectAll = () => {
    const allSelected = companies.every(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
    setQualifiedCompanies(companies.map(c => ({
      ...c,
      syncStatus: allSelected ? 'not_synced' : 'selected' as const,
    })));
  };

  const allSelected = companies.length > 0 && companies.every(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
  const someSelected = companies.some(c => c.syncStatus === 'selected' || c.syncStatus === 'synced') && !allSelected;

  const toggleExpandCompany = (companyId: string) => {
    setExpandedCompany(prev => prev === companyId ? null : companyId);
  };

  const handleSyncSelected = async () => {
    const selectedIds = companies.filter(c => c.syncStatus === 'selected').map(c => c.id);
    if (selectedIds.length > 0) {
      bulkSync(selectedIds);
    }
  };


  return (
    <div className="step-container step-sync-hubspot">
      <div className="step-header">
        <h2>Sync to HubSpot</h2>
        <p>Select companies and contacts to sync to your CRM</p>
      </div>

      {/* Stats Bar */}
      <div className="sync-stats">
        <div className="stat">
          <span className="stat-value">{companies.length}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{selectedCount}</span>
          <span className="stat-label">Selected</span>
        </div>
      </div>

      {/* Companies List with Select All Header */}
      <div className="sync-companies-list">
        {/* Select All Header */}
        <div className="select-all-header">
          <label className="checkbox-container">
            <input 
              type="checkbox" 
              checked={allSelected}
              ref={(el) => {
                if (el) el.indeterminate = someSelected;
              }}
              onChange={handleSelectAll}
            />
            <span className="checkmark"></span>
          </label>
          <span className="select-all-text">
            {allSelected ? 'Deselect All' : 'Select All'} 
            <span className="selected-count">({selectedCount} of {companies.length} selected)</span>
          </span>
        </div>

        {/* Companies */}
        {companies.map((company) => {
          const isSelected = company.syncStatus === 'selected' || company.syncStatus === 'synced';
          return (
            <div 
              key={company.id} 
              className={`sync-company-card ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleCompanySelection(company.id)}
            >
              <div className="company-select">
                <label className="checkbox-container" onClick={(e) => e.stopPropagation()}>
                  <input 
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleCompanySelection(company.id)}
                  />
                  <span className="checkmark"></span>
                </label>
              </div>
              <div className="company-info">
                <h4>{company.name}</h4>
                <div className="company-meta">
                  <span className="tag">{company.industry}</span>
                  <span className="tag">{company.location}</span>
                  <span className="contacts-count">{company.contacts.length} contacts</span>
                </div>
              </div>
              {isSelected && (
                <div className="qualified-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              )}
              <button 
                className="btn-icon expand-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpandCompany(company.id);
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  style={{ transform: expandedCompany === company.id ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              {/* Expanded Contacts */}
              {expandedCompany === company.id && (
                <div className="company-contacts" onClick={(e) => e.stopPropagation()}>
                  <div className="contacts-header">
                    <h5>Contacts to sync</h5>
                  </div>
                  <div className="contacts-list">
                    {company.contacts.slice(0, 3).map((contact) => (
                      <div key={contact.id} className="contact-card">
                        <div className="contact-avatar">
                          {contact.firstName[0]}{contact.lastName[0]}
                        </div>
                        <div className="contact-info">
                          <span className="contact-name">{contact.firstName} {contact.lastName}</span>
                          <span className="contact-title">{contact.jobTitle}</span>
                          <span className="contact-email">{contact.email}</span>
                        </div>
                      </div>
                    ))}
                    {company.contacts.length > 3 && (
                      <div className="more-contacts">
                        +{company.contacts.length - 3} more contacts
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="step-navigation">
        <button className="btn-secondary" onClick={prevStep}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>

        <button
          className="btn-primary btn-large"
          onClick={() => {
            // Only keep selected companies for next step
            const selected = companies.filter(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
            setQualifiedCompanies(selected);
            nextStep();
          }}
          disabled={selectedCount === 0}
        >
          Continue with {selectedCount} Selected
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

