import React, { useState } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';

// Generate mock contacts for the company with realistic data
const generateMockContacts = (companyId: string, companyName: string): Contact[] => {
  const contacts = [
    { firstName: 'James', lastName: 'Anderson', title: 'Chief Executive Officer' },
    { firstName: 'Sarah', lastName: 'Mitchell', title: 'Chief Technology Officer' },
    { firstName: 'Michael', lastName: 'Chen', title: 'VP of Sales' },
    { firstName: 'Emily', lastName: 'Rodriguez', title: 'Head of Marketing' },
    { firstName: 'David', lastName: 'Thompson', title: 'Director of Operations' },
    { firstName: 'Jennifer', lastName: 'Patel', title: 'Chief Financial Officer' },
    { firstName: 'Robert', lastName: 'Kim', title: 'VP of Engineering' },
    { firstName: 'Lisa', lastName: 'Wang', title: 'Head of Product' },
  ];
  
  const numContacts = Math.floor(Math.random() * 4) + 4; // 4-7 contacts
  const domain = companyName.toLowerCase().replace(/\s+/g, '').replace(/[^a-z0-9]/g, '');
  
  return contacts.slice(0, numContacts).map((contact, i) => ({
    id: `${companyId}-contact-${i + 1}`,
    companyId,
    firstName: contact.firstName,
    lastName: contact.lastName,
    email: `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@${domain}.com`,
    phone: `+1-${['415', '650', '408', '510', '925'][Math.floor(Math.random() * 5)]}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    jobTitle: contact.title,
    linkedinUrl: `https://linkedin.com/in/${contact.firstName.toLowerCase()}${contact.lastName.toLowerCase()}${Math.floor(Math.random() * 100)}`,
    isSynced: false,
  }));
};

