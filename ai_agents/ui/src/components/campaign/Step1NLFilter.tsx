import React, { useState } from 'react';
import { useCampaignWizard, type Company, type Contact } from './NewCampaignWizard';

// Generate mock contacts for each company
const generateMockContacts = (companyId: string, companyName: string): Contact[] => {
  const contacts = [
    { firstName: 'Alexandra', lastName: 'Chen', title: 'Chief Executive Officer' },
    { firstName: 'Marcus', lastName: 'Rivera', title: 'Chief Technology Officer' },
    { firstName: 'Priya', lastName: 'Sharma', title: 'VP of Sales' },
    { firstName: 'Thomas', lastName: 'Mueller', title: 'Head of Marketing' },
    { firstName: 'Sophia', lastName: 'Nakamura', title: 'Director of Operations' },
    { firstName: 'Daniel', lastName: 'O\'Brien', title: 'VP of Engineering' },
  ];
  
  const numContacts = Math.floor(Math.random() * 3) + 3; // 3-5 contacts
  const domain = companyName.toLowerCase().replace(/\s+/g, '').replace(/[^a-z0-9]/g, '');
  
  return contacts.slice(0, numContacts).map((contact, i) => ({
    id: `${companyId}-contact-${i + 1}`,
    companyId,
    firstName: contact.firstName,
    lastName: contact.lastName,
    email: `${contact.firstName.toLowerCase()}.${contact.lastName.toLowerCase().replace(/'/g, '')}@${domain}.com`,
    phone: `+1-${['415', '650', '408', '212', '310'][Math.floor(Math.random() * 5)]}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    jobTitle: contact.title,
    linkedinUrl: `https://linkedin.com/in/${contact.firstName.toLowerCase()}${contact.lastName.toLowerCase().replace(/'/g, '')}`,
    isSynced: false,
  }));
};

