import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader } from './shared';

// Mock data for campaign details
const mockCampaignData = {
  _id: '68d1402f508284770d48685c',
  ownership: {
    product_name: 'Fynd Platform',
    hubspot_email: 'sales@fynd.com',
    business_team: 'Enterprise Sales',
    user_email: 'john.doe@fynd.com',
  },
  lifecycle: {
    status: 'active',
  },
  segmentation: {
    industry: ['Technology', 'E-commerce'],
    keywords: 'saas, platform, retail',
    categories: 'B2B, Enterprise',
  },
  target: {
    employee_count: ['201-500', '501-1000'],
    revenue_min: '10',
    revenue_max: '100',
    currency: 'USD',
    location: {
      type: 'country',
      names: ['United States', 'India', 'UK'],
    },
  },
  metadata: {
    created_at: '2025-01-15T10:30:00.000Z',
    updated_at: '2025-01-20T14:45:00.000Z',
  },
  company_mappings_count: 15,
};

// Mock companies data
const mockCompanies = [
  {
    _id: '1',
    name: 'TechCorp Solutions',
    domain: 'techcorp.com',
    industry: 'Technology',
    employees: '201-500',
    status: 'enriched',
    contacts_count: 8,
  },
  {
    _id: '2',
    name: 'RetailMax Inc',
    domain: 'retailmax.io',
    industry: 'E-commerce',
    employees: '501-1000',
    status: 'pending',
    contacts_count: 0,
  },
  {
    _id: '3',
    name: 'CloudNine Systems',
    domain: 'cloudnine.tech',
    industry: 'Cloud Computing',
    employees: '51-200',
    status: 'enriched',
    contacts_count: 12,
  },
  {
    _id: '4',
    name: 'DataFlow Analytics',
    domain: 'dataflow.ai',
    industry: 'Data Analytics',
    employees: '11-50',
    status: 'processing',
    contacts_count: 3,
  },
  {
    _id: '5',
    name: 'FinServe Global',
    domain: 'finserve.com',
    industry: 'Finance',
    employees: '1001-5000',
    status: 'enriched',
    contacts_count: 15,
  },
  {
    _id: '6',
    name: 'HealthTech Pro',
    domain: 'healthtechpro.com',
    industry: 'Healthcare',
    employees: '201-500',
    status: 'failed',
    contacts_count: 0,
  },
  {
    _id: '7',
    name: 'EduLearn Platform',
    domain: 'edulearn.io',
    industry: 'Education',
    employees: '51-200',
    status: 'enriched',
    contacts_count: 6,
  },
  {
    _id: '8',
    name: 'LogiChain Solutions',
    domain: 'logichain.com',
    industry: 'Logistics',
    employees: '501-1000',
    status: 'pending',
    contacts_count: 0,
  },
];

const statusColors: Record<string, { bg: string; text: string }> = {
  enriched: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  pending: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  processing: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  failed: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444' },
  active: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  completed: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1' },
  draft: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  paused: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
};

export const CampaignDetails = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  
  // Simulate loading state
  const [isLoading] = useState(false);
  
  // Use mock data
  const campaign = mockCampaignData;
  const companies = mockCompanies;

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const getStatusStats = () => {
    const stats = {
      enriched: 0,
      pending: 0,
      processing: 0,
      failed: 0,
    };
    companies.forEach(c => {
      if (stats[c.status as keyof typeof stats] !== undefined) {
        stats[c.status as keyof typeof stats]++;
      }
    });
    return stats;
  };

  const stats = getStatusStats();

  return (
    <div className="campaign-details-container">
      <div className="campaign-details-card">
        {/* Back Button */}
        <button
          className="back-to-campaigns-btn"
          onClick={() => navigate('/master-data/campaign')}
        >
          ← Back to Campaigns
        </button>

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading campaign details..." />
        ) : (
          <>
            {/* Campaign Info Section */}
            <div className="campaign-info-section">
              <div className="campaign-details-header">
                <div>
                  <h1 className="campaign-details-title">
                    {campaign.ownership?.product_name || 'Campaign'}
                  </h1>
                  <p className="campaign-id">ID: {campaignId || campaign._id}</p>
                </div>
                <span
                  className="campaign-status-badge"
                  style={{
                    backgroundColor: statusColors[campaign.lifecycle?.status]?.bg,
                    color: statusColors[campaign.lifecycle?.status]?.text,
                  }}
                >
                  {campaign.lifecycle?.status}
                </span>
              </div>

              <div className="campaign-info-grid">
                <div className="info-item">
                  <label>Business Team</label>
                  <span>{campaign.ownership?.business_team || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Owner Email</label>
                  <span>{campaign.ownership?.user_email || '-'}</span>
                </div>
                <div className="info-item">
                  <label>HubSpot Email</label>
                  <span>{campaign.ownership?.hubspot_email || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Target Industries</label>
                  <span>{campaign.segmentation?.industry?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Employee Range</label>
                  <span>{campaign.target?.employee_count?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Revenue Range</label>
                  <span>
                    {campaign.target?.revenue_min && campaign.target?.revenue_max
                      ? `$${campaign.target.revenue_min}M - $${campaign.target.revenue_max}M`
                      : '-'}
                  </span>
                </div>
                <div className="info-item">
                  <label>Locations</label>
                  <span>{campaign.target?.location?.names?.join(', ') || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Created</label>
                  <span>{formatDate(campaign.metadata?.created_at)}</span>
                </div>
              </div>

              {/* Progress Stats */}
              <div className="campaign-progress-section">
                <h3>Company Progress</h3>
                <div className="progress-stats">
                  <div className="stat-card enriched">
                    <span className="stat-number">{stats.enriched}</span>
                    <span className="stat-label">Enriched</span>
                  </div>
                  <div className="stat-card processing">
                    <span className="stat-number">{stats.processing}</span>
                    <span className="stat-label">Processing</span>
                  </div>
                  <div className="stat-card pending">
                    <span className="stat-number">{stats.pending}</span>
                    <span className="stat-label">Pending</span>
                  </div>
                  <div className="stat-card failed">
                    <span className="stat-number">{stats.failed}</span>
                    <span className="stat-label">Failed</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Companies Section */}
            <div className="campaign-companies-section">
              <div className="section-header">
                <h2>Companies ({companies.length})</h2>
              </div>

              <div className="campaign-companies-table-wrapper">
                <table className="campaign-companies-table">
                  <thead>
                    <tr>
                      <th>Company Name</th>
                      <th>Domain</th>
                      <th>Industry</th>
                      <th>Employees</th>
                      <th>Status</th>
                      <th>Contacts</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {companies.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="empty-state">
                          <div className="empty-state-content">
                            <span className="empty-icon">🏢</span>
                            <p>No companies in this campaign yet</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      companies.map((company) => (
                        <tr 
                          key={company._id}
                          className="clickable-row"
                          onClick={() => navigate(`/master-data/companies/${company._id}`)}
                        >
                          <td className="company-name">{company.name}</td>
                          <td className="company-domain">{company.domain}</td>
                          <td>{company.industry}</td>
                          <td>{company.employees}</td>
                          <td>
                            <span
                              className="status-badge"
                              style={{
                                backgroundColor: statusColors[company.status]?.bg,
                                color: statusColors[company.status]?.text,
                              }}
                            >
                              {company.status}
                            </span>
                          </td>
                          <td>
                            <span className="contact-count-badge">
                              {company.contacts_count}
                            </span>
                          </td>
                          <td>
                            <button 
                              className="action-btn" 
                              title="View Company"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/master-data/companies/${company._id}`);
                              }}
                            >
                              👁️
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

