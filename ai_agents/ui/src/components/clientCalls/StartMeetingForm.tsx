import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, BackButton } from '../shared';
import { PRODUCTS } from './mockData';
import { SearchableCompanySelect } from './SearchableCompanySelect';
import { useLazyGetCompanyDetailsQuery } from '../../store/api/companyApi';

// Re-export PRODUCTS for backward compatibility
export { PRODUCTS };

interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  jobTitle: string;
  email?: string;
}

export const StartMeetingForm = () => {
  const navigate = useNavigate();
  
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [callType, setCallType] = useState<'google_meeting' | 'phone_call' | 'in_person' | ''>('');
  const [meetingName, setMeetingName] = useState('');
  const [notes, setNotes] = useState('');
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  
  // Use real API to fetch contacts
  const [fetchCompanyDetails, { isLoading: isLoadingContacts }] = useLazyGetCompanyDetailsQuery();
  
  // Fetch contacts when company changes
  useEffect(() => {
    if (selectedCompany) {
      fetchCompanyDetails({ company_id: selectedCompany, page: 1, limit: 100 })
        .unwrap()
        .then((response) => {
          // Transform API contacts to component format
          const transformedContacts: Contact[] = response.data.contacts.map((c) => ({
            id: c._id,
            firstName: c.contact_data?.firstname || '',
            lastName: c.contact_data?.lastname || '',
            jobTitle: c.contact_data?.jobtitle || '',
            email: c.contact_data?.email?.[0] || '',
          }));
          setContacts(transformedContacts);
          setSelectedContacts([]);
        })
        .catch((err) => {
          console.error('Failed to fetch contacts:', err);
          setContacts([]);
        });
    } else {
      setContacts([]);
    }
  }, [selectedCompany, fetchCompanyDetails]);
  
  const handleContactToggle = (contactId: string) => {
    setSelectedContacts(prev => 
      prev.includes(contactId)
        ? prev.filter(id => id !== contactId)
        : [...prev, contactId]
    );
  };
  
  const handleProductToggle = (productId: string) => {
    setSelectedProducts(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };
  
  const isValid = selectedCompany && selectedContacts.length > 0 && selectedProducts.length > 0 && callType !== '';
  
  const handleStartMeeting = async () => {
    if (!isValid) {
      setError('Please select a company, at least one contact, at least one product, and a call type');
      return;
    }
    
    // If phone call is selected, redirect to phone call flow
    if (callType === 'phone_call') {
      navigate('/client-calls/phone');
      return;
    }
    
    setIsCreating(true);
    setError('');
    
    try {
      // Create meeting via API
      const response = await fetch('/api/v1/meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompany,
          contact_ids: selectedContacts,
          product_ids: selectedProducts,
          call_type: callType,
          meeting_name: meetingName || undefined,
          notes: notes || undefined,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create meeting');
      }
      
      const data = await response.json();
      const meetingId = data.data.meeting_id;
      
      // Navigate to live meeting screen
      navigate(`/client-calls/live/${meetingId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start meeting');
      setIsCreating(false);
    }
  };
  
  return (
    <div className="meeting-form-container">
      <BackButton to="/client-calls" label="Back to Client Calls" />
      <PageHeader 
        title="Start Meeting" 
        subtitle="Set up your meeting before starting the live call"
      />
      
      {error && <div className="form-error">{error}</div>}
      
      <div className="meeting-form">
        {/* Company Selection */}
        <div className="meeting-form-section">
          <SearchableCompanySelect
            value={selectedCompany}
            onChange={setSelectedCompany}
            label="Company"
            placeholder="Select a company..."
            required
          />
        </div>
        
        {/* Contact Selection */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Contact(s) <span className="required">*</span>
          </label>
          {!selectedCompany ? (
            <p className="context-subtitle">Select a company first to see contacts</p>
          ) : isLoadingContacts ? (
            <p className="context-subtitle">Loading contacts...</p>
          ) : contacts.length === 0 ? (
            <p className="context-subtitle">No contacts found for this company</p>
          ) : (
            <div className="selection-grid contacts-grid">
              {contacts.map((contact) => (
                <label
                  key={contact.id}
                  className={`selection-item ${selectedContacts.includes(contact.id) ? 'selected' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedContacts.includes(contact.id)}
                    onChange={() => handleContactToggle(contact.id)}
                  />
                  <div className="selection-item-content">
                    <div className="name">{contact.firstName} {contact.lastName}</div>
                    <div className="subtitle">{contact.jobTitle}</div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>
        
        {/* Product Selection */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Product(s) <span className="required">*</span>
          </label>
          <div className="product-selection-grid">
            {PRODUCTS.map((product) => (
              <label
                key={product.id}
                className={`selection-item ${selectedProducts.includes(product.id) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedProducts.includes(product.id)}
                  onChange={() => handleProductToggle(product.id)}
                />
                <span>{product.name}</span>
              </label>
            ))}
          </div>
        </div>
        
        {/* Call Type Selection */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Call Type <span className="required">*</span>
          </label>
          <div className="call-type-selection">
            <label className={`call-type-option ${callType === 'google_meeting' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="callType"
                value="google_meeting"
                checked={callType === 'google_meeting'}
                onChange={(e) => setCallType(e.target.value as any)}
              />
              <div className="call-type-content">
                <div className="call-type-title">Google Meeting</div>
                <div className="call-type-description">
                  You'll be prompted to share screen audio so Nebula can listen to the meeting
                </div>
              </div>
            </label>
            
            <label className={`call-type-option ${callType === 'phone_call' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="callType"
                value="phone_call"
                checked={callType === 'phone_call'}
                onChange={(e) => setCallType(e.target.value as any)}
              />
              <div className="call-type-content">
                <div className="call-type-title">Phone Call</div>
                <div className="call-type-description">
                  You'll be prompted to share screen audio so Nebula can listen to the call
                </div>
              </div>
            </label>
            
            <label className={`call-type-option ${callType === 'in_person' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="callType"
                value="in_person"
                checked={callType === 'in_person'}
                onChange={(e) => setCallType(e.target.value as any)}
              />
              <div className="call-type-content">
                <div className="call-type-title">In Person Meeting</div>
                <div className="call-type-description">
                  No screen audio sharing required. Just ensure Nebula is listening while you speak
                </div>
              </div>
            </label>
          </div>
        </div>
        
        {/* Optional Fields */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">Meeting Name (optional)</label>
          <input
            type="text"
            className="meeting-form-input"
            value={meetingName}
            onChange={(e) => setMeetingName(e.target.value)}
            placeholder="e.g., Discovery Call, Demo Presentation"
          />
        </div>
        
        <div className="meeting-form-section">
          <label className="meeting-form-label">Notes (optional)</label>
          <textarea
            className="meeting-form-textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any notes for this meeting..."
            rows={3}
          />
        </div>
        
        {/* Start Button */}
        <button
          className="start-meeting-btn"
          onClick={handleStartMeeting}
          disabled={!isValid || isCreating}
        >
          {isCreating ? (
            <>Starting...</>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Start Meeting
            </>
          )}
        </button>
      </div>
    </div>
  );
};