export const Step1SingleCompany: React.FC = () => {
  const { setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  
  const [companyUrl, setCompanyUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [companyInfo, setCompanyInfo] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);

  const extractDomain = (url: string): string => {
    try {
      const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
      return parsed.hostname.replace('www.', '');
    } catch {
      return url.replace('www.', '');
    }
  };

  const handleValidateCompany = async () => {
    if (!companyUrl.trim()) {
      setError('Please enter a company URL');
      return;
    }

    setIsValidating(true);
    setError(null);
    setLoading(true, 'Fetching company information...', 0);

    // Simulate API call to validate and fetch company info
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const domain = extractDomain(companyUrl);
    const domainName = domain.split('.')[0];
    const companyName = domainName.charAt(0).toUpperCase() + domainName.slice(1);

    // Known company data for common domains
    const knownCompanies: Record<string, Partial<Company>> = {
      salesforce: { name: 'Salesforce', industry: 'Enterprise Software', employeeCount: '50000+', revenue: '$30B+', location: 'San Francisco, USA' },
      hubspot: { name: 'HubSpot', industry: 'Marketing Software', employeeCount: '5001-10000', revenue: '$1B+', location: 'Boston, USA' },
      stripe: { name: 'Stripe', industry: 'FinTech', employeeCount: '5001-10000', revenue: '$10B+', location: 'San Francisco, USA' },
      shopify: { name: 'Shopify', industry: 'E-commerce Platform', employeeCount: '10000+', revenue: '$5B+', location: 'Ottawa, Canada' },
      notion: { name: 'Notion', industry: 'Productivity Software', employeeCount: '501-1000', revenue: '$250M+', location: 'San Francisco, USA' },
      figma: { name: 'Figma', industry: 'Design Software', employeeCount: '1001-5000', revenue: '$500M+', location: 'San Francisco, USA' },
      slack: { name: 'Slack', industry: 'Collaboration Software', employeeCount: '1001-5000', revenue: '$1B+', location: 'San Francisco, USA' },
      zoom: { name: 'Zoom', industry: 'Video Communications', employeeCount: '5001-10000', revenue: '$4B+', location: 'San Jose, USA' },
    };

    const known = knownCompanies[domainName.toLowerCase()];
    
    // Mock company data
    const company: Company = {
      id: 'single-company-1',
      name: known?.name || companyName,
      website: companyUrl.startsWith('http') ? companyUrl : `https://${companyUrl}`,
      industry: known?.industry || ['Technology', 'Software', 'E-commerce', 'Healthcare', 'Finance'][Math.floor(Math.random() * 5)],
      employeeCount: known?.employeeCount || ['51-200', '201-500', '501-1000', '1001-5000'][Math.floor(Math.random() * 4)],
      revenue: known?.revenue || ['$5M - $10M', '$10M - $25M', '$25M - $50M', '$50M - $100M'][Math.floor(Math.random() * 4)],
      location: known?.location || ['San Francisco, USA', 'New York, USA', 'London, UK', 'Berlin, Germany', 'Bangalore, India'][Math.floor(Math.random() * 5)],
      linkedinUrl: `https://linkedin.com/company/${domainName}`,
      isQualified: true, // Already qualified for single company flow
      qualificationStatus: 'qualified' as const,
      contacts: generateMockContacts('single-company-1', known?.name || companyName),
      syncStatus: 'not_synced' as const,
      personalization: {
        messageStatus: 'pending' as const,
        deckStatus: 'pending' as const,
      },
    };

    setCompanyInfo(company);
    setIsValidating(false);
    setLoading(false);
  };

  const handleContinue = () => {
    if (!companyInfo) return;
    setQualifiedCompanies([companyInfo]);
    nextStep();
  };

  const handleClear = () => {
    setCompanyUrl('');
    setCompanyInfo(null);
    setError(null);
  };

  return (
    <div className="step-container step-single-company">
      <div className="step-header">
        <h2>Single Company URL</h2>
        <p>Enter the company URL to fetch information and contacts directly</p>
      </div>

      {/* URL Input */}
      <div className="single-company-input">
        <div className="input-group-large">
          <label htmlFor="company-url">Company Website URL</label>
          <div className="url-input-wrapper">
            <div className="url-prefix">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <input
              id="company-url"
              type="text"
              placeholder="e.g., acme.com or https://acme.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleValidateCompany()}
              disabled={isValidating || !!companyInfo}
            />
            {companyInfo && (
              <button className="clear-input-btn" onClick={handleClear}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>
          {error && <span className="input-error">{error}</span>}
        </div>

        {!companyInfo && (
          <button
            className="btn-primary validate-btn"
            onClick={handleValidateCompany}
            disabled={isValidating || !companyUrl.trim()}
          >
            {isValidating ? (
              <>
                <span className="spinner-small" />
                Validating...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Fetch Company
              </>
            )}
          </button>
        )}
      </div>

      {/* Company Info Card */}
      {companyInfo && (
        <div className="company-info-card">
          <div className="company-card-header">
            <div className="company-avatar">
              {companyInfo.name.charAt(0).toUpperCase()}
            </div>
            <div className="company-main-info">
              <h3>{companyInfo.name}</h3>
              <a href={companyInfo.website} target="_blank" rel="noopener noreferrer" className="company-website">
                {companyInfo.website}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              </a>
            </div>
            <div className="company-qualified-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Pre-qualified
            </div>
          </div>

          <div className="company-details-grid">
            <div className="detail-item">
              <span className="detail-label">Industry</span>
              <span className="detail-value">{companyInfo.industry}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Employees</span>
              <span className="detail-value">{companyInfo.employeeCount}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Revenue</span>
              <span className="detail-value">{companyInfo.revenue}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Location</span>
              <span className="detail-value">{companyInfo.location}</span>
            </div>
          </div>

          <div className="company-contacts-preview">
            <h4>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {companyInfo.contacts.length} Contacts Found
            </h4>
            <div className="contacts-preview-list">
              {companyInfo.contacts.slice(0, 3).map((contact) => (
                <div key={contact.id} className="contact-preview-item">
                  <span className="contact-name">{contact.firstName} {contact.lastName}</span>
                  <span className="contact-title">{contact.jobTitle}</span>
                </div>
              ))}
              {companyInfo.contacts.length > 3 && (
                <span className="more-contacts">+{companyInfo.contacts.length - 3} more</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="info-banner">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <p>
          <strong>Single Company Flow:</strong> This company will skip the Company Qualification step 
          and proceed directly to Contact Qualification after enrichment.
        </p>
      </div>

      {/* Actions */}
      <div className="step-actions">
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={!companyInfo}
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

export default Step1SingleCompany;