// Mock companies generator based on NL query with realistic data
const generateCompaniesFromNL = (query: string): Company[] => {
  const realCompanies = [
    { name: 'Acme Corp', industry: 'Enterprise Software', location: 'San Francisco, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'TechNova', industry: 'Cloud Infrastructure', location: 'Seattle, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'DataSphere', industry: 'Data Analytics', location: 'Boston, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'CloudFirst', industry: 'SaaS', location: 'Austin, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'PixelCraft', industry: 'Design Tech', location: 'Los Angeles, USA', employees: '51-200', revenue: '$5M - $10M' },
    { name: 'Quantix Labs', industry: 'AI/ML', location: 'Palo Alto, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'NexGen Systems', industry: 'Enterprise Software', location: 'Chicago, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'Zenith AI', industry: 'Artificial Intelligence', location: 'New York, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Pulse Analytics', industry: 'Business Intelligence', location: 'Denver, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'Velocify', industry: 'Sales Tech', location: 'San Diego, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Streamline.io', industry: 'Workflow Automation', location: 'Portland, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'ClearPath', industry: 'DevOps Tools', location: 'Atlanta, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Beacon Labs', industry: 'IoT Platform', location: 'Miami, USA', employees: '51-200', revenue: '$5M - $10M' },
    { name: 'Quantum Edge', industry: 'Edge Computing', location: 'Phoenix, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Infinity Stack', industry: 'Infrastructure', location: 'Dallas, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'Nova Systems', industry: 'Cybersecurity', location: 'Washington DC, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Pinnacle Tech', industry: 'FinTech', location: 'Charlotte, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'Horizon AI', industry: 'Computer Vision', location: 'Pittsburgh, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'Summit Cloud', industry: 'Cloud Services', location: 'Salt Lake City, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Vertex Labs', industry: 'ML Platform', location: 'San Jose, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Prism Analytics', industry: 'Marketing Analytics', location: 'Minneapolis, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'Catalyst AI', industry: 'AI Platform', location: 'Nashville, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Forge Systems', industry: 'Developer Tools', location: 'Raleigh, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Axion Labs', industry: 'Data Platform', location: 'Columbus, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'Solstice Tech', industry: 'HR Tech', location: 'Indianapolis, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Eclipse AI', industry: 'NLP', location: 'Detroit, USA', employees: '51-200', revenue: '$10M - $25M' },
    { name: 'Momentum Labs', industry: 'Product Analytics', location: 'Philadelphia, USA', employees: '201-500', revenue: '$25M - $50M' },
    { name: 'Stratos Cloud', industry: 'Multi-Cloud', location: 'Tampa, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'Apex Systems', industry: 'Enterprise Platform', location: 'Houston, USA', employees: '501-1000', revenue: '$50M - $100M' },
    { name: 'Vector AI', industry: 'Recommendation Engine', location: 'Las Vegas, USA', employees: '51-200', revenue: '$10M - $25M' },
  ];

  // Shuffle and return a random subset
  const shuffled = [...realCompanies].sort(() => Math.random() - 0.5);
  const numResults = Math.floor(Math.random() * 12) + 18; // 18-30 results
  
  return shuffled.slice(0, numResults).map((company, i) => {
    const id = `nl-${i + 1}`;
    return {
      id,
      name: company.name,
      website: `https://${company.name.toLowerCase().replace(/\s+/g, '').replace(/\./g, '')}.com`,
      industry: company.industry,
      employeeCount: company.employees,
      revenue: company.revenue,
      location: company.location,
      linkedinUrl: `https://linkedin.com/company/${company.name.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`,
      isQualified: undefined,
      qualificationStatus: 'pending' as const,
      contacts: generateMockContacts(id, company.name),
      syncStatus: 'not_synced' as const,
      personalization: {
        messageStatus: 'pending' as const,
        deckStatus: 'pending' as const,
      },
    };
  });
};

const EXAMPLE_QUERIES = [
  "SaaS companies in the US with 50-500 employees that have raised Series A or B funding",
  "E-commerce companies in Europe with revenue between $5M and $50M",
  "Healthcare tech startups in North America using modern tech stack",
  "B2B software companies with remote-first culture and growing engineering teams",
];

export const Step1NLFilter: React.FC = () => {
  const { setQualifiedCompanies, nextStep, setLoading } = useCampaignWizard();
  
  const [nlQuery, setNlQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [parsedIntent, setParsedIntent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!nlQuery.trim()) {
      setError('Please describe your target companies');
      return;
    }

    setIsSearching(true);
    setError(null);
    setCompanies([]);
    setLoading(true, 'Understanding your query...', 0);

    // Simulate NL processing
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setLoading(true, 'Converting to search filters...', 0);
    
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    // Mock parsed intent
    setParsedIntent(`Searching for: ${nlQuery.slice(0, 100)}${nlQuery.length > 100 ? '...' : ''}`);
    
    setLoading(true, 'Fetching matching companies...', 0);
    await new Promise((resolve) => setTimeout(resolve, 1200));

    const results = generateCompaniesFromNL(nlQuery);
    setCompanies(results);
    
    setIsSearching(false);
    setLoading(false);
  };

  const handleExampleClick = (example: string) => {
    setNlQuery(example);
  };

  const handleContinue = () => {
    if (companies.length === 0) return;
    setQualifiedCompanies(companies);
    nextStep();
  };

  const handleReset = () => {
    setNlQuery('');
    setCompanies([]);
    setParsedIntent(null);
    setError(null);
  };

  return (
    <div className="step-container step-nl-filter">
      <div className="step-header">
        <h2>Find All - Natural Language</h2>
        <p>Describe your ideal target companies in plain English</p>
      </div>

      {/* NL Input */}
      <div className="nl-input-section">
        <div className="nl-input-wrapper">
          <textarea
            placeholder="Describe the companies you want to target...&#10;&#10;Example: SaaS companies in the US with 50-500 employees that have raised Series A funding"
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            disabled={isSearching || companies.length > 0}
            rows={4}
          />
          {companies.length > 0 && (
            <button className="clear-input-btn" onClick={handleReset}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
        </div>
        {error && <span className="input-error">{error}</span>}

        {/* Example Queries */}
        {companies.length === 0 && !isSearching && (
          <div className="example-queries">
            <span className="examples-label">Try an example:</span>
            <div className="examples-list">
              {EXAMPLE_QUERIES.map((example, i) => (
                <button
                  key={i}
                  className="example-chip"
                  onClick={() => handleExampleClick(example)}
                >
                  {example.slice(0, 50)}...
                </button>
              ))}
            </div>
          </div>
        )}

        {companies.length === 0 && (
          <button
            className="btn-primary search-btn"
            onClick={handleSearch}
            disabled={isSearching || !nlQuery.trim()}
          >
            {isSearching ? (
              <>
                <span className="spinner-small" />
                Processing...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Find Companies
              </>
            )}
          </button>
        )}
      </div>

      {/* Processing Animation */}
      {isSearching && (
        <div className="nl-processing">
          <div className="processing-steps">
            <div className="processing-step active">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </span>
              <span>Understanding intent</span>
            </div>
            <div className="processing-step">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                </svg>
              </span>
              <span>Building query</span>
            </div>
            <div className="processing-step">
              <span className="step-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </span>
              <span>Searching</span>
            </div>
          </div>
        </div>
      )}

      {/* Parsed Intent */}
      {parsedIntent && companies.length > 0 && (
        <div className="parsed-intent-banner">
          <div className="intent-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
            </svg>
          </div>
          <span>{parsedIntent}</span>
        </div>
      )}

      {/* Results */}
      {companies.length > 0 && (
        <div className="nl-results">
          <div className="results-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {companies.length} Companies Found
            </h3>
            <p>Based on your natural language query</p>
          </div>

          <div className="companies-preview-grid">
            {companies.slice(0, 8).map((company, index) => (
              <div 
                key={company.id} 
                className="company-preview-card"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <h4>{company.name}</h4>
                <div className="company-meta">
                  <span className="tag">{company.industry}</span>
                  <span className="tag">{company.location}</span>
                </div>
                <div className="company-stats">
                  <span>{company.employeeCount} employees</span>
                  <span>{company.contacts.length} contacts</span>
                </div>
              </div>
            ))}
          </div>
          
          {companies.length > 8 && (
            <div className="more-results">
              +{companies.length - 8} more companies match your criteria
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        {companies.length > 0 && (
          <button className="btn-secondary" onClick={handleReset}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2.5 2v6h6"/>
              <path d="M21.5 22v-6h-6"/>
              <path d="M22 11.5A10 10 0 0 0 3.2 7.2"/>
              <path d="M2 12.5a10 10 0 0 0 18.8 4.2"/>
            </svg>
            New Search
          </button>
        )}
        <button
          className="btn-primary btn-large"
          onClick={handleContinue}
          disabled={companies.length === 0}
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

export default Step1NLFilter;

