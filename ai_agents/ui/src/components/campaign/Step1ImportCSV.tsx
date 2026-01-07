import React, { useState, useRef, useEffect } from 'react';
import { useCampaignWizard } from './NewCampaignWizard';
import {
  useCreateCampaignFromCSVImportMutation,
  useGetCampaignStatusMinimalQuery,
} from '../../store';

interface CSVCompany {
  name: string;
  domain: string;
  rowIndex: number;
}

interface ParseResult {
  companies: CSVCompany[];
  errors: string[];
}

// Sample CSV data for testing (15 companies)
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

// Minimal sample CSV for download template (1 example row)
const SAMPLE_CSV_TEMPLATE = `company_name,domain
Acme Corp,acme.com`;

// Function to download sample CSV template
const downloadSampleCSV = () => {
  const blob = new Blob([SAMPLE_CSV_TEMPLATE], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'company_import_template.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const Step1ImportCSV: React.FC = () => {
  const { state, setCampaignId, nextStep, setLoading } = useCampaignWizard();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [createCampaignFromCSVImport, { isLoading: isCreating }] = useCreateCampaignFromCSVImportMutation();

  // OPTIMIZED: Use minimal status API instead of heavy campaign_details_with_companies
  const { data: campaignStatusData } = useGetCampaignStatusMinimalQuery(
    createdCampaignId
      ? { campaign_id: createdCampaignId }
      : { campaign_id: '' },
    {
      skip: !createdCampaignId || !isPolling,
      pollingInterval: createdCampaignId && isPolling ? 3000 : 0,
    }
  );

  // Effect to handle polling result - OPTIMIZED: Read from minimal status API
  useEffect(() => {
    if (!createdCampaignId || !isPolling) return;

    // Read from minimal status API (not full campaign details)
    const csvImportStatus = campaignStatusData?.data?.csv_import;
    const prospectingCycleStatus = campaignStatusData?.data?.prospecting_cycle?.status;

    // Update progress
    if (csvImportStatus?.processed_count !== undefined && csvImportStatus?.total_count) {
      const progress = Math.round((csvImportStatus.processed_count / csvImportStatus.total_count) * 100);
      setLoading(true, `Processing companies... (${csvImportStatus.processed_count}/${csvImportStatus.total_count})`, progress);
    }

    // Check if completed
    if (csvImportStatus?.status === 'completed' || prospectingCycleStatus === 'company_qualification') {
      setIsPolling(false);
      setLoading(false);
      nextStep();
    } else if (csvImportStatus?.status === 'failed') {
      setIsPolling(false);
      setLoading(false);
      const csvImportError = csvImportStatus?.error;
      setError(csvImportError || 'CSV import failed');
    }
  }, [campaignStatusData, createdCampaignId, isPolling, nextStep, setLoading]);

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
      
      if (!parts || parts.length < 1) {
        errors.push(`Row ${i + 1}: Invalid format`);
        continue;
      }

      // Support both: name,domain OR just domain
      let name = '';
      let domain = '';
      
      if (parts.length >= 2) {
        name = parts[0].replace(/"/g, '').trim();
        domain = parts[1].replace(/"/g, '').trim();
      } else {
        // Only domain provided
        domain = parts[0].replace(/"/g, '').trim();
        name = domain; // Use domain as name placeholder
      }

      if (!domain) {
        errors.push(`Row ${i + 1}: Domain/URL is required`);
        continue;
      }

      // Extract domain from URL if needed
      let cleanDomain = domain;
      if (cleanDomain.startsWith('http://')) cleanDomain = cleanDomain.slice(7);
      if (cleanDomain.startsWith('https://')) cleanDomain = cleanDomain.slice(8);
      if (cleanDomain.startsWith('www.')) cleanDomain = cleanDomain.slice(4);
      cleanDomain = cleanDomain.split('/')[0];

      companies.push({
        name: name || cleanDomain,
        domain: cleanDomain,
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
    setError(null);

    try {
      const content = await file.text();
      const result = parseCSV(content);
      setParseResult(result);
    } catch (err) {
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

    setError(null);
    setLoading(true, 'Creating campaign and processing companies...', 0);

    try {
      // Extract domains from parsed companies
      const domains = parseResult.companies.map(c => c.domain);
      
      // Use products selected in ProductSelection step
      const productNames = state.selectedProducts.join(',');

      const payload = {
        campaign_name: state.campaignName, // Required unique campaign name
        company_domains: domains,
        product_name: productNames || undefined,
        campaign_type: 'import_csv',
        prospecting_cycle_status: 'prospecting',
      };

      const response = await createCampaignFromCSVImport(payload).unwrap();
      const newCampaignId = response?.data?.campaign_id;
      const totalCompanies = response?.data?.total_companies || domains.length;

      if (!newCampaignId) {
        throw new Error('campaign_id missing in response');
      }

      setCreatedCampaignId(newCampaignId);
      setCampaignId(newCampaignId);

      // All processing now happens in Kafka - start polling immediately
      setLoading(true, `Processing ${totalCompanies} companies... (0/${totalCompanies})`, 0);
      setIsPolling(true);
    } catch (e: unknown) {
      console.error(e);
      const errorMessage = e instanceof Error ? e.message : 'Failed to create campaign from CSV';
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setParseResult(null);
    setError(null);
    setCreatedCampaignId(null);
    setIsPolling(false);
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
    setError(null);
  };

  const isProcessingCampaign = isCreating || isPolling;

  return (
    <div className="step-container step-import-csv">
      <div className="step-header">
        <h2>Import Company List</h2>
        <p>Upload a CSV file with company names and their domains/URLs</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem', padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

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
          <button 
            className="download-sample-btn"
            onClick={(e) => {
              e.stopPropagation(); // Prevent triggering file browse
              downloadSampleCSV();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Download Sample CSV
          </button>
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
          {!isProcessingCampaign && (
            <button className="remove-file-btn" onClick={handleRemoveFile}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
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
                {parseResult.errors.slice(0, 5).map((err, i) => (
                  <li key={i}>{err}</li>
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
                <p>These companies will be enriched via Apollo and processed in the next step</p>
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
          disabled={!parseResult || parseResult.companies.length === 0 || isProcessing || isProcessingCampaign}
        >
          {isProcessingCampaign ? (
            <>
              <span className="spinner-small" />
              Processing...
            </>
          ) : (
            <>
              Continue to Company Qualification
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Step1ImportCSV;
