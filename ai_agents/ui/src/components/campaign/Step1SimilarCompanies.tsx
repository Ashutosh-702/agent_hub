import React, { useState } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';

// Generate mock contacts for each company with realistic data
const generateMockContacts = (companyId: string, companyName: string): Contact[] => {
  const contacts = [
    { firstName: 'Jessica', lastName: 'Park', title: 'Chief Executive Officer' },
    { firstName: 'Kevin', lastName: 'Nguyen', title: 'Chief Technology Officer' },
    { firstName: 'Rachel', lastName: 'Goldstein', title: 'VP of Sales' },
    { firstName: 'Amit', lastName: 'Patel', title: 'Head of Marketing' },
    { firstName: 'Christina', lastName: 'Lee', title: 'Director of Operations' },
    { firstName: 'Brandon', lastName: 'Williams', title: 'VP of Product' },
  ];
  
  const numContacts = Math.floor(Math.random() * 3) + 3; // 3-5 contacts
  const domain = companyName.toLowerCase().replace(/\s+/g, '').replace(/[^a-z0-9]/g, '');
  
  return contacts.slice(0, numContacts).map((contact, i) => ({
    id: `${companyId}-contact-${i + 1}`,
    companyId,
    firstName: contact.firstName,
    lastName: contact.lastName,
    email: `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase()}@${domain}.com`,
    phone: `+1-${['628', '347', '312', '617', '206'][Math.floor(Math.random() * 5)]}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    jobTitle: contact.title,
    linkedinUrl: `https://linkedin.com/in/${contact.firstName.toLowerCase()}${contact.lastName.toLowerCase()}`,
    isSynced: false,
  }));
};

// Mock similar companies generator with realistic company names
const generateSimilarCompanies = (baseCompanyName: string): Company[] => {
  const realCompanies = [
    { name: 'Attentive', industry: 'Marketing Tech', location: 'New York, USA', employees: '501-1000', revenue: '$500M+' },
    { name: 'Klaviyo', industry: 'E-commerce Marketing', location: 'Boston, USA', employees: '1001-2000', revenue: '$700M+' },
    { name: 'Braze', industry: 'Customer Engagement', location: 'New York, USA', employees: '1001-2000', revenue: '$400M+' },
    { name: 'Iterable', industry: 'Marketing Automation', location: 'San Francisco, USA', employees: '501-1000', revenue: '$200M+' },
    { name: 'Customer.io', industry: 'Marketing Automation', location: 'Portland, USA', employees: '201-500', revenue: '$50M+' },
    { name: 'Postscript', industry: 'SMS Marketing', location: 'Scottsdale, USA', employees: '201-500', revenue: '$100M+' },
    { name: 'Yotpo', industry: 'E-commerce Marketing', location: 'New York, USA', employees: '501-1000', revenue: '$200M+' },
    { name: 'Gorgias', industry: 'Customer Support', location: 'San Francisco, USA', employees: '201-500', revenue: '$50M+' },
    { name: 'Recharge', industry: 'Subscription Commerce', location: 'Santa Monica, USA', employees: '501-1000', revenue: '$150M+' },
    { name: 'Sendlane', industry: 'Email Marketing', location: 'San Diego, USA', employees: '51-200', revenue: '$20M+' },
    { name: 'Omnisend', industry: 'E-commerce Marketing', location: 'London, UK', employees: '201-500', revenue: '$50M+' },
    { name: 'Drip', industry: 'Marketing Automation', location: 'Minneapolis, USA', employees: '51-200', revenue: '$30M+' },
    { name: 'Privy', industry: 'E-commerce Conversion', location: 'Boston, USA', employees: '51-200', revenue: '$25M+' },
    { name: 'Stamped', industry: 'Reviews & UGC', location: 'Toronto, Canada', employees: '51-200', revenue: '$15M+' },
    { name: 'Smile.io', industry: 'Loyalty & Rewards', location: 'Kitchener, Canada', employees: '51-200', revenue: '$20M+' },
    { name: 'LoyaltyLion', industry: 'Loyalty Platform', location: 'London, UK', employees: '51-200', revenue: '$15M+' },
    { name: 'Rebuy', industry: 'Personalization', location: 'Minneapolis, USA', employees: '51-200', revenue: '$25M+' },
    { name: 'Nosto', industry: 'E-commerce Personalization', location: 'Helsinki, Finland', employees: '201-500', revenue: '$40M+' },
    { name: 'Dynamic Yield', industry: 'Personalization', location: 'Tel Aviv, Israel', employees: '501-1000', revenue: '$100M+' },
    { name: 'Bloomreach', industry: 'Commerce Experience', location: 'Mountain View, USA', employees: '501-1000', revenue: '$200M+' },
    { name: 'Searchspring', industry: 'Site Search', location: 'San Antonio, USA', employees: '201-500', revenue: '$40M+' },
    { name: 'Algolia', industry: 'Search & Discovery', location: 'San Francisco, USA', employees: '501-1000', revenue: '$150M+' },
    { name: 'Constructor', industry: 'Product Discovery', location: 'San Francisco, USA', employees: '201-500', revenue: '$50M+' },
    { name: 'Findify', industry: 'E-commerce Search', location: 'Stockholm, Sweden', employees: '51-200', revenue: '$10M+' },
    { name: 'Klevu', industry: 'AI Search', location: 'Helsinki, Finland', employees: '51-200', revenue: '$15M+' },
  ];

  // Shuffle and take 15-25 companies
  const shuffled = [...realCompanies].sort(() => Math.random() - 0.5);
  const numCompanies = Math.floor(Math.random() * 10) + 15;
  
  return shuffled.slice(0, numCompanies).map((company, i) => {
    const id = `similar-${i + 1}`;
    return {
      id,
      name: company.name,
      website: `https://${company.name.toLowerCase().replace(/\./g, '')}.com`,
      industry: company.industry,
      employeeCount: company.employees,
      revenue: company.revenue,
      location: company.location,
      linkedinUrl: `https://linkedin.com/company/${company.name.toLowerCase().replace(/\./g, '')}`,
      isQualified: undefined,
      qualificationStatus: 'pending' as const,
      contacts: generateMockContacts(id, company.name),
      syncStatus: 'not_synced' as const,
      personalization: {
        messageStatus: 'pending' as const,
        deckStatus: 'pending' as const,
      },
      similarityScore: Math.floor(Math.random() * 25) + 75, // 75-100 similarity
    };
  }).sort((a, b) => (b.similarityScore || 0) - (a.similarityScore || 0));
};

