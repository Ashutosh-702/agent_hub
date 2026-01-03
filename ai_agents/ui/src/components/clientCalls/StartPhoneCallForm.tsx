import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';
import { useGetCompaniesQuery } from '../../store';
import { 
  PRODUCTS, 
  MOCK_COMPANIES, 
  getContactsForCompany, 
  type MockContact 
} from './mockData';

interface Contact extends MockContact {}

export const StartPhoneCallForm = () => {
  const navigate = useNavigate();
  const { data: companiesResponse, isLoading: companiesLoading } = useGetCompaniesQuery({ page: 1, limit: 100 });
  
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [meetingName, setMeetingName] = useState('');
  const [notes, setNotes] = useState('');
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  
  // Use API companies if available, otherwise fall back to mock data
  const apiCompanies = companiesResponse?.data || [];
  const companies = apiCompanies.length > 0 ? apiCompanies : MOCK_COMPANIES;
  
  // Fetch contacts when company changes
  useEffect(() => {
    if (selectedCompany) {
      setContacts(getContactsForCompany(selectedCompany));
      setSelectedContacts([]);
    } else {
      setContacts([]);
    }
  }, [selectedCompany]);
  
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
  
  const isValid = selectedCompany && selectedContacts.length > 0 && selectedProducts.length > 0;
  
  const handleStartCall = async () => {
    if (!isValid) {
      setError('Please select a company, at least one contact, and at least one product');
      return;
    }
    
    setIsCreating(true);
    setError('');
    
    try {
      // Create meeting via API with call_type = phone_call
      const response = await fetch('/api/v1/meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompany,
          contact_ids: selectedContacts,
          product_ids: selectedProducts,
          call_type: 'phone_call',
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
      setError(err instanceof Error ? err.message : 'Failed to start phone call');
      setIsCreating(false);
    }
  };
  
  if (companiesLoading) {
    return <Loader text="Loading companies..." />;
  }
  
  return (
    <div className="meeting-form-container">
      <BackButton to="/client-calls/phone" label="Back to Phone Call" />
      <PageHeader 
        title="Start Phone Call" 
        subtitle="Set up your phone call before starting the live transcription"
      />
      
      {error && <div className="form-error">{error}</div>}
      
      <div className="phone-call-info" style={{ 
        marginBottom: 'var(--space-6)', 
        padding: 'var(--space-4)', 
        backgroundColor: 'var(--color-info-light)', 
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-info)'
      }}>
        <strong>📞 Phone Call Setup:</strong>
        <p style={{ margin: 'var(--space-2) 0 0 0', fontSize: 'var(--text-sm)' }}>
          When you start the call, you'll be prompted to share screen audio so Nebula can listen to both sides of the conversation. 
          Make sure your phone call is active before starting.
        </p>
      </div>
      
      <div className="meeting-form">
        {/* Company Selection */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Company <span className="required">*</span>
          </label>
          <select
            className="meeting-form-select"
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
          >
            <option value="">Select a company...</option>
            {companies.map((company: any) => (
              <option key={company.id || company._id} value={company.id || company._id}>
                {company.name}
              </option>
            ))}
          </select>
        </div>
        
        {/* Contact Selection */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Contact(s) <span className="required">*</span>
          </label>
          {!selectedCompany ? (
            <p className="context-subtitle">Select a company first to see contacts</p>
          ) : contacts.length === 0 ? (
            <p className="context-subtitle">No contacts found for this company</p>
          ) : (
            <div className="selection-grid">
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
        
        {/* Optional Fields */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">Call Name (optional)</label>
          <input
            type="text"
            className="meeting-form-input"
            value={meetingName}
            onChange={(e) => setMeetingName(e.target.value)}
            placeholder="e.g., Discovery Call, Follow-up Call"
          />
        </div>
        
        <div className="meeting-form-section">
          <label className="meeting-form-label">Notes (optional)</label>
          <textarea
            className="meeting-form-textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any notes for this call..."
            rows={3}
          />
        </div>
        
        {/* Start Button */}
        <button
          className="start-meeting-btn"
          onClick={handleStartCall}
          disabled={!isValid || isCreating}
        >
          {isCreating ? (
            <>Starting...</>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              Start Phone Call
            </>
          )}
        </button>
      </div>
    </div>
  );
};

