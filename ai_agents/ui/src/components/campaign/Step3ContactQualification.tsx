import { useState } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';

const CONTACT_AI_QUESTIONS = [
  'Should the contact be in a decision-making role (Director/VP/C-level)?',
  'Should the contact have technical background?',
  'Should the contact be actively posting on LinkedIn?',
  'Should the contact have been in the role for at least 6 months?',
  'Should the contact be based in the same region as the company HQ?',
];

export const Step3ContactQualification = () => {
  const { 
    state, 
    setContactQualificationMode, 
    qualifyContact, 
    bulkQualifyContacts, 
    nextStep, 
    prevStep,
    setLoading,
    setQualifiedContacts,
  } = useCampaignWizard();

  const [aiQuestionsAnswers, setAiQuestionsAnswers] = useState<Record<string, boolean>>({});
  const [isQualifying, setIsQualifying] = useState(false);
  const [qualificationComplete, setQualificationComplete] = useState(false);
  const [activeTab, setActiveTab] = useState<'qualified' | 'rejected'>('qualified');
  const [rejectionReasons, setRejectionReasons] = useState<Record<string, string>>({});

  const contacts = state.qualifiedContacts;
  const qualifiedCount = contacts.filter(c => c.qualificationStatus === 'qualified').length;
  const rejectedCount = contacts.filter(c => c.qualificationStatus === 'rejected').length;

  // Get company name for a contact
  const getCompanyName = (companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  // Toggle single contact qualification via checkbox
  const toggleContactQualification = (contactId: string) => {
    const contact = contacts.find(c => c.id === contactId);
    if (contact) {
      const isCurrentlyQualified = contact.qualificationStatus === 'qualified';
      qualifyContact(contactId, !isCurrentlyQualified);
    }
  };

  // Select/Deselect all contacts
  const handleSelectAll = () => {
    const allQualified = contacts.every(c => c.qualificationStatus === 'qualified');
    bulkQualifyContacts(contacts.map(c => c.id), !allQualified);
  };

  const allSelected = contacts.length > 0 && contacts.every(c => c.qualificationStatus === 'qualified');
  const someSelected = contacts.some(c => c.qualificationStatus === 'qualified') && !allSelected;

  const handleAIQualification = async () => {
    setIsQualifying(true);
    setLoading(true, 'AI is qualifying contacts based on your criteria...', 0);

    // Simulate AI qualification process with animation
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 10) + 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
      }
      setLoading(true, `Analyzing contacts... ${Math.min(progress, 100)}%`, progress);
    }, 200);

    await new Promise(resolve => setTimeout(resolve, 3000));
    clearInterval(interval);

    // Mock rejection reasons for contacts
    const REJECTION_REASONS = [
      'Role level does not match decision-maker criteria',
      'Limited LinkedIn activity and engagement',
      'Recently joined the company (less than 6 months)',
      'Job title does not align with target persona',
      'No technical background detected',
      'Contact appears to be in a transitional role',
      'Email domain suggests personal account',
      'Profile indicates non-purchasing role',
    ];

    // Simulate AI qualification results
    const reasons: Record<string, string> = {};
    const updatedContacts = contacts.map(contact => {
      // Random qualification based on "AI analysis"
      const score = Math.random();
      const qualified = score > 0.35; // 65% qualification rate
      
      if (!qualified) {
        reasons[contact.id] = REJECTION_REASONS[Math.floor(Math.random() * REJECTION_REASONS.length)];
      }
      
      return {
        ...contact,
        qualificationStatus: qualified ? 'qualified' : 'rejected',
      } as Contact;
    });

    setRejectionReasons(reasons);
    setQualifiedContacts(updatedContacts);
    setLoading(false);
    setIsQualifying(false);
    setQualificationComplete(true);
  };

  const handleContinue = () => {
    // Filter only qualified contacts for next step
    const qualified = contacts.filter(c => c.qualificationStatus === 'qualified');
    setQualifiedContacts(qualified);
    nextStep();
  };

  return (
    <div className="step-container step-contact-qualification">
      <div className="step-header">
        <h2>Contact Qualification</h2>
        <p>Review and qualify contacts from your qualified companies</p>
      </div>

      {/* Loading Animation */}
      {state.isLoading && (
        <div className="loading-overlay">
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
            <h3>{state.loadingMessage}</h3>
            <div className="loading-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill ai-progress" 
                  style={{ width: `${state.estimatedCount}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Selection */}
      {!state.contactQualificationMode && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div 
              className="mode-card"
              onClick={() => setContactQualificationMode('manual')}
            >
              <div className="mode-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h4>Manual Qualification</h4>
              <p>Review each contact individually and decide if they qualify</p>
              <span className="mode-tag">Full Control</span>
            </div>
            <div 
              className="mode-card"
              onClick={() => setContactQualificationMode('ai')}
            >
              <div className="mode-icon ai">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                  <path d="M12 8v8"/>
                  <path d="M5 12h14"/>
                  <circle cx="5" cy="12" r="2"/>
                  <circle cx="19" cy="12" r="2"/>
                  <circle cx="12" cy="19" r="2"/>
                </svg>
              </div>
              <h4>AI Qualification</h4>
              <p>Let AI qualify contacts based on your custom criteria</p>
              <span className="mode-tag ai">Recommended</span>
            </div>
          </div>
        </div>
      )}

      {/* Manual Qualification */}
      {state.contactQualificationMode === 'manual' && (
        <div className="manual-qualification">
          {/* Stats Bar */}
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{contacts.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">{qualifiedCount}</span>
              <span className="stat-label">Selected</span>
            </div>
          </div>

          {/* Contacts List with Select All Header */}
          <div className="contacts-qualification-list">
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
                <span className="selected-count">({qualifiedCount} of {contacts.length} selected)</span>
              </span>
            </div>

            {/* Contacts */}
            {contacts.map((contact) => {
              const isQualified = contact.qualificationStatus === 'qualified';
              return (
                <div 
                  key={contact.id} 
                  className={`contact-qualification-card ${isQualified ? 'qualified' : ''}`}
                  onClick={() => toggleContactQualification(contact.id)}
                >
                  <div className="contact-select">
                    <label className="checkbox-container">
                      <input 
                        type="checkbox"
                        checked={isQualified}
                        onChange={() => toggleContactQualification(contact.id)}
                        onClick={(e) => e.stopPropagation()}
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
                  {isQualified && (
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
        </div>
      )}

      {/* AI Qualification */}
      {state.contactQualificationMode === 'ai' && !qualificationComplete && (
        <div className="ai-qualification">
          <div className="ai-questions-card">
            <h3>Define Contact Qualification Criteria</h3>
            <p>Answer these questions to help AI understand your ideal contact profile</p>
            
            <div className="ai-questions-list">
              {CONTACT_AI_QUESTIONS.map((question, index) => (
                <div key={index} className="ai-question">
                  <span className="question-text">{question}</span>
                  <div className="question-options">
                    <button
                      className={`option-btn ${aiQuestionsAnswers[question] === true ? 'selected yes' : ''}`}
                      onClick={() => setAiQuestionsAnswers(prev => ({ ...prev, [question]: true }))}
                    >
                      Yes
                    </button>
                    <button
                      className={`option-btn ${aiQuestionsAnswers[question] === false ? 'selected no' : ''}`}
                      onClick={() => setAiQuestionsAnswers(prev => ({ ...prev, [question]: false }))}
                    >
                      No
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <button 
              className="btn-primary btn-large"
              onClick={handleAIQualification}
              disabled={isQualifying || Object.keys(aiQuestionsAnswers).length < 3}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                <path d="M12 8v8"/>
              </svg>
              Run AI Qualification
            </button>
          </div>
        </div>
      )}

      {/* AI Qualification Results */}
      {state.contactQualificationMode === 'ai' && qualificationComplete && (
        <div className="ai-results">
          {/* Summary Cards - Also act as tab switchers */}
          <div className="results-summary">
            <div 
              className={`result-card success ${activeTab === 'qualified' ? 'active' : ''}`}
              onClick={() => setActiveTab('qualified')}
              role="button"
              tabIndex={0}
            >
              <div className="card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <h3>{qualifiedCount}</h3>
              <p>Qualified Contacts</p>
            </div>
            <div 
              className={`result-card danger ${activeTab === 'rejected' ? 'active' : ''}`}
              onClick={() => setActiveTab('rejected')}
              role="button"
              tabIndex={0}
            >
              <div className="card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
              </div>
              <h3>{rejectedCount}</h3>
              <p>Rejected</p>
            </div>
          </div>

          {/* Qualified Contacts Tab */}
          {activeTab === 'qualified' && (
            <div className="contacts-tab-content">
              {contacts.filter(c => c.qualificationStatus === 'qualified').length === 0 ? (
                <div className="empty-state">
                  <p>No qualified contacts yet</p>
                </div>
              ) : (
                contacts.filter(c => c.qualificationStatus === 'qualified').map((contact) => (
                  <div key={contact.id} className="contact-result-card qualified">
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
                    <span className="status-badge qualified">✓ Qualified</span>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Rejected Contacts Tab */}
          {activeTab === 'rejected' && (
            <div className="contacts-tab-content">
              {contacts.filter(c => c.qualificationStatus === 'rejected').length === 0 ? (
                <div className="empty-state">
                  <p>No rejected contacts</p>
                </div>
              ) : (
                contacts.filter(c => c.qualificationStatus === 'rejected').map((contact) => (
                  <div key={contact.id} className="contact-result-card rejected">
                    <div className="contact-avatar">
                      {contact.firstName[0]}{contact.lastName[0]}
                    </div>
                    <div className="contact-info">
                      <h4>{contact.firstName} {contact.lastName}</h4>
                      <div className="contact-meta">
                        <span className="job-title">{contact.jobTitle}</span>
                        <span className="company-name">{getCompanyName(contact.companyId)}</span>
                      </div>
                      <div className="rejection-reason">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="12" y1="8" x2="12" y2="12"/>
                          <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <span>{rejectionReasons[contact.id] || 'Does not meet qualification criteria'}</span>
                      </div>
                    </div>
                    <button 
                      className="btn-override"
                      onClick={() => qualifyContact(contact.id, true)}
                      title="Override AI decision and qualify this contact"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Qualify
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="step-navigation">
        <button className="btn-secondary" onClick={() => {
          setContactQualificationMode(null);
          setQualificationComplete(false);
          prevStep();
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        
        {state.contactQualificationMode && (
          <button className="btn-secondary" onClick={() => {
            setContactQualificationMode(null);
            setQualificationComplete(false);
          }}>
            Change Method
          </button>
        )}

        {qualifiedCount > 0 && (
          <button className="btn-primary btn-large" onClick={handleContinue}>
            Continue with {qualifiedCount} Contacts
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

