import { useState } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

const AI_QUESTIONS = [
  'Does the company have a dedicated IT/Engineering team?',
  'Is the company actively hiring for technical roles?',
  'Does the company use cloud-based solutions?',
  'Has the company raised funding in the last 2 years?',
  'Is the company in a growth phase (expanding operations)?',
];

export const Step2CompanyQualification = () => {
  const { 
    state, 
    setCompanyQualificationMode, 
    qualifyCompany, 
    bulkQualify, 
    nextStep, 
    prevStep,
    setLoading,
    setQualifiedCompanies,
    setQualifiedContacts,
  } = useCampaignWizard();

  const [aiQuestionsAnswers, setAiQuestionsAnswers] = useState<Record<string, boolean>>({});
  const [isQualifying, setIsQualifying] = useState(false);
  const [qualificationComplete, setQualificationComplete] = useState(false);
  const [activeTab, setActiveTab] = useState<'qualified' | 'rejected'>('qualified');
  const [rejectionReasons, setRejectionReasons] = useState<Record<string, string>>({});

  const companies = state.qualifiedCompanies;
  const qualifiedCount = companies.filter(c => c.qualificationStatus === 'qualified').length;
  const rejectedCount = companies.filter(c => c.qualificationStatus === 'rejected').length;

  // Toggle single company qualification via checkbox
  const toggleCompanyQualification = (companyId: string) => {
    const company = companies.find(c => c.id === companyId);
    if (company) {
      const isCurrentlyQualified = company.qualificationStatus === 'qualified';
      qualifyCompany(companyId, !isCurrentlyQualified);
    }
  };

  // Select/Deselect all companies
  const handleSelectAll = () => {
    const allQualified = companies.every(c => c.qualificationStatus === 'qualified');
    bulkQualify(companies.map(c => c.id), !allQualified);
  };

  const allSelected = companies.length > 0 && companies.every(c => c.qualificationStatus === 'qualified');
  const someSelected = companies.some(c => c.qualificationStatus === 'qualified') && !allSelected;

  const handleAIQualification = async () => {
    setIsQualifying(true);
    setLoading(true, 'AI is qualifying leads based on your criteria...', 0);

    // Simulate AI qualification process with animation
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 10) + 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
      }
      setLoading(true, `Analyzing companies... ${Math.min(progress, 100)}%`, progress);
    }, 200);

    await new Promise(resolve => setTimeout(resolve, 3000));
    clearInterval(interval);

    // Mock rejection reasons
    const REJECTION_REASONS = [
      'Employee count below target threshold',
      'Industry not aligned with ICP criteria',
      'Revenue below minimum requirement',
      'Geographic region outside target market',
      'No recent funding or growth signals detected',
      'Company appears to be in decline phase',
      'Limited online presence and engagement',
      'Tech stack mismatch with product offering',
    ];

    // Simulate AI qualification results
    const reasons: Record<string, string> = {};
    const updatedCompanies = companies.map(company => {
      // Random qualification based on "AI analysis"
      const score = Math.random();
      const qualified = score > 0.4; // 60% qualification rate
      
      if (!qualified) {
        // Assign a random rejection reason
        reasons[company.id] = REJECTION_REASONS[Math.floor(Math.random() * REJECTION_REASONS.length)];
      }
      
      return {
        ...company,
        isQualified: qualified,
        qualificationStatus: qualified ? 'qualified' : 'rejected',
      } as typeof company;
    });

    setRejectionReasons(reasons);
    setQualifiedCompanies(updatedCompanies);
    setLoading(false);
    setIsQualifying(false);
    setQualificationComplete(true);
  };

  const handleContinue = () => {
    // Filter only qualified companies for next step
    const qualified = companies.filter(c => c.qualificationStatus === 'qualified');
    setQualifiedCompanies(qualified);
    
    // Extract contacts from qualified companies for contact qualification
    const contacts = qualified.flatMap(company => 
      company.contacts.map(contact => ({
        ...contact,
        qualificationStatus: 'pending' as const,
        syncStatus: 'not_synced' as const,
      }))
    );
    setQualifiedContacts(contacts);
    nextStep();
  };

  return (
    <div className="step-container step-company-qualification">
      <div className="step-header">
        <h2>Company Qualification</h2>
        <p>Review and qualify companies before proceeding to contact qualification</p>
      </div>

      {/* Loading Animation */}
      {state.isLoading && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation ai-animation">
              <div className="ai-brain">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                  <path d="M12 8v8"/>
                  <path d="M5 12h14"/>
                  <circle cx="5" cy="12" r="2"/>
                  <circle cx="19" cy="12" r="2"/>
                  <circle cx="12" cy="19" r="2"/>
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
      {!state.companyQualificationMode && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div 
              className="mode-card"
              onClick={() => setCompanyQualificationMode('manual')}
            >
              <div className="mode-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h4>Manual Qualification</h4>
              <p>Review each company individually and decide if they qualify as a lead</p>
              <span className="mode-tag">Full Control</span>
            </div>
            <div 
              className="mode-card"
              onClick={() => setCompanyQualificationMode('ai')}
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
              <p>Let AI qualify leads based on your custom criteria questions</p>
              <span className="mode-tag ai">Recommended</span>
            </div>
          </div>
        </div>
      )}

      {/* Manual Qualification */}
      {state.companyQualificationMode === 'manual' && (
        <div className="manual-qualification">
          {/* Stats Bar */}
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{companies.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">{qualifiedCount}</span>
              <span className="stat-label">Selected</span>
            </div>
          </div>

          {/* Companies List with Select All Header */}
          <div className="companies-qualification-list">
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
                <span className="selected-count">({qualifiedCount} of {companies.length} selected)</span>
              </span>
            </div>

            {/* Companies */}
            {companies.map((company) => {
              const isQualified = company.qualificationStatus === 'qualified';
              return (
                <div 
                  key={company.id} 
                  className={`company-qualification-card ${isQualified ? 'qualified' : ''}`}
                  onClick={() => toggleCompanyQualification(company.id)}
                >
                  <div className="company-select">
                    <label className="checkbox-container">
                      <input 
                        type="checkbox"
                        checked={isQualified}
                        onChange={() => toggleCompanyQualification(company.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="checkmark"></span>
                    </label>
                  </div>
                  <div className="company-info">
                    <h4>{company.name}</h4>
                    <div className="company-meta">
                      <span className="tag">{company.industry}</span>
                      <span className="tag">{company.location}</span>
                      <span className="tag">{company.revenue}</span>
                      <span className="tag">{company.contacts.length} contacts</span>
                    </div>
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
      {state.companyQualificationMode === 'ai' && !qualificationComplete && (
        <div className="ai-qualification">
          <div className="ai-questions-card">
            <h3>Define Qualification Criteria</h3>
            <p>Answer these questions to help AI understand your ideal customer profile</p>
            
            <div className="ai-questions-list">
              {AI_QUESTIONS.map((question, index) => (
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
      {state.companyQualificationMode === 'ai' && qualificationComplete && (
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
              <p>Qualified Leads</p>
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

          {/* Qualified Companies Tab */}
          {activeTab === 'qualified' && (
            <div className="companies-tab-content">
              {companies.filter(c => c.qualificationStatus === 'qualified').length === 0 ? (
                <div className="empty-state">
                  <p>No qualified companies yet</p>
                </div>
              ) : (
                companies.filter(c => c.qualificationStatus === 'qualified').map((company) => (
                  <div key={company.id} className="company-result-card qualified">
                    <div className="company-info">
                      <h4>{company.name}</h4>
                      <div className="company-meta">
                        <span className="tag">{company.industry}</span>
                        <span className="tag">{company.location}</span>
                        <span className="tag">{company.employeeCount} employees</span>
                      </div>
                    </div>
                    <span className="status-badge qualified">✓ Qualified</span>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Rejected Companies Tab */}
          {activeTab === 'rejected' && (
            <div className="companies-tab-content">
              {companies.filter(c => c.qualificationStatus === 'rejected').length === 0 ? (
                <div className="empty-state">
                  <p>No rejected companies</p>
                </div>
              ) : (
                companies.filter(c => c.qualificationStatus === 'rejected').map((company) => (
                  <div key={company.id} className="company-result-card rejected">
                    <div className="company-info">
                      <h4>{company.name}</h4>
                      <div className="company-meta">
                        <span className="tag">{company.industry}</span>
                        <span className="tag">{company.location}</span>
                        <span className="tag">{company.employeeCount} employees</span>
                      </div>
                      <div className="rejection-reason">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="12" y1="8" x2="12" y2="12"/>
                          <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <span>{rejectionReasons[company.id] || 'Does not meet qualification criteria'}</span>
                      </div>
                    </div>
                    <button 
                      className="btn-override"
                      onClick={() => qualifyCompany(company.id, true)}
                      title="Override AI decision and qualify this company"
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
          setCompanyQualificationMode(null);
          setQualificationComplete(false);
          prevStep();
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        
        {state.companyQualificationMode && (
          <button className="btn-secondary" onClick={() => {
            setCompanyQualificationMode(null);
            setQualificationComplete(false);
          }}>
            Change Method
          </button>
        )}

        {qualifiedCount > 0 && (
          <button className="btn-primary btn-large" onClick={handleContinue}>
            Continue with {qualifiedCount} Selected
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

