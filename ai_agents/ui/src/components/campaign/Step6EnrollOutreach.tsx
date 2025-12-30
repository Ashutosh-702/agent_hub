import { useState, useEffect } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import { useLazyGetEnrollmentContactsQuery, useEnrollContactsToSequenceMutation } from '../../store';

import { MOCK_LEMLIST_SEQUENCES as MOCK_SEQUENCES } from '../../store/api/wizardMockData';

interface EnrollmentContact {
  campaign_contact_run_id: string;
  campaign_id: string;
  company_id: string | null;
  contact_id: string | null;
  is_relevant: boolean;
  enrichment_status: string | null;
  personalization_status: string;
  personalized_message: string;
  ai_generated_deck: string;
  email_id: string;
  campaign_contact_run_metadata: Record<string, unknown>;
  contact_data: {
    firstname: string;
    lastname: string;
    email: string[];
    phone: string[];
    jobtitle: string;
    company: string;
    source_id: string;
  } | null;
  linkedin_data: {
    linkedin_url: string | null;
    source: string;
  } | null;
  contact_metadata: Record<string, unknown> | null;
  company_data: {
    name: string | null;
    domain: string | null;
    website: string | null;
    industry: string | null;
    employee_count: string | null;
    revenue: string | null;
    location: string | null;
    description: string | null;
    company_metadata: Record<string, unknown> | null;
  } | null;
}

