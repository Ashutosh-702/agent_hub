import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';
import { useGetCompaniesQuery } from '../../store';
import { PRODUCTS } from './StartMeetingForm';

// Mock contacts
const MOCK_CONTACTS = [
  { id: 'c1', firstName: 'Rajesh', lastName: 'Kumar', jobTitle: 'VP Operations', email: 'rajesh@acme.com' },
  { id: 'c2', firstName: 'Priya', lastName: 'Sharma', jobTitle: 'Chief Technology Officer', email: 'priya@acme.com' },
  { id: 'c3', firstName: 'Amit', lastName: 'Patel', jobTitle: 'Head of E-commerce', email: 'amit@acme.com' },
];

interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  jobTitle: string;
  email?: string;
}

export const PrepMeetingForm = () => {
  const navigate = useNavigate();
  const { data: companiesResponse, isLoading: companiesLoading } = useGetCompaniesQuery({ page: 1, limit: 100 });
  
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [meetingType, setMeetingType] = useState<'discovery' | 'demo' | 'followup' | 'negotiation'>('discovery');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [additionalContext, setAdditionalContext] = useState('');
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  
  const companies = companiesResponse?.data?.companies || [];
  
  useEffect(() => {
    if (selectedCompany) {
      setContacts(MOCK_CONTACTS);
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
  
  const handleGenerate = async () => {
    if (!isValid) {
      setError('Please select a company, at least one contact, and at least one product');
      return;
    }
    
    setIsGenerating(true);
    setError('');
    
    try {
      // In production, call API to generate battlecard
      const response = await fetch('/api/v1/meetings/battlecard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompany,
          contact_ids: selectedContacts,
          product_ids: selectedProducts,
          meeting_type: meetingType,
          scheduled_at: scheduledDate && scheduledTime ? `${scheduledDate}T${scheduledTime}` : undefined,
          additional_context: additionalContext || undefined,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate battlecard');
      }
      
      const data = await response.json();
      const battlecardId = data.data?.battlecard_id || 'mock-bc-1';
      
      navigate(`/client-calls/battlecard/${battlecardId}`);
    } catch (err) {
      // For demo, navigate to mock battlecard
      navigate('/client-calls/battlecard/mock-bc-1');
    } finally {
      setIsGenerating(false);
    }
  };
  
  if (companiesLoading) {
    return <Loader text="Loading..." />;
  }
  
  return (
    <div className="meeting-form-container">
      <BackButton to="/client-calls" label="Back to Client Calls" />
      <PageHeader
        title="Prepare Battlecard"
        subtitle="Generate a comprehensive preparation guide for your upcoming meeting"
      />
      
      {error && <div className="form-error">{error}</div>}
      
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
        
        {/* Meeting Type */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">Meeting Type</label>
          <select
            className="meeting-form-select"
            value={meetingType}
            onChange={(e) => setMeetingType(e.target.value as any)}
          >
            <option value="discovery">Discovery Call</option>
            <option value="demo">Product Demo</option>
            <option value="followup">Follow-up Meeting</option>
            <option value="negotiation">Negotiation / Closing</option>
          </select>
        </div>
        
        {/* Scheduled Date/Time */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">Scheduled Date & Time (optional)</label>
          <div className="datetime-grid">
            <input
              type="date"
              className="meeting-form-input"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
            />
            <input
              type="time"
              className="meeting-form-input"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
            />
          </div>
        </div>
        
        {/* Additional Context */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">Additional Context (optional)</label>
          <textarea
            className="meeting-form-textarea"
            value={additionalContext}
            onChange={(e) => setAdditionalContext(e.target.value)}
            placeholder="Any specific topics to cover, concerns to address, or goals for this meeting..."
            rows={3}
          />
        </div>
        
        {/* Generate Button */}
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={!isValid || isGenerating}
          style={{ marginTop: '1rem', width: '100%', justifyContent: 'center', padding: '1rem' }}
        >
          {isGenerating ? (
            'Generating Battlecard...'
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
              Generate Battlecard
            </>
          )}
        </button>
      </div>
    </div>
  );
};
