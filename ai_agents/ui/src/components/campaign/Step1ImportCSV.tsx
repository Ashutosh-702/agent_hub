import React, { useState, useRef } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';

interface CSVCompany {
  name: string;
  domain: string;
  rowIndex: number;
}

interface ParseResult {
  companies: CSVCompany[];
  errors: string[];
}

// Sample CSV data for testing
const SAMPLE_CSV_DATA = `company_name,domain
Shopify,shopify.com
HubSpot,hubspot.com
Salesforce,salesforce.com
Stripe,stripe.com
Notion,notion.so
Figma,figma.com
Slack,slack.com
Zoom,zoom.us
Atlassian,atlassian.com
Twilio,twilio.com
Datadog,datadoghq.com
MongoDB,mongodb.com
Elastic,elastic.co
Snowflake,snowflake.com
Confluent,confluent.io`;

// Generate mock contacts for each company with realistic data
const generateMockContacts = (companyId: string, companyName: string): Contact[] => {
  const contacts = [
    { firstName: 'Amanda', lastName: 'Torres', title: 'Chief Executive Officer' },
    { firstName: 'Ryan', lastName: 'Kowalski', title: 'Chief Technology Officer' },
    { firstName: 'Michelle', lastName: 'Santos', title: 'VP of Sales' },
    { firstName: 'Derek', lastName: 'Chang', title: 'Head of Marketing' },
    { firstName: 'Lauren', lastName: 'Baker', title: 'Director of Operations' },
    { firstName: 'Nathan', lastName: 'Singh', title: 'VP of Business Development' },
  ];
  
  const numContacts = Math.floor(Math.random() * 3) + 3; // 3-5 contacts
  const domain = companyName.toLowerCase().replace(/\s+/g, '').replace(/[^a-z0-9]/g, '');
  
  return contacts.slice(0, numContacts).map((contact, i) => ({
    id: `${companyId}-contact-${i + 1}`,
    companyId,
    firstName: contact.firstName,
    lastName: contact.lastName,
    email: `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@${domain}.com`,
    phone: `+1-${['415', '212', '312', '617', '303'][Math.floor(Math.random() * 5)]}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    jobTitle: contact.title,
    linkedinUrl: `https://linkedin.com/in/${contact.firstName.toLowerCase()}${contact.lastName.toLowerCase()}`,
    isSynced: false,
  }));
};

