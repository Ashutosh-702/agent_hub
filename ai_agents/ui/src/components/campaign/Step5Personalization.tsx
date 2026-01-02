import { useState, useEffect, useRef, useCallback } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';
import { 
  useBulkSaveContactPersonalizationMutation,
  useGetCampaignContactListQuery,
} from '../../store';
import { skipToken } from '@reduxjs/toolkit/query';

// Generate multiple message options for a contact
const generateMessageOptions = (contact: { firstName: string; jobTitle: string; companyName?: string }) => {
  return [
    {
      id: 'msg-1',
      text: `Hi ${contact.firstName},\n\nI noticed your role as ${contact.jobTitle} at ${contact.companyName || 'your company'} and wanted to reach out. Based on your company's growth trajectory, I believe our solution could help streamline your operations.\n\nWould you be open to a brief 15-minute call this week?\n\nBest regards`,
      label: 'Professional & Direct',
    },
    {
      id: 'msg-2',
      text: `Hello ${contact.firstName},\n\nI came across your profile and was impressed by your work at ${contact.companyName || 'your organization'}. Given your focus on ${contact.jobTitle?.toLowerCase().includes('sales') ? 'driving revenue' : 'business growth'}, I think you'd find our platform valuable.\n\nLet me know if you'd like to explore this further.\n\nCheers`,
      label: 'Friendly & Casual',
    },
    {
      id: 'msg-3',
      text: `Dear ${contact.firstName},\n\nAs ${contact.jobTitle} at ${contact.companyName || 'your company'}, you're likely facing challenges in scaling efficiently. Our solution has helped similar companies achieve 3x productivity gains.\n\nI'd love to share some insights that could benefit your team.\n\nWarm regards`,
      label: 'Value-Focused',
    },
  ];
};

// Generate multiple deck options for a contact
const generateDeckOptions = (contactId: string) => {
  const timestamp = Date.now();
  return [
    {
      id: 'deck-1',
      url: `https://storage.cloud.example.com/personalized-decks/deck_${contactId}_${timestamp}_standard.pdf`,
      label: 'Standard Deck',
    },
    {
      id: 'deck-2',
      url: `https://storage.cloud.example.com/personalized-decks/deck_${contactId}_${timestamp}_detailed.pdf`,
      label: 'Detailed Deck',
    },
    {
      id: 'deck-3',
      url: `https://storage.cloud.example.com/personalized-decks/deck_${contactId}_${timestamp}_executive.pdf`,
      label: 'Executive Summary',
    },
  ];
};

interface MessageOption {
  id: string;
  text: string;
  label: string;
}

interface DeckOption {
  id: string;
  url: string;
  label: string;
}

interface PersonalizationResult {
  contact_id: string;
  email_id: string;
  // Multiple options
  messageOptions: MessageOption[];
  deckOptions: DeckOption[];
  // Selected options
  selectedMessageId: string | null;
  selectedDeckId: string | null;
  // Approval status (separate for message and deck)
  messageApproved: boolean;
  deckApproved: boolean;
  // Legacy fields for compatibility
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
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const campaignId = state.campaignId || '';
  
  // RTK Query mutations
  const [bulkSaveContactPersonalization] = useBulkSaveContactPersonalizationMutation();

  // Track if we've hydrated from API to prevent re-fetching
  const [hasHydratedFromApi, setHasHydratedFromApi] = useState(false);
  
  // Always fetch contacts from API when campaignId exists (to restore personalization data)
  const { data: contactListData, isLoading: isLoadingCandidates } = useGetCampaignContactListQuery(
    campaignId ? { campaign_id: campaignId, page: 1, limit: 200 } : skipToken
  );
  
  console.log('[Step5] State check:', { 
    campaignId, 
    contactsLength: state.qualifiedContacts.length, 
    hasHydratedFromApi,
    hasApiData: !!contactListData?.data?.contacts?.length,
    isLoading: isLoadingCandidates,
  });