export const Step6EnrollOutreach = () => {
  const {
    state,
    setSelectedSequence,
    prevStep,
  } = useCampaignWizard();

  const [isLoading, setIsLoading] = useState(true);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrollmentComplete, setEnrollmentComplete] = useState(false);
  const [enrollmentError, setEnrollmentError] = useState<string | null>(null);
  const [enrollmentContacts, setEnrollmentContacts] = useState<EnrollmentContact[]>([]);
  const [enrolledContactsData, setEnrolledContactsData] = useState<unknown[]>([]);

  const campaignId = state.campaignId || '';
  const selectedSequence = MOCK_SEQUENCES.find(s => s.id === state.selectedSequence);

  // RTK Query hooks
  const [fetchEnrollmentContacts] = useLazyGetEnrollmentContactsQuery();
  const [enrollContactsToSequence] = useEnrollContactsToSequenceMutation();

  // Fetch contacts on mount
  useEffect(() => {
    const loadContacts = async () => {
      if (!campaignId) {
        setIsLoading(false);
        return;
      }

      try {
        const result = await fetchEnrollmentContacts({ campaign_id: campaignId, limit: 500 }).unwrap();
        if (result.success && result.data.contacts) {
          setEnrollmentContacts(result.data.contacts);
        }
      } catch (error) {
        console.error('Failed to fetch enrollment contacts:', error);
        setEnrollmentError('Failed to load contacts. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadContacts();
  }, [campaignId, fetchEnrollmentContacts]);

  // Get company name for a contact
  const getCompanyName = (contact: EnrollmentContact) => {
    return contact.company_data?.name || contact.contact_data?.company || 'Unknown Company';
  };

  const handleEnroll = async () => {
    if (!state.selectedSequence || !campaignId) return;
    
    const sequence = MOCK_SEQUENCES.find(s => s.id === state.selectedSequence);
    if (!sequence) return;

    setIsEnrolling(true);
    setEnrollmentError(null);
    
    try {
      const result = await enrollContactsToSequence({
        campaign_id: campaignId,
        sequence_id: sequence.id,
        sequence_name: sequence.name,
      }).unwrap();

      if (result.success) {
        setEnrolledContactsData(result.data.enrolled_contacts);
        setEnrollmentComplete(true);
      }
    } catch (error) {
      console.error('Failed to enroll contacts:', error);
      setEnrollmentError('Failed to enroll contacts. Please try again.');
    } finally {
      setIsEnrolling(false);
    }
  };

  const handleViewInLemlist = () => {
    // Open Lemlist in new tab (mock URL)
    window.open('https://app.lemlist.com/campaigns', '_blank');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="step-container step-enroll-outreach">
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>Loading contacts for enrollment...</h3>
          </div>
        </div>
      </div>
    );
  }

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
          <p>{enrollmentContacts.length} contacts have been enrolled to "{selectedSequence?.name}"</p>
          
          <div className="enrollment-summary">
            <div className="summary-card">
              <h4>Enrolled Contacts</h4>
              <span className="value">{enrollmentContacts.length}</span>
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

          {/* Enrolled Contacts Data Preview */}
          <div className="enrolled-data-preview">
            <h3>Enrolled Contact Data (sent to sequence)</h3>
            <p className="data-info">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              Full contact details including all metadata were sent to the sequence
            </p>
            <div className="enrolled-data-grid">
              {(enrolledContactsData as Array<Record<string, unknown>>).slice(0, 3).map((contact, idx) => (
                <div key={idx} className="enrolled-contact-card">
                  <div className="contact-header">
                    <div className="contact-avatar">
                      {(contact.first_name as string)?.[0] || '?'}{(contact.last_name as string)?.[0] || '?'}
                    </div>
                    <div className="contact-basic">
                      <h4>{String(contact.first_name || '')} {String(contact.last_name || '')}</h4>
                      <span>{String(contact.job_title || '')}</span>
                    </div>
                  </div>
                  <div className="contact-details">
                    <div className="detail-row">
                      <span className="label">Email:</span>
                      <span className="value">{contact.email as string}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Company:</span>
                      <span className="value">{contact.company_name as string}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Personalized:</span>
                      <span className="value success">✓ Message & Deck</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Metadata:</span>
                      <span className="value success">✓ Included</span>
                    </div>
                  </div>
                </div>
              ))}
              {(enrolledContactsData as unknown[]).length > 3 && (
                <div className="more-contacts-indicator">
                  +{(enrolledContactsData as unknown[]).length - 3} more contacts enrolled with full data
                </div>
              )}
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
            <button className="btn-secondary" onClick={() => window.location.href = '/prospecting/campaigns'}>
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
        <p>Select a Lemlist sequence to enroll {enrollmentContacts.length} contacts for outreach</p>
      </div>

      {/* Error Banner */}
      {enrollmentError && (
        <div className="sync-error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{enrollmentError}</span>
          <button className="btn-icon" onClick={() => setEnrollmentError(null)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      )}

      {/* Loading State */}
      {isEnrolling && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation">
              <div className="spinner large" />
            </div>
            <h3>Enrolling contacts to sequence...</h3>
            <p>Sending full contact details with metadata to Lemlist</p>
          </div>
        </div>
      )}

      {/* Contacts Preview */}
      <div className="enrollment-preview">
        <h3>Contacts to Enroll ({enrollmentContacts.length})</h3>
        <p className="enrollment-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Full contact data including personalized message, AI deck, and all metadata will be sent
        </p>
        <div className="contacts-preview-grid">
          {enrollmentContacts.slice(0, 6).map((contact) => (
            <div key={contact.campaign_contact_run_id} className="contact-preview-card">
              <div className="contact-avatar">
                {contact.contact_data?.firstname?.[0] || '?'}{contact.contact_data?.lastname?.[0] || '?'}
              </div>
              <div className="contact-info">
                <span className="contact-name">
                  {contact.contact_data?.firstname} {contact.contact_data?.lastname}
                </span>
                <span className="contact-company">{getCompanyName(contact)}</span>
                <span className="contact-email">{contact.email_id}</span>
              </div>
              <div className="contact-badges">
                {contact.personalized_message && (
                  <span className="badge success" title="Personalized message included">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Message
                  </span>
                )}
                {contact.ai_generated_deck && (
                  <span className="badge success" title="AI deck included">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Deck
                  </span>
                )}
              </div>
            </div>
          ))}
          {enrollmentContacts.length > 6 && (
            <div className="more-contacts-indicator">
              +{enrollmentContacts.length - 6} more contacts
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
                <span className="value">{enrollmentContacts.length}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Preview Info */}
      <div className="data-preview-section">
        <h3>Data to be Sent</h3>
        <div className="data-preview-info">
          <div className="data-category">
            <h5>Contact Information</h5>
            <ul>
              <li>Email, Name, Job Title</li>
              <li>Phone Numbers</li>
              <li>LinkedIn URL</li>
            </ul>
          </div>
          <div className="data-category">
            <h5>Company Information</h5>
            <ul>
              <li>Company Name, Domain</li>
              <li>Industry, Size</li>
              <li>Location</li>
            </ul>
          </div>
          <div className="data-category">
            <h5>Personalization</h5>
            <ul>
              <li>Personalized Message</li>
              <li>AI Generated Deck URL</li>
            </ul>
          </div>
          <div className="data-category">
            <h5>All Metadata</h5>
            <ul>
              <li>Contact Metadata</li>
              <li>Company Metadata</li>
              <li>Campaign Run Metadata</li>
            </ul>
          </div>
        </div>
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
          className="btn-primary btn-large enroll-btn"
          disabled={!state.selectedSequence || isEnrolling || enrollmentContacts.length === 0}
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
              Enroll {enrollmentContacts.length} Contacts to Sequence
            </>
          )}
        </button>
      </div>
    </div>
  );
};
