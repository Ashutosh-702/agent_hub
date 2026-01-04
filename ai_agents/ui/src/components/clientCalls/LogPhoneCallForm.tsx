import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, BackButton } from '../shared';
import { 
  PRODUCTS, 
  getContactsForCompany, 
  type MockContact 
} from './mockData';
import { SearchableCompanySelect } from './SearchableCompanySelect';

interface Contact extends MockContact {}

export const LogPhoneCallForm = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [meetingName, setMeetingName] = useState('');
  const [notes, setNotes] = useState('');
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  
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
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/webm'];
      const validExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        setError('Please upload a valid audio file (MP3, WAV, M4A, OGG, or WebM)');
        return;
      }
      
      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setError('File size must be less than 100MB');
        return;
      }
      
      setAudioFile(file);
      setError('');
    }
  };
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };
  
  const isValid = selectedCompany && selectedContacts.length > 0 && selectedProducts.length > 0 && audioFile !== null;
  
  const handleLogCall = async () => {
    if (!isValid) {
      setError('Please select a company, at least one contact, at least one product, and upload an audio file');
      return;
    }
    
    setIsUploading(true);
    setError('');
    setUploadProgress(0);
    
    try {
      // First, create meeting record
      const meetingResponse = await fetch('/api/v1/meetings', {
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
      
      if (!meetingResponse.ok) {
        throw new Error('Failed to create meeting record');
      }
      
      const meetingData = await meetingResponse.json();
      const meetingId = meetingData.data.meeting_id;
      
      // Upload audio file and transcribe
      const formData = new FormData();
      formData.append('audio_file', audioFile!);
      formData.append('meeting_id', meetingId);
      
      const uploadResponse = await fetch(`/api/v1/meetings/${meetingId}/transcribe-audio`, {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadResponse.ok) {
        throw new Error('Failed to upload and transcribe audio');
      }
      
      // Navigate to summary/reflections page
      navigate(`/client-calls/summary/${meetingId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to log phone call');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };
  
  return (
    <div className="meeting-form-container">
      <BackButton to="/client-calls/phone" label="Back to Phone Call" />
      <PageHeader 
        title="Log Existing Phone Call" 
        subtitle="Upload a recorded phone call to transcribe and analyze"
      />
      
      {error && <div className="form-error">{error}</div>}
      
      <div className="meeting-form">
        {/* Audio File Upload */}
        <div className="meeting-form-section">
          <label className="meeting-form-label">
            Audio Recording <span className="required">*</span>
          </label>
          <div className="file-upload-area" style={{
            border: '2px dashed var(--color-gray-300)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-6)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
            backgroundColor: audioFile ? 'var(--color-success-light)' : 'var(--color-gray-50)',
            borderColor: audioFile ? 'var(--color-success)' : 'var(--color-gray-300)',
          }}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); }}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            if (file) {
              const event = { target: { files: [file] } } as any;
              handleFileSelect(event);
            }
          }}>
            {audioFile ? (
              <div>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="1.5" style={{ margin: '0 auto var(--space-2)' }}>
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                <div style={{ fontWeight: 600, color: 'var(--color-success)', marginBottom: 'var(--space-1)' }}>
                  {audioFile.name}
                </div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)' }}>
                  {formatFileSize(audioFile.size)}
                </div>
                <button 
                  type="button"
                  className="btn-secondary" 
                  style={{ marginTop: 'var(--space-2)' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setAudioFile(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                >
                  Remove File
                </button>
              </div>
            ) : (
              <div>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-gray-400)" strokeWidth="1.5" style={{ margin: '0 auto var(--space-2)' }}>
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <div style={{ fontWeight: 600, color: 'var(--color-gray-700)', marginBottom: 'var(--space-1)' }}>
                  Click to upload or drag and drop
                </div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)' }}>
                  MP3, WAV, M4A, OGG, or WebM (max 100MB)
                </div>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        </div>
        
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
        
        {/* Upload Progress */}
        {isUploading && (
          <div className="upload-progress" style={{
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-info-light)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontWeight: 600, color: 'var(--color-info)' }}>Uploading and transcribing...</span>
              <span style={{ color: 'var(--color-info)' }}>{uploadProgress}%</span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--color-gray-200)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                backgroundColor: 'var(--color-info)',
                transition: 'width 0.3s ease',
              }} />
            </div>
          </div>
        )}
        
        {/* Submit Button */}
        <button
          className="start-meeting-btn"
          onClick={handleLogCall}
          disabled={!isValid || isUploading}
        >
          {isUploading ? (
            <>Processing...</>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Log Phone Call
            </>
          )}
        </button>
      </div>
    </div>
  );
};

