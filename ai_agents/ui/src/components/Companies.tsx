import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCompaniesQuery } from '../store';
import { Button, CounterBadge, EmptyState, Input, NotificationBanner, Spinner, Typography } from 'novus';
import viteLogo from '/vite.svg';
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
            <Typography variant="heading-xl" type="h1" className="companies-title">
              Companies
            </Typography>
            <Typography variant="body-m" type="p" className="companies-subtitle">
              View and search company information
            </Typography>
          </div>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="companies-filter-bar">
          <Input
            value={searchInput}
            placeholder="Search by company name..."
            onChange={(e: any) => setSearchInput(e.target.value)}
            size="m"
            className="companies-filter-input"
            label=""
          />
          <Button type="primary" appearance="default" size="m" className="companies-filter-btn">
            Search
          </Button>
          {searchName && (
            <Button type="secondary" appearance="default" size="m" className="companies-clear-btn" onClick={clearSearch}>
              Clear
            </Button>
          )}
        </form>

        {/* Error State */}
        {error && (
          <NotificationBanner
            appearance="negative"
            type="inline"
            title="Failed to load companies"
            description="Please try again."
            primaryButtonText="Retry"
            onPrimaryClick={() => refetch()}
            showIcon
          />
        )}

        {/* Loading State */}
        {isLoading ? (
          <div style={{ padding: '2rem 0' }}>
            <Spinner size="l" label="Loading companies..." labelPlacement="bottom" />
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
                          <EmptyState
                            type="single"
                            imageURL={viteLogo}
                            title="No companies found"
                            description="Try adjusting your search."
                          />
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
                        <td title={company.profile?.industry?.join(', ') || ''}>{getIndustry(company)}</td>
                        <td>{getEmployees(company)}</td>
                        <td>
                          <CounterBadge content={company.contact_count || 0} />
                        </td>
                        <td>
                          <Button
                            size="s"
                            type="tertiary"
                            appearance="default"
                            className="action-btn"
                            onClick={(e: any) => {
                              e.stopPropagation();
                              navigate(`/master-data/companies/${company._id}`);
                            }}
                          >
                            👁️
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && companies.length > 0 && (
              <div className="pagination-component">
                <div className="pagination-info">
                  Showing page {pagination.page_number}
                  {pagination.total_records > 0 && ` of ${Math.ceil(pagination.total_records / limit)}`}
                  {pagination.total_records > 0 && ` (${pagination.total_records} total)`}
                </div>
                <div className="pagination-controls">
                  <Button
                    type="secondary"
                    appearance="default"
                    size="s"
                    className="pagination-btn"
                    onClick={handlePrevPage}
                    disabled={page === 1}
                  >
                    ← Previous
                  </Button>
                  <span className="pagination-current">Page {page}</span>
                  <Button
                    type="secondary"
                    appearance="default"
                    size="s"
                    className="pagination-btn"
                    onClick={handleNextPage}
                    disabled={!pagination.has_next}
                  >
                    Next →
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
