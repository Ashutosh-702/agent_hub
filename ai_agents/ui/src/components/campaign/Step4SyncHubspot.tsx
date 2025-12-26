import { useState } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';

export const Step4SyncHubspot = () => {
  const { state, syncContact, bulkSyncContacts, nextStep, prevStep, setQualifiedContacts } = useCampaignWizard();

  const [isSyncing, setIsSyncing] = useState(false);
  const [syncComplete, setSyncComplete] = useState(false);

  const contacts = state.qualifiedContacts;
  const selectedCount = contacts.filter(c => c.syncStatus === 'selected' || c.syncStatus === 'synced').length;
  const syncedCount = contacts.filter(c => c.syncStatus === 'synced').length;

  // Get company name for a contact
  const getCompanyName = (companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  // Toggle contact selection for sync
  const toggleContactSelection = (contactId: string) => {
    setQualifiedContacts(contacts.map(c => 
      c.id === contactId 
        ? { ...c, syncStatus: c.syncStatus === 'selected' ? 'not_synced' : 'selected' as const }
        : c
    ));
  };

  // Select/Deselect all contacts
  const handleSelectAll = () => {
    const allSelected = contacts.every(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
    setQualifiedContacts(contacts.map(c => ({
      ...c,
      syncStatus: allSelected ? 'not_synced' : 'selected' as const,
    })));
  };

  const allSelected = contacts.length > 0 && contacts.every(c => c.syncStatus === 'selected' || c.syncStatus === 'synced');
  const someSelected = contacts.some(c => c.syncStatus === 'selected' || c.syncStatus === 'synced') && !allSelected;

  const handleSyncSelected = async () => {
    const selectedIds = contacts.filter(c => c.syncStatus === 'selected').map(c => c.id);
    if (selectedIds.length > 0) {
      setIsSyncing(true);
      
      // Simulate syncing
      setQualifiedContacts(contacts.map(c => 
        selectedIds.includes(c.id) 
          ? { ...c, syncStatus: 'syncing' as const }
          : c
      ));

      // Simulate sync completion
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setQualifiedContacts(contacts.map(c => 
        selectedIds.includes(c.id) 
          ? { ...c, syncStatus: 'synced' as const }
          : c
      ));
      
      setIsSyncing(false);
      setSyncComplete(true);
    }
  };

  const handleContinue = () => {
    // Keep only synced contacts for next step
    const synced = contacts.filter(c => c.syncStatus === 'synced');
    setQualifiedContacts(synced);
    nextStep();
  };

  return (
    <div className="step-container step-sync-hubspot">
      <div className="step-header">
        <h2>Sync to HubSpot</h2>
        <p>Select contacts to sync to your CRM</p>
      </div>

      {/* Stats Bar */}
      <div className="sync-stats">
        <div className="stat">
          <span className="stat-value">{contacts.length}</span>
          <span className="stat-label">Total Contacts</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{selectedCount}</span>
          <span className="stat-label">Selected</span>
        </div>
        {syncedCount > 0 && (
          <div className="stat success">
            <span className="stat-value">{syncedCount}</span>
            <span className="stat-label">Synced</span>
          </div>
        )}
      </div>

      {/* Sync Button */}
      {selectedCount > 0 && !syncComplete && (
        <div className="sync-action-bar">
          <button 
            className="btn-primary btn-large"
            onClick={handleSyncSelected}
            disabled={isSyncing}
          >
            {isSyncing ? (
              <>
                <div className="spinner" />
                Syncing...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/>
                </svg>
                Sync {selectedCount} Contacts to HubSpot
              </>
            )}
          </button>
        </div>
      )}

      {/* Sync Success Message */}
      {syncComplete && syncedCount > 0 && (
        <div className="sync-success-banner">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>{syncedCount} contacts successfully synced to HubSpot</span>
        </div>
      )}

      {/* Contacts List with Select All Header */}
      <div className="sync-contacts-list">
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
              disabled={syncComplete}
            />
            <span className="checkmark"></span>
          </label>
          <span className="select-all-text">
            {allSelected ? 'Deselect All' : 'Select All'} 
            <span className="selected-count">({selectedCount} of {contacts.length} selected)</span>
          </span>
        </div>

        {/* Contacts */}
        {contacts.map((contact) => {
          const isSelected = contact.syncStatus === 'selected' || contact.syncStatus === 'synced';
          const isSynced = contact.syncStatus === 'synced';
          const isSyncingContact = contact.syncStatus === 'syncing';
          
          return (
            <div 
              key={contact.id} 
              className={`sync-contact-card ${isSelected ? 'selected' : ''} ${isSynced ? 'synced' : ''}`}
              onClick={() => !isSynced && toggleContactSelection(contact.id)}
            >
              <div className="contact-select">
                <label className="checkbox-container" onClick={(e) => e.stopPropagation()}>
                  <input 
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleContactSelection(contact.id)}
                    disabled={isSynced}
                  />
                  <span className="checkmark"></span>
                </label>
              </div>
              <div className="contact-avatar">
                {contact.firstName[0]}{contact.lastName[0]}
              </div>
              <div className="contact-info">
                <h4>{contact.firstName} {contact.lastName}</h4>
                <div className="contact-meta">
                  <span className="job-title">{contact.jobTitle}</span>
                  <span className="company-name">{getCompanyName(contact.companyId)}</span>
                </div>
                <span className="contact-email">{contact.email}</span>
              </div>
              {isSyncingContact && (
                <div className="syncing-badge">
                  <div className="spinner small" />
                  Syncing...
                </div>
              )}
              {isSynced && (
                <div className="synced-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Synced
                </div>
              )}
              {isSelected && !isSynced && !isSyncingContact && (
                <div className="qualified-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
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
          onClick={handleContinue}
          disabled={syncedCount === 0}
        >
          Continue with {syncedCount} Synced Contacts
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
