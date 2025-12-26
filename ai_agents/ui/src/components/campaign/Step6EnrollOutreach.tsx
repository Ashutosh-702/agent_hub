import { useState } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';

const MOCK_SEQUENCES = [
  { 
    id: 'seq-1', 
    name: 'Enterprise Outreach - Q1 2025',
    description: 'Multi-touch sequence for enterprise prospects with personalized follow-ups',
    steps: 5,
    avgOpenRate: 42,
    avgReplyRate: 8,
  },
  { 
    id: 'seq-2', 
    name: 'SMB Cold Outreach',
    description: 'Quick and direct sequence for small and medium businesses',
    steps: 3,
    avgOpenRate: 38,
    avgReplyRate: 12,
  },
  { 
    id: 'seq-3', 
    name: 'Healthcare Decision Makers',
    description: 'Tailored sequence for healthcare industry executives',
    steps: 4,
    avgOpenRate: 35,
    avgReplyRate: 6,
  },
  { 
    id: 'seq-4', 
    name: 'Tech Founders Sequence',
    description: 'Casual, founder-to-founder outreach for tech startups',
    steps: 4,
    avgOpenRate: 45,
    avgReplyRate: 15,
  },
  { 
    id: 'seq-5', 
    name: 'Re-engagement Campaign',
    description: 'Win-back sequence for previously contacted prospects',
    steps: 3,
    avgOpenRate: 28,
    avgReplyRate: 5,
  },
];

export const Step6EnrollOutreach = () => {
  const {
    state,
    setSelectedSequence,
    enrollToSequence,
    prevStep,
  } = useCampaignWizard();

  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrollmentComplete, setEnrollmentComplete] = useState(false);

  const contacts = state.qualifiedContacts;
  const selectedSequence = MOCK_SEQUENCES.find(s => s.id === state.selectedSequence);

  // Get company name for a contact
  const getCompanyName = (companyId: string) => {
    const company = state.qualifiedCompanies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  const handleEnroll = async () => {
    if (!state.selectedSequence) return;
    
    setIsEnrolling(true);
    
    // Simulate enrollment
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    setIsEnrolling(false);
    setEnrollmentComplete(true);
  };

  const handleViewInLemlist = () => {
    // Open Lemlist in new tab (mock URL)
    window.open('https://app.lemlist.com/campaigns', '_blank');
  };

  // Enrollment complete view
  if (enrollmentComplete) {
    return (
      <div className="step-container step-enroll-outreach">
        <div className="enrollment-success">
          <div className="success-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <h2>Contacts Enrolled Successfully!</h2>
          <p>{contacts.length} contacts have been enrolled to "{selectedSequence?.name}"</p>
          
          <div className="enrollment-summary">
            <div className="summary-card">
              <h4>Enrolled Contacts</h4>
              <span className="value">{contacts.length}</span>
            </div>
            <div className="summary-card">
              <h4>Sequence</h4>
              <span className="value">{selectedSequence?.name}</span>
            </div>
            <div className="summary-card">
              <h4>Expected Steps</h4>
              <span className="value">{selectedSequence?.steps}</span>
            </div>
          </div>

          <div className="success-actions">
            <button className="btn-primary btn-large" onClick={handleViewInLemlist}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              View in Lemlist
            </button>
            <button className="btn-secondary" onClick={() => window.location.href = '/campaign'}>
              Back to Campaigns
            </button>
          </div>

          <div className="lemlist-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>You can track the outreach progress and manage responses in your Lemlist dashboard</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="step-container step-enroll-outreach">
      <div className="step-header">
        <h2>Enroll for Outreach</h2>
        <p>Select a Lemlist sequence to enroll {contacts.length} contacts for outreach</p>
      </div>

      {/* Loading State */}
      {isEnrolling && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>Enrolling contacts to sequence...</h3>
            <p>This may take a few moments</p>
          </div>
        </div>
      )}

      {/* Contacts Preview */}
      <div className="enrollment-preview">
        <h3>Contacts to Enroll ({contacts.length})</h3>
        <div className="contacts-preview-grid">
          {contacts.slice(0, 6).map((contact) => (
            <div key={contact.id} className="contact-preview-card">
              <div className="contact-avatar">
                {contact.firstName[0]}{contact.lastName[0]}
              </div>
              <div className="contact-info">
                <span className="contact-name">{contact.firstName} {contact.lastName}</span>
                <span className="contact-company">{getCompanyName(contact.companyId)}</span>
              </div>
            </div>
          ))}
          {contacts.length > 6 && (
            <div className="more-contacts-indicator">
              +{contacts.length - 6} more contacts
            </div>
          )}
        </div>
      </div>

      {/* Sequence Selection */}
      <div className="sequence-selection">
        <h3>Select Lemlist Sequence</h3>
        <div className="sequence-list">
          {MOCK_SEQUENCES.map((seq) => (
            <div
              key={seq.id}
              className={`sequence-card ${state.selectedSequence === seq.id ? 'selected' : ''}`}
              onClick={() => setSelectedSequence(seq.id)}
            >
              <div className="sequence-radio">
                <div className={`radio-circle ${state.selectedSequence === seq.id ? 'checked' : ''}`}>
                  {state.selectedSequence === seq.id && (
                    <div className="radio-dot" />
                  )}
                </div>
              </div>
              <div className="sequence-info">
                <h4>{seq.name}</h4>
                <p>{seq.description}</p>
                <div className="sequence-stats">
                  <span className="stat">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    {seq.steps} steps
                  </span>
                  <span className="stat">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                      <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    {seq.avgOpenRate}% open rate
                  </span>
                  <span className="stat">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                    </svg>
                    {seq.avgReplyRate}% reply rate
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Sequence Details */}
      {selectedSequence && (
        <div className="selected-sequence-details">
          <h3>Sequence Details</h3>
          <div className="sequence-detail-card">
            <div className="detail-header">
              <h4>{selectedSequence.name}</h4>
              <span className="selected-badge">Selected</span>
            </div>
            <p>{selectedSequence.description}</p>
            <div className="detail-stats">
              <div className="detail-stat">
                <span className="label">Total Steps</span>
                <span className="value">{selectedSequence.steps}</span>
              </div>
              <div className="detail-stat">
                <span className="label">Avg. Open Rate</span>
                <span className="value">{selectedSequence.avgOpenRate}%</span>
              </div>
              <div className="detail-stat">
                <span className="label">Avg. Reply Rate</span>
                <span className="value">{selectedSequence.avgReplyRate}%</span>
              </div>
              <div className="detail-stat">
                <span className="label">Contacts to Enroll</span>
                <span className="value">{contacts.length}</span>
              </div>
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
          disabled={!state.selectedSequence || isEnrolling}
          onClick={handleEnroll}
        >
          {isEnrolling ? (
            <>
              <div className="spinner" />
              Enrolling...
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Enroll {contacts.length} Contacts to Sequence
            </>
          )}
        </button>
      </div>
    </div>
  );
};