  // Hydrate contacts and personalization results from API
  useEffect(() => {
    // Only hydrate once per mount
    if (hasHydratedFromApi || !contactListData?.data?.contacts || contactListData.data.contacts.length === 0) {
      return;
    }

    const apiContacts = contactListData.data.contacts;
    console.log('[Step5] Hydrating from API:', apiContacts.length, 'contacts from API');
    
    // Filter for relevant contacts
    const relevantContacts = apiContacts.filter((c) => c.is_relevant);
    console.log('[Step5] Relevant contacts:', relevantContacts.length);
    
    // Check if any contacts have personalization data
    const contactsWithPersonalization = relevantContacts.filter(c => c.personalized_message && c.ai_generated_deck);
    console.log('[Step5] Contacts with existing personalization:', contactsWithPersonalization.length);
    
    // Always map contacts from API (to ensure we have the latest data)
    const mappedContacts: Contact[] = relevantContacts.map((c) => ({
      id: c.contact_id,
      companyId: c.company_id || '',
      companyName: c.contact_data?.company || '',
      firstName: c.contact_data?.firstname || '',
      lastName: c.contact_data?.lastname || '',
      email: c.contact_data?.email?.[0] || '',
      phone: c.contact_data?.phone?.[0] || undefined,
      jobTitle: c.contact_data?.jobtitle || '',
      linkedinUrl: c.linkedin_data?.linkedin_url || undefined,
      qualificationStatus: 'qualified' as const,
      syncStatus: 'synced' as const,
      personalization: {
        messageStatus: c.personalization_status === 'approved' ? 'approved' as const : 'pending' as const,
        deckStatus: c.personalization_status === 'approved' ? 'approved' as const : 'pending' as const,
        isSelected: true, // Always pre-select for personalization
      },
    }));
    
    // Restore personalization results for contacts that have saved data
    const restoredResults = new Map<string, PersonalizationResult>();
    relevantContacts.forEach((c) => {
      if (c.personalized_message && c.ai_generated_deck) {
        // Create single-option arrays for restored data
        const messageOptions: MessageOption[] = [{
          id: 'saved-msg',
          text: c.personalized_message,
          label: 'Saved Message',
        }];
        const deckOptions: DeckOption[] = [{
          id: 'saved-deck',
          url: c.ai_generated_deck,
          label: 'Saved Deck',
        }];
        
        restoredResults.set(c.contact_id, {
          contact_id: c.contact_id,
          email_id: c.email_id || c.contact_data?.email?.[0] || '',
          messageOptions,
          deckOptions,
          selectedMessageId: 'saved-msg',
          selectedDeckId: 'saved-deck',
          messageApproved: c.personalization_status === 'approved',
          deckApproved: c.personalization_status === 'approved',
          text_message: c.personalized_message,
          deck_url: c.ai_generated_deck,
          status: c.personalization_status === 'approved' ? 'approved' : 'generated',
        });
      }
    });
    
    console.log('[Step5] Setting state - Contacts:', mappedContacts.length, 'Personalization results:', restoredResults.size);
    
    setHasHydratedFromApi(true);
    
    if (mappedContacts.length > 0) {
      setQualifiedContacts(mappedContacts);
    }
    
    // Always restore personalization results (even if empty, to reset stale state)
    if (restoredResults.size > 0) {
      setPersonalizationResults(restoredResults);
    }
  }, [hasHydratedFromApi, contactListData, setQualifiedContacts]);

  const contacts = state.qualifiedContacts;

  // Get company name for a contact
  const getCompanyName = useCallback((companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  }, [state.qualifiedCompanies]);

  // Count stats
  const generatedCount = Array.from(personalizationResults.values()).filter(r => r.status === 'generated' || r.status === 'approved').length;
  // Approved means both message AND deck are approved
  const approvedCount = Array.from(personalizationResults.values()).filter(r => r.messageApproved && r.deckApproved).length;
  
