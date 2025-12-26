import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCompaniesQuery } from '../store';
import { DataTable, EmptyState, ErrorBanner, Loader, PageHeader, Pagination } from './shared';
import type { DataTableColumn } from './shared';
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

  const columns: Array<DataTableColumn<Company>> = [
    {
      id: 'name',
      header: 'Company Name',
      cell: (company) => <span className="company-name">{company.identifiers?.name || '-'}</span>,
    },
    {
      id: 'domain',
      header: 'Domain',
      cell: (company) => <span className="company-domain">{getDomain(company)}</span>,
    },
    {
      id: 'industry',
      header: 'Industry',
      cell: (company) => (
        <span title={company.profile?.industry?.join(', ') || ''}>{getIndustry(company)}</span>
      ),
    },
    {
      id: 'employees',
      header: 'Employees',
      cell: (company) => getEmployees(company),
    },
    {
      id: 'contacts',
      header: 'Contacts',
      cell: (company) => (
        <span className="contact-count-badge">{company.contact_count || 0}</span>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (company) => (
        <button
          className="action-btn"
          title="View Details"
          aria-label="View company details"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/master-data/companies/${company._id}`);
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      ),
    },
  ];

  return (
    <div className="companies-container">
      <div className="companies-card">
        {/* Header */}
        <div className="companies-header">
          <PageHeader
            variant="inline"
            title="Companies"
            subtitle="View and search company information"
            titleClassName="companies-title"
            subtitleClassName="companies-subtitle"
          />
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
        {error && <ErrorBanner message="Failed to load companies" onRetry={() => refetch()} />}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading companies..." />
        ) : (
          <>
            {/* Companies Table */}
            <div className="companies-table-wrapper">
              <DataTable<Company>
                rows={companies}
                columns={columns}
                getRowKey={(c) => c._id}
                onRowClick={(c) => navigate(`/master-data/companies/${c._id}`)}
                rowClassName={() => 'clickable-row'}
                tableClassName="companies-table"
                emptyState={
                  <div className="empty-state">
                    <div className="empty-state-content">
                      <EmptyState 
                        title="No companies found"
                        icon={
                          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.4 }}>
                            <path d="M3 21h18"/>
                            <path d="M5 21V7l8-4v18"/>
                            <path d="M19 21V11l-6-4"/>
                            <path d="M9 9h.01"/>
                            <path d="M9 12h.01"/>
                            <path d="M9 15h.01"/>
                          </svg>
                        }
                      />
                    </div>
                  </div>
                }
              />
            </div>

            {/* Pagination */}
            {pagination && companies.length > 0 && (
              <Pagination
                currentPage={pagination.page_number}
                totalRecords={pagination.total_records}
                pageSize={limit}
                hasNext={pagination.has_next}
                onPrevious={handlePrevPage}
                onNext={handleNextPage}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};
