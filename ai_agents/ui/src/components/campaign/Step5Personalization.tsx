import { useState, useEffect, useRef, useCallback } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import { useBulkSaveContactPersonalizationMutation } from '../../store';

// Mock personalization data generator
const generateMockPersonalization = (contact: { id: string; firstName: string; lastName: string; email: string; jobTitle: string; companyName?: string }) => {
  const messages = [
    `Hi ${contact.firstName},\n\nI noticed your role as ${contact.jobTitle} at ${contact.companyName || 'your company'} and wanted to reach out. Based on your company's growth trajectory, I believe our solution could help streamline your operations.\n\nWould you be open to a brief 15-minute call this week?\n\nBest regards`,
    `Hello ${contact.firstName},\n\nI came across your profile and was impressed by your work at ${contact.companyName || 'your organization'}. Given your focus on ${contact.jobTitle?.toLowerCase().includes('sales') ? 'driving revenue' : 'business growth'}, I think you'd find our platform valuable.\n\nLet me know if you'd like to explore this further.\n\nCheers`,
    `Dear ${contact.firstName},\n\nAs ${contact.jobTitle} at ${contact.companyName || 'your company'}, you're likely facing challenges in scaling efficiently. Our solution has helped similar companies achieve 3x productivity gains.\n\nI'd love to share some insights that could benefit your team.\n\nWarm regards`,
  ];

  const randomMessage = messages[Math.floor(Math.random() * messages.length)];
  const deckId = `deck_${contact.id}_${Date.now()}`;

  return {
    contact_id: contact.id,
    email_id: contact.email || `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@example.com`,
    text_message: randomMessage,
    deck_url: `https://storage.cloud.example.com/personalized-decks/${deckId}.pdf`,
    status: 'generated' as const,
  };
};

interface PersonalizationResult {
  contact_id: string;
  email_id: string;
  text_message: string;
  deck_url: string;
  status: 'pending' | 'generated' | 'approved' | 'rejected';
}

