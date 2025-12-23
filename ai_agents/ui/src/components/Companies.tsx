import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCompaniesQuery } from '../store';
import { Loader } from './shared';
import type { Company } from '../store';

export const Companies = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [searchName, setSearchName] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const limit = 10;

  // RTK Query hook - handles loading, error, caching automatically
  const { data, isLoading, error, refetch } = useGetCompaniesQuery({ 
    page, 
    limit, 
    name: searchName || undefined 
  });

  const companies = data?.data || [];
  const pagination = data?.pagination;

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
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (pagination?.has_next) setPage(page + 1);
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
    return String(company.profile.employee_count);
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
            ❌ Failed to load companies
            <button className="retry-btn" onClick={() => refetch()}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading companies..." />
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
                          <button 
                            className="action-btn" 
                            title="View Details"
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
    </div>
  );
};