  // Handlers for selecting message/deck options
  const handleSelectMessage = (contactId: string, messageId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        const selectedMessage = result.messageOptions.find(m => m.id === messageId);
        newMap.set(contactId, {
          ...result,
          selectedMessageId: messageId,
          text_message: selectedMessage?.text || '',
        });
      }
      return newMap;
    });
  };
  
  const handleSelectDeck = (contactId: string, deckId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        const selectedDeck = result.deckOptions.find(d => d.id === deckId);
        newMap.set(contactId, {
          ...result,
          selectedDeckId: deckId,
          deck_url: selectedDeck?.url || '',
        });
      }
      return newMap;
    });
  };
  
  const handleApproveMessage = (contactId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result && result.selectedMessageId) {
        const bothApproved = true && result.deckApproved;
        newMap.set(contactId, {
          ...result,
          messageApproved: true,
          status: bothApproved ? 'approved' : result.status,
        });
      }
      return newMap;
    });
  };
  
  const handleApproveDeck = (contactId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result && result.selectedDeckId) {
        const bothApproved = result.messageApproved && true;
        newMap.set(contactId, {
          ...result,
          deckApproved: true,
          status: bothApproved ? 'approved' : result.status,
        });
      }
      return newMap;
    });
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
      
      // Generate multiple options for message and deck
      const messageOptions = generateMessageOptions({
        firstName: contact.firstName,
        jobTitle: contact.jobTitle,
        companyName: contact.companyName || getCompanyName(contact.companyId),
      });
      const deckOptions = generateDeckOptions(contact.id);
      
      const result: PersonalizationResult = {
        contact_id: contact.id,
        email_id: contact.email || `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@example.com`,
        messageOptions,
        deckOptions,
        selectedMessageId: null, // User needs to select
        selectedDeckId: null, // User needs to select
        messageApproved: false,
        deckApproved: false,
        text_message: '', // Will be set when user selects
        deck_url: '', // Will be set when user selects
        status: 'generated' as const,
      };

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
  // Reject personalization
  const handleReject = (contactId: string) => {
    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      const result = newMap.get(contactId);
      if (result) {
        newMap.set(contactId, { 
          ...result, 
          status: 'rejected',
          messageApproved: false,
          deckApproved: false,
          selectedMessageId: null,
          selectedDeckId: null,
        });
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

    // Generate new options
    const messageOptions = generateMessageOptions({
      firstName: contact.firstName,
      jobTitle: contact.jobTitle,
      companyName: contact.companyName || getCompanyName(contact.companyId),
    });
    const deckOptions = generateDeckOptions(contact.id);

    const newResult: PersonalizationResult = {
      contact_id: contact.id,
      email_id: contact.email || `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@example.com`,
      messageOptions,
      deckOptions,
      selectedMessageId: null,
      selectedDeckId: null,
      messageApproved: false,
      deckApproved: false,
      text_message: '',
      deck_url: '',
      status: 'generated' as const,
    };

    setPersonalizationResults(prev => {
      const newMap = new Map(prev);
      newMap.set(contactId, newResult);
      return newMap;
    });
  };

  // Continue to next step - saves all approved personalizations to database first
  const handleContinue = async () => {
    // Get all fully approved personalizations (both message AND deck approved)
    const approvedResults = Array.from(personalizationResults.entries())
      .filter(([_, result]) => result.messageApproved && result.deckApproved);
    
    if (approvedResults.length === 0) {
      setSaveError('Please approve both message AND deck for at least one contact before continuing.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      // Build personalizations payload for API - use selected options
      const personalizations = approvedResults.map(([_, result]) => {
        // Get the selected message text
        const selectedMessage = result.messageOptions.find(m => m.id === result.selectedMessageId);
        const selectedDeck = result.deckOptions.find(d => d.id === result.selectedDeckId);
        
        return {
          contact_id: result.contact_id,
          email_id: result.email_id,
          personalized_message: selectedMessage?.text || result.text_message,
          ai_generated_deck: selectedDeck?.url || result.deck_url,
        };
      });

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
    
    // Check if both message and deck are approved
    if (result.messageApproved && result.deckApproved) {
      return <span className="status-badge approved">Approved ✓</span>;
    }
    
    // Check partial approvals
    if (result.messageApproved || result.deckApproved) {
      const msgStatus = result.messageApproved ? '✓' : '○';
      const deckStatus = result.deckApproved ? '✓' : '○';
      return <span className="status-badge generated">Msg {msgStatus} | Deck {deckStatus}</span>;
    }
    
    // Check if options are selected but not approved
    if (result.selectedMessageId || result.selectedDeckId) {
      return <span className="status-badge generated">Select & Approve</span>;
    }
    
    switch (result.status) {
      case 'pending':
        return <span className="status-badge generating">Generating...</span>;
      case 'generated':
        return <span className="status-badge generated">Ready for Review</span>;
      case 'rejected':
        return <span className="status-badge rejected">Rejected</span>;
      default:
        return <span className="status-badge pending">Pending</span>;
    }
  };

  // Show loading state when fetching from API
  if (isLoadingCandidates) {
    return (
      <div className="step-container step-personalization">
        <div className="step-header">
          <h2>Personalization</h2>
          <p>Loading contacts...</p>
        </div>
        <div className="loading-overlay" style={{ position: 'relative', minHeight: '200px' }}>
          <div className="loading-card">
            <div className="loading-animation ai-animation">
              <div className="ai-brain">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div className="ai-pulse" />
            </div>
            <h3>Loading contacts from server...</h3>
          </div>
        </div>
      </div>
    );
  }

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

                  {/* Message Selection Section */}
                  <div className={`personalization-section ${result.messageApproved ? 'approved' : ''}`}>
                    <div className="personalization-section-header">
                      <label>
                        Personalized Message
                        {result.messageApproved && (
                          <span className="personalization-approved-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approved
                          </span>
                        )}
                      </label>
                      {result.selectedMessageId && !result.messageApproved && (
                        <div className="personalization-section-actions">
                          <button className="btn-approve" onClick={() => handleApproveMessage(contact.id)}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approve Message
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {result.messageOptions && result.messageOptions.length > 1 ? (
                      <div className="message-options-list">
                        {result.messageOptions.map((option) => (
                          <div 
                            key={option.id}
                            className={`message-option ${result.selectedMessageId === option.id ? 'selected' : ''}`}
                            onClick={() => !result.messageApproved && handleSelectMessage(contact.id, option.id)}
                          >
                            <input 
                              type="radio" 
                              name={`message-${contact.id}`}
                              checked={result.selectedMessageId === option.id}
                              onChange={() => handleSelectMessage(contact.id, option.id)}
                              disabled={result.messageApproved}
                            />
                            <div className="message-option-content">
                              <strong>{option.label}</strong>
                              <pre>{option.text}</pre>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <pre className="message-preview">{result.text_message || result.messageOptions?.[0]?.text || 'No message generated'}</pre>
                    )}
                  </div>

                  {/* Deck Selection Section */}
                  <div className={`personalization-section ${result.deckApproved ? 'approved' : ''}`}>
                    <div className="personalization-section-header">
                      <label>
                        AI Generated Deck
                        {result.deckApproved && (
                          <span className="personalization-approved-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approved
                          </span>
                        )}
                      </label>
                      {result.selectedDeckId && !result.deckApproved && (
                        <div className="personalization-section-actions">
                          <button className="btn-approve" onClick={() => handleApproveDeck(contact.id)}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approve Deck
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {result.deckOptions && result.deckOptions.length > 1 ? (
                      <div className="message-options-list">
                        {result.deckOptions.map((option) => (
                          <div 
                            key={option.id}
                            className={`message-option ${result.selectedDeckId === option.id ? 'selected' : ''}`}
                            onClick={() => !result.deckApproved && handleSelectDeck(contact.id, option.id)}
                          >
                            <input 
                              type="radio" 
                              name={`deck-${contact.id}`}
                              checked={result.selectedDeckId === option.id}
                              onChange={() => handleSelectDeck(contact.id, option.id)}
                              disabled={result.deckApproved}
                            />
                            <div className="message-option-content">
                              <strong>{option.label}</strong>
                              <div className="deck-url-display" style={{ marginTop: '8px' }}>
                                <input type="text" value={option.url} readOnly className="deck-url-input" />
                                <button
                                  className="btn-icon open-deck-btn"
                                  title="Open Deck"
                                  onClick={(e) => { e.stopPropagation(); window.open(option.url, '_blank', 'noopener,noreferrer'); }}
                                >
                                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                    <polyline points="15 3 21 3 21 9"/>
                                    <line x1="10" y1="14" x2="21" y2="3"/>
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="deck-url-display">
                        <input type="text" value={result.deck_url || result.deckOptions?.[0]?.url || ''} readOnly className="deck-url-input" />
                        <button
                          className="btn-icon open-deck-btn"
                          title="Open Deck"
                          onClick={() => window.open(result.deck_url || result.deckOptions?.[0]?.url, '_blank', 'noopener,noreferrer')}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                            <polyline points="15 3 21 3 21 9"/>
                            <line x1="10" y1="14" x2="21" y2="3"/>
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Overall Status */}
                  {result.messageApproved && result.deckApproved && (
                    <div className="approved-badge-large">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                      <span>Both Message and Deck Approved - Ready to save</span>
                    </div>
                  )}

                  {/* Reject/Regenerate Actions */}
                  {result.status === 'generated' && !result.messageApproved && !result.deckApproved && (
                    <div className="review-actions">
                      <button className="btn-danger" onClick={() => handleReject(contact.id)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"/>
                          <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                        Reject All
                      </button>
                    </div>
                  )}

                  {result.status === 'rejected' && (
                    <div className="rejected-actions">
                      <p>Personalization was rejected. You can regenerate:</p>
                      <div className="action-buttons">
                        <button className="btn-primary" onClick={() => handleRegenerate(contact.id)}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                          </svg>
                          Regenerate
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