interface CompanyWithSimilarity extends Company {
  similarityScore?: number;
}

export const Step1SimilarCompanies: React.FC = () => {
  const { setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  
  const [companyUrl, setCompanyUrl] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [sourceCompany, setSourceCompany] = useState<{ name: string; domain: string } | null>(null);
  const [similarCompanies, setSimilarCompanies] = useState<CompanyWithSimilarity[]>([]);
  const [error, setError] = useState<string | null>(null);

  const extractDomain = (url: string): string => {
    try {
      const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
      return parsed.hostname.replace('www.', '');
    } catch {
      return url.replace('www.', '');
    }
  };

  const handleFindSimilar = async () => {
    if (!companyUrl.trim()) {
      setError('Please enter a company URL');
      return;
    }

    setIsSearching(true);
    setError(null);
    setSimilarCompanies([]);
    setLoading(true, 'Finding similar companies...', 0);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const domain = extractDomain(companyUrl);
    const companyName = domain.split('.')[0].charAt(0).toUpperCase() + domain.split('.')[0].slice(1);

    setSourceCompany({ name: companyName, domain });

    // Generate mock similar companies
    const companies = generateSimilarCompanies(companyName);
    setSimilarCompanies(companies);
    
    setIsSearching(false);
    setLoading(false);
  };

  const handleContinue = () => {
    if (similarCompanies.length === 0) return;
    // Remove similarityScore before setting (it's not part of the Company type)
    const companiesWithoutScore = similarCompanies.map(({ similarityScore, ...company }) => company);
    setQualifiedCompanies(companiesWithoutScore);
    nextStep();
  };

  const handleReset = () => {
    setCompanyUrl('');
    setSourceCompany(null);
    setSimilarCompanies([]);
    setError(null);
  };

  return (
    <div className="step-container step-similar-companies">
      <div className="step-header">
        <h2>Similar Companies Search</h2>
        <p>Enter a company URL to find similar companies you can target</p>
      </div>

      {/* URL Input */}
      <div className="similar-company-input">
        <div className="input-group-large">
          <label htmlFor="source-company-url">Reference Company URL</label>
          <div className="url-input-wrapper">
            <div className="url-prefix">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <input
              id="source-company-url"
              type="text"
              placeholder="e.g., salesforce.com or https://hubspot.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFindSimilar()}
              disabled={isSearching || similarCompanies.length > 0}
            />
            {similarCompanies.length > 0 && (
              <button className="clear-input-btn" onClick={handleReset}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>
          {error && <span className="input-error">{error}</span>}
        </div>

        {similarCompanies.length === 0 && (
          <button
            className="btn-primary search-btn"
            onClick={handleFindSimilar}
            disabled={isSearching || !companyUrl.trim()}
          >
            {isSearching ? (
              <>
                <span className="spinner-small" />
                Searching...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Find Similar Companies
              </>
            )}
          </button>
        )}
      </div>

      {/* Source Company Info */}
      {sourceCompany && (
        <div className="source-company-banner">
          <div className="source-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
          </div>
          <div className="source-info">
            <span className="source-label">Finding companies similar to</span>
            <span className="source-name">{sourceCompany.name}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {similarCompanies.length > 0 && (
        <div className="similar-results">
          <div className="results-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {similarCompanies.length} Similar Companies Found
            </h3>
            <p>Companies are ranked by similarity score</p>
          </div>

          <div className="similar-companies-list">
            {similarCompanies.slice(0, 10).map((company, index) => (
              <div 
                key={company.id} 
                className="similar-company-card"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="similarity-badge">
                  {company.similarityScore}%
                </div>
                <div className="company-info">
                  <h4>{company.name}</h4>
                  <div className="company-meta">
                    <span className="tag">{company.industry}</span>
                    <span className="tag">{company.location}</span>
                    <span className="tag">{company.employeeCount}</span>
                  </div>
                </div>
                <div className="company-contacts">
                  <span>{company.contacts.length} contacts</span>
                </div>
              </div>
            ))}
            {similarCompanies.length > 10 && (
              <div className="more-companies-indicator">
                +{similarCompanies.length - 10} more similar companies
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        {similarCompanies.length > 0 && (
          <button className="btn-secondary" onClick={handleReset}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2.5 2v6h6"/>
              <path d="M21.5 22v-6h-6"/>
              <path d="M22 11.5A10 10 0 0 0 3.2 7.2"/>
              <path d="M2 12.5a10 10 0 0 0 18.8 4.2"/>
            </svg>
            Search Again
          </button>
        )}
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={similarCompanies.length === 0}
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

export default Step1SimilarCompanies;

