import { useState } from 'react';
import { useCampaignWizard, type Company } from './NewCampaignWizard';

export const Step3SyncHubspot = () => {
  const { state, syncCompany, bulkSync, nextStep, prevStep } = useCampaignWizard();

  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);
  const [selectedContacts, setSelectedContacts] = useState<Record<string, string[]>>({});

  const companies = state.qualifiedCompanies;
  const syncedCount = companies.filter(c => c.syncStatus === 'synced').length;
  const syncingCount = companies.filter(c => c.syncStatus === 'syncing').length;

  const toggleSelectCompany = (companyId: string) => {
    setSelectedCompanies(prev =>
      prev.includes(companyId)
        ? prev.filter(id => id !== companyId)
        : [...prev, companyId]
    );
  };

  const toggleSelectAll = () => {
    const unsyncedCompanies = companies.filter(c => c.syncStatus === 'not_synced');
    if (selectedCompanies.length === unsyncedCompanies.length) {
      setSelectedCompanies([]);
    } else {
      setSelectedCompanies(unsyncedCompanies.map(c => c.id));
    }
  };

  const toggleExpandCompany = (companyId: string) => {
    setExpandedCompany(prev => prev === companyId ? null : companyId);
  };

  const toggleSelectContact = (companyId: string, contactId: string) => {
    setSelectedContacts(prev => ({
      ...prev,
      [companyId]: prev[companyId]?.includes(contactId)
        ? prev[companyId].filter(id => id !== contactId)
        : [...(prev[companyId] || []), contactId],
    }));
  };

  const handleSyncCompany = (companyId: string) => {
    syncCompany(companyId);
  };

  const handleBulkSync = () => {
    if (selectedCompanies.length > 0) {
      bulkSync(selectedCompanies);
      setSelectedCompanies([]);
    }
  };

  const handleSyncAll = () => {
    const unsyncedIds = companies.filter(c => c.syncStatus === 'not_synced').map(c => c.id);
    bulkSync(unsyncedIds);
  };

  const getSyncStatusIcon = (status: Company['syncStatus']) => {
    switch (status) {
      case 'synced':
        return (
          <span className="sync-status synced" title="Synced to HubSpot">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </span>
        );
      case 'syncing':
        return (
          <span className="sync-status syncing" title="Syncing...">
            <svg className="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
          </span>
        );
      case 'failed':
        return (
          <span className="sync-status failed" title="Sync Failed">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </span>
        );
      default:
        return (
          <span className="sync-status not-synced" title="Not Synced">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </span>
        );
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
          <span className="stat-label">Total Companies</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{syncedCount}</span>
          <span className="stat-label">Synced</span>
        </div>
        <div className="stat syncing">
          <span className="stat-value">{syncingCount}</span>
          <span className="stat-label">Syncing</span>
        </div>
        <div className="stat pending">
          <span className="stat-value">{companies.length - syncedCount - syncingCount}</span>
          <span className="stat-label">Pending</span>
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="bulk-actions">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={selectedCompanies.length === companies.filter(c => c.syncStatus === 'not_synced').length && companies.filter(c => c.syncStatus === 'not_synced').length > 0}
            onChange={toggleSelectAll}
          />
          Select All Unsynced ({selectedCompanies.length} selected)
        </label>
        <div className="bulk-buttons">
          <button
            className="btn-primary btn-small"
            disabled={selectedCompanies.length === 0 || syncingCount > 0}
            onClick={handleBulkSync}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
              <path d="M16 21h5v-5"/>
            </svg>
            Sync Selected
          </button>
          <button
            className="btn-secondary btn-small"
            disabled={syncingCount > 0 || syncedCount === companies.length}
            onClick={handleSyncAll}
          >
            Sync All
          </button>
        </div>
      </div>

      {/* Companies List */}
      <div className="sync-companies-list">
        {companies.map((company) => (
          <div key={company.id} className={`sync-company-card ${company.syncStatus}`}>
            <div className="company-header" onClick={() => toggleExpandCompany(company.id)}>
              <div className="company-select">
                {company.syncStatus === 'not_synced' && (
                  <input
                    type="checkbox"
                    checked={selectedCompanies.includes(company.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelectCompany(company.id);
                    }}
                    onClick={(e) => e.stopPropagation()}
                  />
                )}
              </div>
              <div className="company-info">
                <h4>{company.name}</h4>
                <div className="company-meta">
                  <span className="tag">{company.industry}</span>
                  <span className="tag">{company.location}</span>
                  <span className="contacts-count">{company.contacts.length} contacts</span>
                </div>
              </div>
              <div className="company-status">
                {getSyncStatusIcon(company.syncStatus)}
              </div>
              <div className="company-actions">
                {company.syncStatus === 'not_synced' && (
                  <button
                    className="btn-primary btn-small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSyncCompany(company.id);
                    }}
                  >
                    Sync
                  </button>
                )}
                <button className="btn-icon expand-btn">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    style={{ transform: expandedCompany === company.id ? 'rotate(180deg)' : 'none' }}
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>
            </div>

            {/* Expanded Contacts */}
            {expandedCompany === company.id && (
              <div className="company-contacts">
                <div className="contacts-header">
                  <h5>Contacts</h5>
                </div>
                <div className="contacts-list">
                  {company.contacts.slice(0, 3).map((contact) => (
                    <div key={contact.id} className="contact-card">
                      <div className="contact-select">
                        <input
                          type="checkbox"
                          checked={selectedContacts[company.id]?.includes(contact.id) || false}
                          onChange={() => toggleSelectContact(company.id, contact.id)}
                        />
                      </div>
                      <div className="contact-avatar">
                        {contact.firstName[0]}{contact.lastName[0]}
                      </div>
                      <div className="contact-info">
                        <span className="contact-name">{contact.firstName} {contact.lastName}</span>
                        <span className="contact-title">{contact.jobTitle}</span>
                        <span className="contact-email">{contact.email}</span>
                      </div>
                      <div className="contact-status">
                        {contact.isSynced ? (
                          <span className="synced-badge">Synced</span>
                        ) : (
                          <span className="pending-badge">Pending</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {company.contacts.length > 3 && (
                    <button className="show-more-btn">
                      +{company.contacts.length - 3} more contacts
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
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
          onClick={nextStep}
          disabled={syncedCount === 0}
        >
          Continue to Personalization
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

