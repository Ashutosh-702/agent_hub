import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/api.js';

interface Company {
  _id: string;
  identifiers: {
    source_id: string;
    name: string;
  };
  profile: {
    industry: string[];
    revenue_min: string | null;
    revenue_max: string | null;
    employee_count: string[] | null;
  };
  location: {
    type: string;
    name: string[];
  };
  source: string;
  metadata: {
    created_at: string;
    updated_at: string;
    api_response: {
      primary_domain?: string;
      website_url?: string;
      [key: string]: any;
    };
  };
  contact_count: number;
}

interface Pagination {
  page_size: number;
  page_number: number;
  has_next: boolean;
  total_records: number;
}

export const Companies = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination & search state
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [searchName, setSearchName] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // Search modal state
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [searchDomain, setSearchDomain] = useState('');
  const [interestedProduct, setInterestedProduct] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<any>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const fetchCompanies = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (searchName.trim()) {
        params.append('name', searchName.trim());
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/companies?${params}`, {
        method: 'GET',
        headers: {
          'accept': 'application/json',
        },
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setCompanies(result.data || []);
        setPagination(result.pagination || null);
      } else {
        setError(result.message || 'Failed to fetch companies');
      }
    } catch (err) {
      console.error('Error fetching companies:', err);
      setError('Failed to connect to API');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, [page, searchName]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearchName(searchInput);
  };

  const clearSearch = () => {
    setSearchInput('');
    setSearchName('');
    setPage(1);
  };

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1);
    }
  };

  const handleNextPage = () => {
    if (pagination?.has_next) {
      setPage(page + 1);
    }
  };

  // Domain search functions
  const handleDomainSearch = async () => {
    if (!searchDomain.trim()) {
      setSearchError('Please enter a company domain');
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    setSearchResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/apollo_contact_enrichment`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_domain: [searchDomain.trim()],
          interested_product: interestedProduct || 'General',
          slack_metadata: {},
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSearchResult(data);
        // Refresh the list after successful search
        fetchCompanies();
      } else {
        setSearchError(data.message || 'Failed to search company');
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchError('Failed to connect to API');
    } finally {
      setIsSearching(false);
    }
  };

  const closeModal = () => {
    setShowSearchModal(false);
    setSearchDomain('');
    setInterestedProduct('');
    setSearchResult(null);
    setSearchError(null);
  };

  const getDomain = (company: Company): string => {
    return company.metadata?.api_response?.primary_domain || 
           company.metadata?.api_response?.website_url?.replace(/^https?:\/\//, '').replace(/\/$/, '') || 
           '-';
  };

  const getIndustry = (company: Company): string => {
    if (!company.profile?.industry || company.profile.industry.length === 0) {
      return '-';
    }
    return company.profile.industry.slice(0, 2).join(', ') + 
           (company.profile.industry.length > 2 ? '...' : '');
  };

  const getEmployees = (company: Company): string => {
    if (!company.profile?.employee_count) {
      return '-';
    }
    if (Array.isArray(company.profile.employee_count)) {
      return company.profile.employee_count[0] || '-';
    }
    return company.profile.employee_count;
  };

  return (
    <div className="companies-container">
      <div className="companies-card">
        {/* Header */}
        <div className="companies-header">
          <div>
            <h1 className="companies-title">Companies</h1>
            <p className="companies-subtitle">View and search company information</p>
          </div>
          <button
            className="search-company-btn"
            onClick={() => setShowSearchModal(true)}
          >
            <span className="btn-icon">🔍</span>
            Search Company
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="companies-filter-bar">
          <input
            type="text"
            className="companies-filter-input"
            placeholder="Search by company name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit" className="companies-filter-btn">
            Search
          </button>
          {searchName && (
            <button type="button" className="companies-clear-btn" onClick={clearSearch}>
              Clear
            </button>
          )}
        </form>

        {/* Error State */}
        {error && (
          <div className="error-banner">
            ❌ {error}
            <button className="retry-btn" onClick={fetchCompanies}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading companies...</p>
          </div>
        ) : (
          <>
            {/* Companies Table */}
            <div className="companies-table-wrapper">
              <table className="companies-table">
                <thead>
                  <tr>
                    <th>Company Name</th>
                    <th>Domain</th>
                    <th>Industry</th>
                    <th>Employees</th>
                    <th>Contacts</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        <div className="empty-state-content">
                          <span className="empty-icon">🏢</span>
                          <p>No companies found</p>
                          <button
                            className="search-company-btn-small"
                            onClick={() => setShowSearchModal(true)}
                          >
                            Search for a company
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    companies.map((company) => (
                      <tr key={company._id}>
                        <td className="company-name">{company.identifiers?.name || '-'}</td>
                        <td className="company-domain">{getDomain(company)}</td>
                        <td title={company.profile?.industry?.join(', ')}>{getIndustry(company)}</td>
                        <td>{getEmployees(company)}</td>
                        <td>
                          <span className="contact-count-badge">
                            {company.contact_count || 0}
                          </span>
                        </td>
                        <td>
                          <button className="action-btn" title="View Details">
                            👁️
                          </button>
                          <button className="action-btn" title="Refresh">
                            🔄
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && companies.length > 0 && (
              <div className="pagination-container">
                <div className="pagination-info">
                  Showing page {pagination.page_number} 
                  {pagination.total_records > 0 && ` of ${Math.ceil(pagination.total_records / limit)}`}
                  {pagination.total_records > 0 && ` (${pagination.total_records} total)`}
                </div>
                <div className="pagination-controls">
                  <button
                    className="pagination-btn"
                    onClick={handlePrevPage}
                    disabled={page === 1}
                  >
                    ← Previous
                  </button>
                  <span className="pagination-current">Page {page}</span>
                  <button
                    className="pagination-btn"
                    onClick={handleNextPage}
                    disabled={!pagination.has_next}
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Search Modal */}
      {showSearchModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Search Company</h2>
              <button className="modal-close-btn" onClick={closeModal}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="domain">Company Domain *</label>
                <input
                  type="text"
                  id="domain"
                  className="modal-input"
                  placeholder="e.g., example.com"
                  value={searchDomain}
                  onChange={(e) => setSearchDomain(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="product">Interested Product</label>
                <input
                  type="text"
                  id="product"
                  className="modal-input"
                  placeholder="e.g., GaaS, DaaS, Storefront"
                  value={interestedProduct}
                  onChange={(e) => setInterestedProduct(e.target.value)}
                />
              </div>

              {searchError && (
                <div className="search-error">
                  ❌ {searchError}
                </div>
              )}

              {searchResult && (
                <div className="search-result">
                  <h3>Search Result</h3>
                  <pre>{JSON.stringify(searchResult, null, 2)}</pre>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="modal-cancel-btn" onClick={closeModal}>
                Cancel
              </button>
              <button
                className="modal-search-btn"
                onClick={handleDomainSearch}
                disabled={isSearching}
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
