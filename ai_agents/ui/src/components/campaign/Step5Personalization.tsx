import { useState } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';

export const Step5Personalization = () => {
  const {
    state,
    generateContactPersonalization,
    bulkGenerateContactPersonalization,
    approveContactPersonalization,
    rejectContactPersonalization,
    prevStep,
    nextStep,
    setQualifiedContacts,
  } = useCampaignWizard();

  const [expandedContact, setExpandedContact] = useState<string | null>(null);
  const [manualMessage, setManualMessage] = useState<Record<string, string>>({});
  const [editingMessage, setEditingMessage] = useState<string | null>(null);

  const contacts = state.qualifiedContacts;
  
  // Count selected (for bulk actions)
  const selectedCount = contacts.filter(c => c.personalization?.isSelected).length;
  const generatingCount = contacts.filter(c => c.personalization?.messageStatus === 'generating').length;
  const approvedCount = contacts.filter(c => c.personalization?.messageStatus === 'approved').length;

  // Get company name for a contact
  const getCompanyName = (companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  // Toggle contact selection
  const toggleContactSelection = (contactId: string) => {
    setQualifiedContacts(contacts.map(c => 
      c.id === contactId 
        ? { ...c, personalization: { ...c.personalization!, isSelected: !c.personalization?.isSelected } }
        : c
    ));
  };

  // Select/Deselect all contacts
  const handleSelectAll = () => {
    const allSelected = contacts.every(c => c.personalization?.isSelected);
    setQualifiedContacts(contacts.map(c => ({
      ...c,
      personalization: { ...c.personalization!, isSelected: !allSelected },
    })));
  };

  const allSelected = contacts.length > 0 && contacts.every(c => c.personalization?.isSelected);
  const someSelected = contacts.some(c => c.personalization?.isSelected) && !allSelected;

  const handleGenerate = (contactId: string) => {
    generateContactPersonalization(contactId);
  };

  const handleBulkGenerate = () => {
    const selectedIds = contacts.filter(c => c.personalization?.isSelected).map(c => c.id);
    if (selectedIds.length > 0) {
      bulkGenerateContactPersonalization(selectedIds);
    }
  };

  const handleApprove = (contactId: string) => {
    approveContactPersonalization(contactId);
  };

  const handleReject = (contactId: string) => {
    rejectContactPersonalization(contactId);
  };

  const handleRegenerate = (contactId: string) => {
    generateContactPersonalization(contactId);
  };

  const getStatusBadge = (status: string | undefined) => {
    switch (status) {
      case 'generating':
        return <span className="status-badge generating">Generating...</span>;
      case 'generated':
        return <span className="status-badge generated">Ready for Review</span>;
      case 'approved':
        return <span className="status-badge approved">Approved</span>;
      case 'rejected':
        return <span className="status-badge rejected">Needs Revision</span>;
      default:
        return <span className="status-badge pending">Pending</span>;
    }
  };

  const handleContinue = () => {
    // Keep only contacts with approved personalization
    const approved = contacts.filter(c => c.personalization?.messageStatus === 'approved');
    setQualifiedContacts(approved);
    nextStep();
  };

  return (
    <div className="step-container step-personalization">
      <div className="step-header">
        <h2>Personalization</h2>
        <p>Generate personalized messages for each contact</p>
      </div>

      {/* Stats Bar */}
      <div className="personalization-stats">
        <div className="stat">
          <span className="stat-value">{contacts.length}</span>
          <span className="stat-label">Total Contacts</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{selectedCount}</span>
          <span className="stat-label">Selected</span>
        </div>
        <div className="stat success">
          <span className="stat-value">{approvedCount}</span>
          <span className="stat-label">Approved</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bulk-actions">
        <button
          className="btn-primary"
          disabled={selectedCount === 0 || generatingCount > 0}
          onClick={handleBulkGenerate}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          Generate Personalized Messages for {selectedCount} Contacts
        </button>
      </div>

      {/* Contacts List with Select All Header */}
      <div className="personalization-contacts-list">
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
            <span className="selected-count">({selectedCount} of {contacts.length} selected)</span>
          </span>
        </div>

        {/* Contacts */}
        {contacts.map((contact) => {
          const isSelected = contact.personalization?.isSelected;
          return (
            <div 
              key={contact.id} 
              className={`personalization-contact-card ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleContactSelection(contact.id)}
            >
              <div className="contact-select" onClick={(e) => e.stopPropagation()}>
                <label className="checkbox-container">
                  <input 
                    type="checkbox"
                    checked={isSelected || false}
                    onChange={() => toggleContactSelection(contact.id)}
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
                {getStatusBadge(contact.personalization?.messageStatus)}
              </div>
              <div className="contact-actions" onClick={(e) => e.stopPropagation()}>
                {contact.personalization?.messageStatus === 'generating' && (
                  <div className="generating-indicator">
                    <div className="spinner" />
                    <span>Generating...</span>
                  </div>
                )}
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
                    setExpandedContact(expandedContact === contact.id ? null : contact.id);
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    style={{ transform: expandedContact === contact.id ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>

              {/* Expanded Content */}
              {expandedContact === contact.id && (
                <div className="personalization-content" onClick={(e) => e.stopPropagation()}>
                  {/* Message Section */}
                  <div className="personalization-section">
                    <div className="section-header">
                      <h5>Personalized Message for {contact.firstName}</h5>
                      {getStatusBadge(contact.personalization?.messageStatus)}
                    </div>
                    
                    {contact.personalization?.messageStatus === 'generating' && (
                      <div className="generating-placeholder">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                        <p>AI is crafting a personalized message...</p>
                      </div>
                    )}

                    {(contact.personalization?.messageStatus === 'generated' || contact.personalization?.messageStatus === 'approved') && (
                      <div className="message-preview">
                        {editingMessage === contact.id ? (
                          <textarea
                            value={manualMessage[contact.id] || contact.personalization?.message || ''}
                            onChange={(e) => setManualMessage(prev => ({ ...prev, [contact.id]: e.target.value }))}
                            rows={6}
                          />
                        ) : (
                          <pre>{contact.personalization?.message}</pre>
                        )}
                        
                        {contact.personalization?.messageStatus !== 'approved' && (
                          <div className="review-actions">
                            <button className="btn-success btn-small" onClick={() => handleApprove(contact.id)}>
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="20 6 9 17 4 12"/>
                              </svg>
                              Approve
                            </button>
                            <button className="btn-danger btn-small" onClick={() => handleReject(contact.id)}>
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                              </svg>
                              Reject
                            </button>
                            <button className="btn-secondary btn-small" onClick={() => setEditingMessage(editingMessage === contact.id ? null : contact.id)}>
                              {editingMessage === contact.id ? 'Cancel Edit' : 'Edit Manually'}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {contact.personalization?.messageStatus === 'rejected' && (
                      <div className="rejected-content">
                        <p>Message was rejected. You can:</p>
                        <div className="rejection-actions">
                          <button className="btn-primary btn-small" onClick={() => handleRegenerate(contact.id)}>
                            Regenerate
                          </button>
                          <button className="btn-secondary btn-small" onClick={() => setEditingMessage(contact.id)}>
                            Type Manual Message
                          </button>
                        </div>
                        {editingMessage === contact.id && (
                          <textarea
                            placeholder="Enter your custom message..."
                            value={manualMessage[contact.id] || ''}
                            onChange={(e) => setManualMessage(prev => ({ ...prev, [contact.id]: e.target.value }))}
                            rows={6}
                          />
                        )}
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
          disabled={approvedCount === 0}
          onClick={handleContinue}
        >
          Continue with {approvedCount} Approved
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