export const Step1ImportCSV: React.FC = () => {
  const { setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const parseCSV = (content: string): ParseResult => {
    const lines = content.split('\n').filter((line) => line.trim());
    const errors: string[] = [];
    const companies: CSVCompany[] = [];

    if (lines.length === 0) {
      errors.push('CSV file is empty');
      return { companies, errors };
    }

    // Try to detect header row
    const firstLine = lines[0].toLowerCase();
    const hasHeader = firstLine.includes('name') || firstLine.includes('company') || firstLine.includes('domain') || firstLine.includes('url');
    const startIndex = hasHeader ? 1 : 0;

    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Split by comma, handling quoted values
      const parts = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g);
      
      if (!parts || parts.length < 2) {
        errors.push(`Row ${i + 1}: Invalid format - expected at least 2 columns (name, domain)`);
        continue;
      }

      const name = parts[0].replace(/"/g, '').trim();
      const domain = parts[1].replace(/"/g, '').trim();

      if (!name) {
        errors.push(`Row ${i + 1}: Company name is required`);
        continue;
      }

      if (!domain) {
        errors.push(`Row ${i + 1}: Domain/URL is required`);
        continue;
      }

      companies.push({
        name,
        domain,
        rowIndex: i + 1,
      });
    }

    return { companies, errors };
  };

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setParseResult({ companies: [], errors: ['Please upload a CSV file'] });
      return;
    }

    setUploadedFile(file);
    setIsProcessing(true);

    try {
      const content = await file.text();
      const result = parseCSV(content);
      setParseResult(result);
    } catch (error) {
      setParseResult({ companies: [], errors: ['Failed to read file'] });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleContinue = async () => {
    if (!parseResult || parseResult.companies.length === 0) return;

    setLoading(true, 'Processing companies...', 0);

    // Convert parsed companies to Company objects
    const companies: Company[] = parseResult.companies.map((csvCompany, index) => ({
      id: `imported-${index + 1}`,
      name: csvCompany.name,
      website: csvCompany.domain.startsWith('http') ? csvCompany.domain : `https://${csvCompany.domain}`,
      industry: 'Unknown',
      employeeCount: 'Unknown',
      revenue: 'Unknown',
      location: 'Unknown',
      linkedinUrl: '',
      isQualified: undefined,
      qualificationStatus: 'pending' as const,
      contacts: generateMockContacts(`imported-${index + 1}`, csvCompany.name),
      syncStatus: 'not_synced' as const,
      personalization: {
        messageStatus: 'pending' as const,
        deckStatus: 'pending' as const,
      },
    }));

    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    setQualifiedCompanies(companies);
    setLoading(false);
    nextStep();
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setParseResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUseSampleData = () => {
    // Create a fake file for display purposes
    const fakeFile = new File([SAMPLE_CSV_DATA], 'sample_companies.csv', { type: 'text/csv' });
    setUploadedFile(fakeFile);
    const result = parseCSV(SAMPLE_CSV_DATA);
    setParseResult(result);
  };

  return (
    <div className="step-container step-import-csv">
      <div className="step-header">
        <h2>Import Company List</h2>
        <p>Upload a CSV file with company names and their domains/URLs</p>
      </div>

      {/* Upload Area */}
      {!uploadedFile && (
        <div
          className={`csv-upload-area ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <div className="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <h3>Drop your CSV file here</h3>
          <p>or click to browse</p>
          <div className="upload-format-hint">
            Expected format: company_name, domain/url
          </div>
        </div>
      )}
      
      {/* Sample Data Button - shown when no file uploaded */}
      {!uploadedFile && (
        <div className="sample-data-section">
          <span className="divider-text">or</span>
          <button 
            className="use-sample-data-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleUseSampleData();
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Use Sample Data (15 companies)
          </button>
        </div>
      )}

      {/* File Info - shown when file is uploaded */}
      {uploadedFile && (
        <div className="csv-file-info">
          <div className="file-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <div className="file-details">
            <span className="file-name">{uploadedFile.name}</span>
            <span className="file-size">{(uploadedFile.size / 1024).toFixed(1)} KB</span>
          </div>
          <button className="remove-file-btn" onClick={handleRemoveFile}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="processing-indicator">
          <span className="spinner-small" />
          Processing file...
        </div>
      )}

      {/* Parse Results */}
      {parseResult && (
        <div className="parse-results">
          {/* Errors */}
          {parseResult.errors.length > 0 && (
            <div className="parse-errors">
              <h4>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {parseResult.errors.length} Warning{parseResult.errors.length > 1 ? 's' : ''}
              </h4>
              <ul>
                {parseResult.errors.slice(0, 5).map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
                {parseResult.errors.length > 5 && (
                  <li className="more-errors">+{parseResult.errors.length - 5} more warnings</li>
                )}
              </ul>
            </div>
          )}

          {/* Success Summary */}
          {parseResult.companies.length > 0 && (
            <div className="parse-success">
              <div className="success-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div className="success-info">
                <h4>{parseResult.companies.length} companies ready to import</h4>
                <p>These companies will be processed in the next step</p>
              </div>
            </div>
          )}

          {/* Preview List */}
          {parseResult.companies.length > 0 && (
            <div className="csv-preview">
              <h4>Preview</h4>
              <div className="preview-list">
                {parseResult.companies.slice(0, 5).map((company, i) => (
                  <div key={i} className="preview-item">
                    <span className="preview-name">{company.name}</span>
                    <span className="preview-domain">{company.domain}</span>
                  </div>
                ))}
                {parseResult.companies.length > 5 && (
                  <div className="preview-more">
                    +{parseResult.companies.length - 5} more companies
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={!parseResult || parseResult.companies.length === 0 || isProcessing}
        >
          Continue to Enrichment
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Step1ImportCSV;

