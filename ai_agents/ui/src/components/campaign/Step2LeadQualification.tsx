import { useState } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

const AI_QUESTIONS = [
  'Does the company have a dedicated IT/Engineering team?',
  'Is the company actively hiring for technical roles?',
  'Does the company use cloud-based solutions?',
  'Has the company raised funding in the last 2 years?',
  'Is the company in a growth phase (expanding operations)?',
];

export const Step2LeadQualification = () => {
  const { 
    state, 
    setQualificationMode, 
    qualifyCompany, 
    bulkQualify, 
    nextStep, 
    prevStep,
    setLoading,
    setQualifiedCompanies,
  } = useCampaignWizard();

  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [aiQuestionsAnswers, setAiQuestionsAnswers] = useState<Record<string, boolean>>({});
  const [isQualifying, setIsQualifying] = useState(false);
  const [qualificationComplete, setQualificationComplete] = useState(false);

  const companies = state.qualifiedCompanies;
  const qualifiedCount = companies.filter(c => c.qualificationStatus === 'qualified').length;
  const rejectedCount = companies.filter(c => c.qualificationStatus === 'rejected').length;
  const pendingCount = companies.filter(c => c.qualificationStatus === 'pending').length;

  const toggleSelectCompany = (companyId: string) => {
    setSelectedCompanies(prev => 
      prev.includes(companyId) 
        ? prev.filter(id => id !== companyId)
        : [...prev, companyId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedCompanies.length === companies.length) {
      setSelectedCompanies([]);
    } else {
      setSelectedCompanies(companies.map(c => c.id));
    }
  };

  const handleBulkQualify = (qualified: boolean) => {
    if (selectedCompanies.length > 0) {
      bulkQualify(selectedCompanies, qualified);
      setSelectedCompanies([]);
    }
  };

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

    // Simulate AI qualification results
    const updatedCompanies = companies.map(company => {
      // Random qualification based on "AI analysis"
      const score = Math.random();
      const qualified = score > 0.4; // 60% qualification rate
      return {
        ...company,
        isQualified: qualified,
        qualificationStatus: qualified ? 'qualified' : 'rejected',
      } as typeof company;
    });

    setQualifiedCompanies(updatedCompanies);
    setLoading(false);
    setIsQualifying(false);
    setQualificationComplete(true);
  };

  const handleContinue = () => {
    // Filter only qualified companies for next step
    const qualified = companies.filter(c => c.qualificationStatus === 'qualified');
    setQualifiedCompanies(qualified);
    nextStep();
  };

  return (
    <div className="step-container step-lead-qualification">
      <div className="step-header">
        <h2>Lead Qualification</h2>
        <p>Review and qualify your prospects before syncing to CRM</p>
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
      {!state.qualificationMode && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div 
              className="mode-card"
              onClick={() => setQualificationMode('manual')}
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
              onClick={() => setQualificationMode('ai')}
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
      {state.qualificationMode === 'manual' && (
        <div className="manual-qualification">
          {/* Stats Bar */}
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{companies.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">{qualifiedCount}</span>
              <span className="stat-label">Qualified</span>
            </div>
            <div className="stat rejected">
              <span className="stat-value">{rejectedCount}</span>
              <span className="stat-label">Rejected</span>
            </div>
            <div className="stat pending">
              <span className="stat-value">{pendingCount}</span>
              <span className="stat-label">Pending</span>
            </div>
          </div>

          {/* Bulk Actions */}
          <div className="bulk-actions">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={selectedCompanies.length === companies.length && companies.length > 0}
                onChange={toggleSelectAll}
              />
              Select All ({selectedCompanies.length} selected)
            </label>
            <div className="bulk-buttons">
              <button 
                className="btn-success btn-small"
                disabled={selectedCompanies.length === 0}
                onClick={() => handleBulkQualify(true)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Qualify Selected
              </button>
              <button 
                className="btn-danger btn-small"
                disabled={selectedCompanies.length === 0}
                onClick={() => handleBulkQualify(false)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                Reject Selected
              </button>
            </div>
          </div>

          {/* Companies List */}
          <div className="companies-qualification-list">
            {companies.map((company) => (
              <div 
                key={company.id} 
                className={`company-qualification-card ${company.qualificationStatus}`}
              >
                <div className="company-select">
                  <input 
                    type="checkbox"
                    checked={selectedCompanies.includes(company.id)}
                    onChange={() => toggleSelectCompany(company.id)}
                  />
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
                <div className="company-actions">
                  {company.qualificationStatus === 'pending' ? (
                    <>
                      <button 
                        className="btn-icon btn-success"
                        onClick={() => qualifyCompany(company.id, true)}
                        title="Qualify"
                      >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      </button>
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => qualifyCompany(company.id, false)}
                        title="Reject"
                      >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"/>
                          <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </>
                  ) : (
                    <span className={`status-badge ${company.qualificationStatus}`}>
                      {company.qualificationStatus === 'qualified' ? '✓ Qualified' : '✗ Rejected'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Qualification */}
      {state.qualificationMode === 'ai' && !qualificationComplete && (
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
      {state.qualificationMode === 'ai' && qualificationComplete && (
        <div className="ai-results">
          <div className="results-summary">
            <div className="result-card success">
              <h3>{qualifiedCount}</h3>
              <p>Qualified Leads</p>
            </div>
            <div className="result-card danger">
              <h3>{rejectedCount}</h3>
              <p>Rejected</p>
            </div>
          </div>

          <div className="qualified-companies-list">
            <h3>Qualified Companies</h3>
            {companies.filter(c => c.qualificationStatus === 'qualified').map((company) => (
              <div key={company.id} className="company-result-card qualified">
                <div className="company-info">
                  <h4>{company.name}</h4>
                  <div className="company-meta">
                    <span className="tag">{company.industry}</span>
                    <span className="tag">{company.location}</span>
                  </div>
                </div>
                <span className="status-badge qualified">✓ Qualified</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="step-navigation">
        <button className="btn-secondary" onClick={() => {
          setQualificationMode(null);
          setQualificationComplete(false);
          prevStep();
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        
        {state.qualificationMode && (
          <button className="btn-secondary" onClick={() => {
            setQualificationMode(null);
            setQualificationComplete(false);
          }}>
            Change Method
          </button>
        )}

        {(qualifiedCount > 0 || (state.qualificationMode === 'manual' && pendingCount === 0)) && (
          <button className="btn-primary btn-large" onClick={handleContinue}>
            Continue with {qualifiedCount} Qualified Leads
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