export const Step5Personalization = () => {
  const {
    state,
    prevStep,
    nextStep,
    setQualifiedContacts,
  } = useCampaignWizard();

  const [expandedContact, setExpandedContact] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingProgress, setGeneratingProgress] = useState<{ current: number; total: number } | null>(null);
  const [personalizationResults, setPersonalizationResults] = useState<Map<string, PersonalizationResult>>(new Map());
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editedMessages, setEditedMessages] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const campaignId = state.campaignId || '';
  const contacts = state.qualifiedContacts;
  
  // RTK Query mutations
  const [bulkSaveContactPersonalization] = useBulkSaveContactPersonalizationMutation();

  // Get company name for a contact
  const getCompanyName = useCallback((companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  }, [state.qualifiedCompanies]);

  // Count stats
  const generatedCount = Array.from(personalizationResults.values()).filter(r => r.status === 'generated' || r.status === 'approved').length;
  const approvedCount = Array.from(personalizationResults.values()).filter(r => r.status === 'approved').length;

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

  const selectedCount = contacts.filter(c => c.personalization?.isSelected).length;
  const allSelected = contacts.length > 0 && contacts.every(c => c.personalization?.isSelected);
  const someSelected = contacts.some(c => c.personalization?.isSelected) && !allSelected;

  // Generate personalization for selected contacts (Mock API)
  const handleGeneratePersonalization = async () => {
    const selectedContacts = contacts.filter(c => c.personalization?.isSelected);
    if (selectedContacts.length === 0) return;

    setIsGenerating(true);
    setGeneratingProgress({ current: 0, total: selectedContacts.length });

    // Simulate API call and processing
    for (let i = 0; i < selectedContacts.length; i++) {
      const contact = selectedContacts[i];
      
      // Simulate processing delay (1-2 seconds per contact)
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
      
      // Generate mock personalization
      const result = generateMockPersonalization({
        id: contact.id,
        firstName: contact.firstName,
        lastName: contact.lastName,
        email: contact.email,
        jobTitle: contact.jobTitle,
        companyName: contact.companyName || getCompanyName(contact.companyId),
      });

      setPersonalizationResults(prev => {
        const newMap = new Map(prev);
        newMap.set(contact.id, result);
        return newMap;
      });

      setGeneratingProgress({ current: i + 1, total: selectedContacts.length });
    }

    setIsGenerating(false);
    setGeneratingProgress(null);
  };

  // Approve personalization - updates local state (saves to DB on Continue)
  const handleApprove = (contactId: string) => {
    const result = personalizationResults.get(contactId);
    if (!result) return;

    // Update local state to approved
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      newMap.set(contactId, { ...result, status: 'approved' });
      return newMap;
    });
  };

  // Reject personalization
  const handleReject = (contactId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        newMap.set(contactId, { ...result, status: 'rejected' });
      }
      return newMap;
    });
  };

  // Regenerate personalization for a contact
  const handleRegenerate = async (contactId: string) => {
    const contact = contacts.find(c => c.id === contactId);
    if (!contact) return;

    // Set generating status
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        newMap.set(contactId, { ...result, status: 'pending' });
      }
      return newMap;
    });

    // Simulate regeneration
    await new Promise(resolve => setTimeout(resolve, 1500));

    const result = generateMockPersonalization({
      id: contact.id,
      firstName: contact.firstName,
      lastName: contact.lastName,
      email: contact.email,
      jobTitle: contact.jobTitle,
      companyName: contact.companyName || getCompanyName(contact.companyId),
    });

    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      newMap.set(contactId, result);
      return newMap;
    });
  };

  // Save edited message
  const handleSaveEdit = (contactId: string) => {
    const editedMessage = editedMessages[contactId];
    if (!editedMessage) return;

    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        newMap.set(contactId, { ...result, text_message: editedMessage });
      }
      return newMap;
    });
    setEditingMessage(null);
  };

  // Continue to next step - saves all approved personalizations to database first
  const handleContinue = async () => {
    // Get all approved personalizations
    const approvedResults = Array.from(personalizationResults.entries())
      .filter(([_, result]) => result.status === 'approved');
    
    if (approvedResults.length === 0) {
      setSaveError('Please approve at least one contact personalization before continuing.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      // Build personalizations payload for API
      const personalizations = approvedResults.map(([_, result]) => ({
        contact_id: result.contact_id,
        email_id: result.email_id,
        personalized_message: result.text_message,
        ai_generated_deck: result.deck_url,
      }));

      // Save all approved personalizations to database
      if (campaignId) {
        console.log('Saving personalizations to database:', { campaign_id: campaignId, count: personalizations.length });
        const saveResult = await bulkSaveContactPersonalization({
          campaign_id: campaignId,
          personalizations,
        }).unwrap();
        console.log('Save result:', saveResult);
      } else {
        console.warn('No campaign ID found, skipping database save');
      }

      // Update contacts and proceed to next step
      const approvedContactIds = new Set(approvedResults.map(([id]) => id));
      const approvedContacts = contacts.filter(c => approvedContactIds.has(c.id));
      
      setQualifiedContacts(approvedContacts);
      nextStep();
    } catch (error) {
      console.error('Failed to save personalizations:', error);
      setSaveError('Failed to save personalizations to database. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const getStatusBadge = (contactId: string) => {
    const result = personalizationResults.get(contactId);
    if (!result) return <span className="status-badge pending">Pending</span>;
    
    switch (result.status) {
      case 'pending':
        return <span className="status-badge generating">Generating...</span>;
      case 'generated':
        return <span className="status-badge generated">Ready for Review</span>;
      case 'approved':
        return <span className="status-badge approved">Approved ✓</span>;
      case 'rejected':
        return <span className="status-badge rejected">Rejected</span>;
      default:
        return <span className="status-badge pending">Pending</span>;
    }
  };

  return (
    <div className="step-container step-personalization">
      <div className="step-header">
        <h2>Personalization</h2>
        <p>Generate personalized messages and decks for each contact</p>
      </div>

      {/* Error Banner */}
      {saveError && (
        <div className="sync-error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{saveError}</span>
          <button className="btn-icon" onClick={() => setSaveError(null)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      )}

      {/* Progress Bar during generation */}
      {generatingProgress && (
        <div className="sync-progress-container">
          <div className="sync-progress-header">
            <span className="sync-progress-status">
              <div className="spinner small" />
              Generating personalized content...
            </span>
            <span>{generatingProgress.current} / {generatingProgress.total} contacts</span>
          </div>
          <div className="sync-progress-bar">
            <div 
              className="sync-progress-fill"
              style={{ width: `${(generatingProgress.current / generatingProgress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

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
        <div className="stat">
          <span className="stat-value">{generatedCount}</span>
          <span className="stat-label">Generated</span>
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
          disabled={selectedCount === 0 || isGenerating}
          onClick={handleGeneratePersonalization}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          {isGenerating ? 'Generating...' : `Generate Personalization for ${selectedCount} Contacts`}
        </button>
      </div>

      {/* Contacts List */}
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
              disabled={isGenerating}
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
          const result = personalizationResults.get(contact.id);
          const isExpanded = expandedContact === contact.id;

          return (
            <div 
              key={contact.id} 
              className={`personalization-contact-card ${isSelected ? 'selected' : ''} ${result?.status === 'approved' ? 'approved' : ''}`}
            >
              <div className="contact-row" onClick={() => setExpandedContact(isExpanded ? null : contact.id)}>
              <div className="contact-select" onClick={(e) => e.stopPropagation()}>
                <label className="checkbox-container">
                  <input 
                    type="checkbox"
                    checked={isSelected || false}
                    onChange={() => toggleContactSelection(contact.id)}
                      disabled={isGenerating}
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
                    <span className="company-name">{contact.companyName || getCompanyName(contact.companyId)}</span>
                  </div>
                </div>
                <div className="contact-status">
                  {getStatusBadge(contact.id)}
              </div>
                {result?.status === 'approved' && (
                  <div className="qualified-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                )}
                <button 
                  className={`btn-icon expand-btn ${result?.status === 'generated' ? 'pulse-attention' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedContact(isExpanded ? null : contact.id);
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>

              {/* Expanded Content */}
              {isExpanded && result && (
                <div className="personalization-content" onClick={(e) => e.stopPropagation()}>
                  {/* Email ID */}
                  <div className="personalization-field">
                    <label>Email ID</label>
                    <div className="field-value email-field">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                      </svg>
                      <span>{result.email_id}</span>
                    </div>
                      </div>

                  {/* Text Message */}
                  <div className="personalization-field">
                    <label>Personalized Message</label>
                        {editingMessage === contact.id ? (
                      <div className="message-edit">
                          <textarea
                          value={editedMessages[contact.id] || result.text_message}
                          onChange={(e) => setEditedMessages(prev => ({ ...prev, [contact.id]: e.target.value }))}
                          rows={8}
                        />
                        <div className="edit-actions">
                          <button className="btn-primary btn-small" onClick={() => handleSaveEdit(contact.id)}>
                            Save Changes
                          </button>
                          <button className="btn-secondary btn-small" onClick={() => setEditingMessage(null)}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <pre className="message-preview">{result.text_message}</pre>
                    )}
                  </div>

                  {/* Deck URL (Public Cloud Storage) */}
                  <div className="personalization-field">
                    <label>AI Generated Deck (Cloud Storage URL)</label>
                    <div className="deck-url-display">
                          <input 
                            type="text" 
                        value={result.deck_url} 
                            readOnly 
                            className="deck-url-input"
                          />
                          <button
                            className="btn-icon open-deck-btn"
                        title="Open Deck"
                        onClick={() => window.open(result.deck_url, '_blank', 'noopener,noreferrer')}
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                              <polyline points="15 3 21 3 21 9"/>
                              <line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                          </button>
                        </div>
                      </div>

                  {/* Actions */}
                  {result.status === 'generated' && (
                    <div className="review-actions">
                      <button className="btn-success" onClick={() => handleApprove(contact.id)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Approve
                      </button>
                      <button className="btn-danger" onClick={() => handleReject(contact.id)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"/>
                          <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                        Reject
                      </button>
                      <button className="btn-secondary" onClick={() => {
                        setEditedMessages(prev => ({ ...prev, [contact.id]: result.text_message }));
                        setEditingMessage(contact.id);
                      }}>
                        Edit Message
                      </button>
                    </div>
                  )}

                  {result.status === 'rejected' && (
                    <div className="rejected-actions">
                      <p>Personalization was rejected. You can:</p>
                      <div className="action-buttons">
                        <button className="btn-primary" onClick={() => handleRegenerate(contact.id)}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                          </svg>
                          Regenerate
                        </button>
                        <button className="btn-secondary" onClick={() => {
                          setEditedMessages(prev => ({ ...prev, [contact.id]: result.text_message }));
                          setEditingMessage(contact.id);
                        }}>
                          Edit Manually
                        </button>
                      </div>
                    </div>
                  )}

                  {result.status === 'approved' && (
                    <div className="approved-badge-large">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                      <span>Approved - will be saved when you continue</span>
                    </div>
                  )}
                  </div>
              )}

              {/* Show pending message if no result yet */}
              {isExpanded && !result && (
                <div className="personalization-content pending-content" onClick={(e) => e.stopPropagation()}>
                  <p>Select this contact and click "Generate Personalization" to create personalized content.</p>
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
          disabled={approvedCount === 0 || isSaving}
          onClick={handleContinue}
        >
          {isSaving ? (
            <>
              <div className="spinner small" />
              Saving...
            </>
          ) : (
            <>
              Save & Continue with {approvedCount} Approved
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
