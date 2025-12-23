import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config/api.js';
import { Loader } from './shared';

interface Contact {
  _id: string;
  company_id: string;
  contact_data: {
    firstname: string;
    lastname: string;
    email: string[];
    phone: string[];
    jobtitle: string;
    company: string;
  };
  linkedin_data: {
    linkedin_url: string;
    source: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
  };
}

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
    name: string | string[];
  };
  source: string;
  metadata: {
    created_at: string;
    updated_at: string;
  };
}

interface Pagination {
  page_size: number;
  page_number: number;
  has_next: boolean;
  total_records: number;
}

export const CompanyDetails = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  
  const [company, setCompany] = useState<Company | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  
  // Pagination for contacts
  const [page, setPage] = useState(1);
  const limit = 5;
  
  // Ref for scroll container
  const contactsScrollRef = useRef<HTMLDivElement>(null);
  // Flag to prevent multiple simultaneous fetches
  const isFetchingRef = useRef(false);

  const fetchCompanyDetails = async (pageNum: number, append: boolean = false) => {
    if (!companyId || isFetchingRef.current) return;
    
    isFetchingRef.current = true;
    
    if (append) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const params = new URLSearchParams({
        company_id: companyId,
        page: pageNum.toString(),
        limit: limit.toString(),
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/company_details_with_contacts?${params}`, {
        method: 'GET',
        headers: {
          'accept': 'application/json',
        },
      });

      const result = await response.json();
      console.log('API Response page', pageNum, ':', result);

      if (response.ok && result.success) {
        setCompany(result.data.company);
        
        // Handle pagination - check both result.pagination and result.data.pagination
        const paginationData = result.pagination || result.data?.pagination;
        setPagination(paginationData);
        
        const newContacts = result.data.contacts || [];
        
        if (append) {
          setContacts(prev => [...prev, ...newContacts]);
        } else {
          setContacts(newContacts);
        }
        
        // Determine if there are more contacts to load
        if (paginationData && paginationData.has_next !== undefined) {
          setHasMore(paginationData.has_next === true);
        } else {
          // If no pagination info, check if we got fewer results than limit
          setHasMore(newContacts.length >= limit);
        }
      } else {
        setError(result.message || 'Failed to fetch company details');
      }
    } catch (err) {
      console.error('Error fetching company details:', err);
      setError('Failed to connect to API');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
      isFetchingRef.current = false;
    }
  };

  useEffect(() => {
    setPage(1);
    setContacts([]);
    setHasMore(true);
    fetchCompanyDetails(1, false);
  }, [companyId]);

  // Handle scroll to load more
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    if (!container || isLoadingMore || !hasMore || isFetchingRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
    
    console.log('Scroll:', { scrollTop, scrollHeight, clientHeight, scrollPercentage, hasMore });
    
    // Load more when scrolled to 80% of the container
    if (scrollPercentage >= 0.8) {
      const nextPage = page + 1;
      console.log('Loading page:', nextPage);
      setPage(nextPage);
      fetchCompanyDetails(nextPage, true);
    }
  }, [page, isLoadingMore, hasMore]);

  const getLocation = (location: Company['location']): string => {
    if (!location?.name) return '-';
    if (Array.isArray(location.name)) {
      return location.name.join(', ');
    }
    return location.name;
  };

  const getIndustries = (industries: string[] | undefined): string => {
    if (!industries || industries.length === 0) return '-';
    return industries.join(', ');
  };

  const getEmployees = (employees: string[] | null): string => {
    if (!employees) return '-';
    if (Array.isArray(employees)) {
      return employees.join(', ');
    }
    return employees;
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="company-details-container">
      <div className="company-details-card">
        {/* Back Button */}
        <button
          className="back-to-companies-btn"
          onClick={() => navigate('/master-data/companies')}
        >
          ← Back to Companies
        </button>

        {/* Error State */}
        {error && (
          <div className="error-banner">
            ❌ {error}
            <button className="retry-btn" onClick={() => fetchCompanyDetails(1, false)}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <Loader size="large" text="Loading company details..." />
        ) : company ? (
          <>
            {/* Company Info Section */}
            <div className="company-info-section">
              <h1 className="company-details-title">{company.identifiers?.name || 'Unknown Company'}</h1>
              
              <div className="company-info-grid">
                <div className="info-item">
                  <label>Source</label>
                  <span className="source-badge">{company.source || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Industry</label>
                  <span>{getIndustries(company.profile?.industry)}</span>
                </div>
                <div className="info-item">
                  <label>Employees</label>
                  <span>{getEmployees(company.profile?.employee_count)}</span>
                </div>
                <div className="info-item">
                  <label>Location</label>
                  <span>{getLocation(company.location)}</span>
                </div>
                <div className="info-item">
                  <label>Revenue Range</label>
                  <span>
                    {company.profile?.revenue_min && company.profile?.revenue_max
                      ? `$${company.profile.revenue_min}M - $${company.profile.revenue_max}M`
                      : '-'}
                  </span>
                </div>
                <div className="info-item">
                  <label>Created</label>
                  <span>{formatDate(company.metadata?.created_at)}</span>
                </div>
              </div>
            </div>

            {/* Contacts Section */}
            <div className="contacts-section">
              <div className="contacts-section-header">
                <h2>Contacts {pagination?.total_records ? `(${pagination.total_records})` : `(${contacts.length})`}</h2>
              </div>

              <div 
                className="contacts-scroll-container" 
                ref={contactsScrollRef}
                onScroll={handleScroll}
              >
                <div className="contacts-list">
                  {contacts.length === 0 && !isLoadingMore ? (
                    <div className="empty-state-box">
                      <span className="empty-icon">👤</span>
                      <p>No contacts found for this company</p>
                    </div>
                  ) : (
                    contacts.map((contact) => (
                      <div key={contact._id} className="contact-card">
                        <div className="contact-card-grid">
                          <div className="contact-col name-col">
                            <span className="col-label">Name</span>
                            <span className="col-value name">
                              {contact.contact_data?.firstname} {contact.contact_data?.lastname}
                            </span>
                          </div>
                          <div className="contact-col">
                            <span className="col-label">Job Title</span>
                            <span className="col-value">{contact.contact_data?.jobtitle || '-'}</span>
                          </div>
                          <div className="contact-col">
                            <span className="col-label">Email</span>
                            <span className="col-value email">
                              {contact.contact_data?.email?.length > 0 
                                ? contact.contact_data.email.join(', ') 
                                : '-'}
                            </span>
                          </div>
                          <div className="contact-col">
                            <span className="col-label">Phone</span>
                            <span className="col-value">
                              {contact.contact_data?.phone?.length > 0 
                                ? contact.contact_data.phone.join(', ') 
                                : '-'}
                            </span>
                          </div>
                          <div className="contact-col">
                            <span className="col-label">LinkedIn</span>
                            {contact.linkedin_data?.linkedin_url ? (
                              <a 
                                href={contact.linkedin_data.linkedin_url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="linkedin-link"
                              >
                                View Profile
                              </a>
                            ) : <span className="col-value">-</span>}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                
                {/* Loading more indicator */}
                {isLoadingMore && (
                  <div className="load-more-indicator">
                    <Loader size="small" text="Loading more contacts..." />
                  </div>
                )}
                
                {/* End of list indicator */}
                {!isLoadingMore && contacts.length > 0 && !hasMore && (
                  <div className="end-of-list">
                    No more contacts to load
                  </div>
                )}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
