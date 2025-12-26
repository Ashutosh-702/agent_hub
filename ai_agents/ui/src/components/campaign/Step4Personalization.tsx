import { useState } from 'react';
import { useCampaignWizard, type Company } from './NewCampaignWizard';

const MOCK_SEQUENCES = [
  { id: 'seq-1', name: 'Enterprise Outreach - Q1 2025' },
  { id: 'seq-2', name: 'SMB Cold Outreach' },
  { id: 'seq-3', name: 'Healthcare Decision Makers' },
  { id: 'seq-4', name: 'Tech Founders Sequence' },
  { id: 'seq-5', name: 'Re-engagement Campaign' },
];

export const Step4Personalization = () => {
  const {
    state,
    generatePersonalization,
    bulkGeneratePersonalization,
    approvePersonalization,
    rejectPersonalization,
    setSelectedSequence,
    enrollToSequence,
    prevStep,
    setQualifiedCompanies,
  } = useCampaignWizard();

  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [manualMessage, setManualMessage] = useState<Record<string, string>>({});
  const [manualDeckUrl, setManualDeckUrl] = useState<Record<string, string>>({});
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editingDeck, setEditingDeck] = useState<string | null>(null);

  const companies = state.qualifiedCompanies;
  
  // Count selected (for enrollment)
  const selectedCount = companies.filter(c => c.personalization?.isSelected).length;

  const generatingCount = companies.filter(c => 
    c.personalization?.messageStatus === 'generating'
  ).length;

  // Toggle company selection for enrollment
  const toggleCompanySelection = (companyId: string) => {
    setQualifiedCompanies(companies.map(c => 
      c.id === companyId 
        ? { ...c, personalization: { ...c.personalization!, isSelected: !c.personalization?.isSelected } }
        : c
    ));
  };

  // Select/Deselect all companies
  const handleSelectAll = () => {
    const allSelected = companies.every(c => c.personalization?.isSelected);
    setQualifiedCompanies(companies.map(c => ({
      ...c,
      personalization: { ...c.personalization!, isSelected: !allSelected },
    })));
  };

  const allSelected = companies.length > 0 && companies.every(c => c.personalization?.isSelected);
  const someSelected = companies.some(c => c.personalization?.isSelected) && !allSelected;

  const handleGenerate = (companyId: string) => {
    generatePersonalization(companyId);
  };

  const handleBulkGenerate = () => {
    const selectedIds = companies.filter(c => c.personalization?.isSelected).map(c => c.id);
    if (selectedIds.length > 0) {
      bulkGeneratePersonalization(selectedIds);
    }
  };

  const handleApprove = (companyId: string, type: 'message' | 'deck') => {
    approvePersonalization(companyId, type);
  };

  const handleReject = (companyId: string, type: 'message' | 'deck') => {
    rejectPersonalization(companyId, type);
  };

  const handleRegenerate = (companyId: string) => {
    generatePersonalization(companyId);
  };

  const handleEnroll = () => {
    if (state.selectedSequence) {
      const selectedIds = companies
        .filter(c => c.personalization?.isSelected)
        .map(c => c.id);
      enrollToSequence(selectedIds);
    }
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

  const readyForEnrollment = selectedCount > 0;

  return (
    <div className="step-container step-personalization">
      <div className="step-header">
        <h2>Personalization</h2>
        <p>Generate personalized messages and decks for each company</p>
      </div>

      {/* Stats Bar */}
      <div className="personalization-stats">
        <div className="stat">
          <span className="stat-value">{companies.length}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat synced">
          <span className="stat-value">{selectedCount}</span>
          <span className="stat-label">Selected</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bulk-actions">
        <button
          className="btn-primary btn-small"
          disabled={selectedCount === 0 || generatingCount > 0}
          onClick={handleBulkGenerate}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          Generate for Selected ({selectedCount})
        </button>
      </div>

      {/* Companies List with Select All Header */}
      <div className="personalization-companies-list">
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
          const isSelected = company.personalization?.isSelected;
          return (
            <div 
              key={company.id} 
              className={`personalization-company-card ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleCompanySelection(company.id)}
            >
              <div className="company-select" onClick={(e) => e.stopPropagation()}>
                <label className="checkbox-container">
                  <input 
                    type="checkbox"
                    checked={isSelected || false}
                    onChange={() => toggleCompanySelection(company.id)}
                  />
                  <span className="checkmark"></span>
                </label>
              </div>
              <div className="company-info">
                <h4>{company.name}</h4>
                <div className="company-meta">
                  <span className="tag">{company.industry}</span>
                  {getStatusBadge(company.personalization?.messageStatus)}
                </div>
              </div>
              <div className="company-actions" onClick={(e) => e.stopPropagation()}>
                {company.personalization?.messageStatus === 'pending' && (
                  <button
                    className="btn-primary btn-small"
                    onClick={() => handleGenerate(company.id)}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                    </svg>
                    Generate
                  </button>
                )}
                {company.personalization?.messageStatus === 'generating' && (
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
                    setExpandedCompany(expandedCompany === company.id ? null : company.id);
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
              </div>

              {/* Expanded Content */}
              {expandedCompany === company.id && (
              <div className="personalization-content">
                {/* Message Section */}
                <div className="personalization-section">
                  <div className="section-header">
                    <h5>Personalized Message</h5>
                    {getStatusBadge(company.personalization?.messageStatus)}
                  </div>
                  
                  {company.personalization?.messageStatus === 'generating' && (
                    <div className="generating-placeholder">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <p>AI is crafting a personalized message...</p>
                    </div>
                  )}

                  {(company.personalization?.messageStatus === 'generated' || company.personalization?.messageStatus === 'approved') && (
                    <div className="message-preview">
                      {editingMessage === company.id ? (
                        <textarea
                          value={manualMessage[company.id] || company.personalization?.message || ''}
                          onChange={(e) => setManualMessage(prev => ({ ...prev, [company.id]: e.target.value }))}
                          rows={6}
                        />
                      ) : (
                        <pre>{company.personalization?.message}</pre>
                      )}
                      
                      {company.personalization?.messageStatus !== 'approved' && (
                        <div className="review-actions">
                          <button className="btn-success btn-small" onClick={() => handleApprove(company.id, 'message')}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approve
                          </button>
                          <button className="btn-danger btn-small" onClick={() => handleReject(company.id, 'message')}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <line x1="18" y1="6" x2="6" y2="18"/>
                              <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                            Reject
                          </button>
                          <button className="btn-secondary btn-small" onClick={() => setEditingMessage(editingMessage === company.id ? null : company.id)}>
                            {editingMessage === company.id ? 'Cancel Edit' : 'Edit Manually'}
                          </button>
                          <div className="ai-review-badge coming-soon">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                            </svg>
                            AI Review - Coming Soon
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {company.personalization?.messageStatus === 'rejected' && (
                    <div className="rejected-content">
                      <p>Message was rejected. You can:</p>
                      <div className="rejection-actions">
                        <button className="btn-primary btn-small" onClick={() => handleRegenerate(company.id)}>
                          Regenerate
                        </button>
                        <button className="btn-secondary btn-small" onClick={() => setEditingMessage(company.id)}>
                          Type Manual Message
                        </button>
                      </div>
                      {editingMessage === company.id && (
                        <textarea
                          placeholder="Enter your custom message..."
                          value={manualMessage[company.id] || ''}
                          onChange={(e) => setManualMessage(prev => ({ ...prev, [company.id]: e.target.value }))}
                          rows={6}
                        />
                      )}
                    </div>
                  )}
                </div>

                {/* Deck Section */}
                <div className="personalization-section">
                  <div className="section-header">
                    <h5>Personalized Deck</h5>
                    {getStatusBadge(company.personalization?.deckStatus)}
                  </div>

                  {company.personalization?.deckStatus === 'generating' && (
                    <div className="generating-placeholder">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <p>AI is generating a personalized deck...</p>
                    </div>
                  )}

                  {(company.personalization?.deckStatus === 'generated' || company.personalization?.deckStatus === 'approved') && (
                    <div className="deck-preview">
                      <div className="deck-card">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                          <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        <span>personalized_deck_{company.name.toLowerCase().replace(/\s+/g, '_')}.pdf</span>
                        <a href={company.personalization?.deckUrl} target="_blank" rel="noopener noreferrer" className="btn-link">
                          View PDF
                        </a>
                      </div>

                      {company.personalization?.deckStatus !== 'approved' && (
                        <div className="review-actions">
                          <button className="btn-success btn-small" onClick={() => handleApprove(company.id, 'deck')}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approve
                          </button>
                          <button className="btn-danger btn-small" onClick={() => handleReject(company.id, 'deck')}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <line x1="18" y1="6" x2="6" y2="18"/>
                              <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {company.personalization?.deckStatus === 'rejected' && (
                    <div className="rejected-content">
                      <p>Deck was rejected. You can:</p>
                      <div className="rejection-actions">
                        <button className="btn-primary btn-small" onClick={() => handleRegenerate(company.id)}>
                          Regenerate
                        </button>
                        <button className="btn-secondary btn-small" onClick={() => setEditingDeck(company.id)}>
                          Attach Deck Manually
                        </button>
                      </div>
                      {editingDeck === company.id && (
                        <div className="manual-deck-input">
                          <input
                            type="url"
                            placeholder="Enter public URL to deck PDF..."
                            value={manualDeckUrl[company.id] || ''}
                            onChange={(e) => setManualDeckUrl(prev => ({ ...prev, [company.id]: e.target.value }))}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Enroll Modal */}
      {showEnrollModal && (
        <div className="modal-overlay" onClick={() => setShowEnrollModal(false)}>
          <div className="modal-content enroll-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Enroll Leads to Sequence</h3>
              <button className="modal-close" onClick={() => setShowEnrollModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div className="modal-body">
              <p>Select a Lemlist sequence to enroll {selectedCount} leads:</p>
              <div className="sequence-list">
                {MOCK_SEQUENCES.map((seq) => (
                  <div
                    key={seq.id}
                    className={`sequence-option ${state.selectedSequence === seq.id ? 'selected' : ''}`}
                    onClick={() => setSelectedSequence(seq.id)}
                  >
                    <div className="sequence-radio">
                      {state.selectedSequence === seq.id && (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <circle cx="12" cy="12" r="8"/>
                        </svg>
                      )}
                    </div>
                    <span>{seq.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowEnrollModal(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                disabled={!state.selectedSequence}
                onClick={handleEnroll}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                Enroll {selectedCount} Leads
              </button>
            </div>
          </div>
        </div>
      )}

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
          className="btn-primary btn-large enroll-btn"
          disabled={!readyForEnrollment}
          onClick={() => setShowEnrollModal(true)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          Enroll {selectedCount} Leads to Sequence
        </button>
      </div>
    </div>
  );
};

