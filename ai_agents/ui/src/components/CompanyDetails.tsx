import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useLazyGetCompanyDetailsQuery } from '../store';
import type { Company, Contact, Pagination } from '../store';
import { Loader } from './shared';

type CompanyDetailsNavState =
  | {
      from: 'campaign';
      campaignId?: string;
      shortlistingApproach?: string;
    }
  | undefined;

export const CompanyDetails = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const navState = location.state as CompanyDetailsNavState;
  const isFromCampaign = navState?.from === 'campaign';
  // Contacts should be manually shortlisted only for `overall_manual`
  const isOverallManualShortlisting = navState?.shortlistingApproach === 'overall_manual';
  const showContactManualShortlisting = isFromCampaign && isOverallManualShortlisting;
  
  // RTK Query lazy hook for manual triggering (needed for infinite scroll)
  const [fetchDetails, { isLoading: isInitialLoading, error }] = useLazyGetCompanyDetailsQuery();
  
  const [company, setCompany] = useState<Company | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  // Local-only (mock) overrides for manual contact shortlisting; keyed by contact `_id`
  const [manualContactStatus, setManualContactStatus] = useState<Record<string, boolean>>({});
  
  // Pagination for contacts
  const [page, setPage] = useState(1);
  const limit = 5;
  
  // Ref for scroll container
  const contactsScrollRef = useRef<HTMLDivElement>(null);
  const isFetchingRef = useRef(false);

  const fetchCompanyDetails = useCallback(async (pageNum: number, append: boolean = false) => {
    if (!companyId || isFetchingRef.current) return;
    
    isFetchingRef.current = true;
    
    if (append) {
      setIsLoadingMore(true);
    }

    try {
      const result = await fetchDetails({ 
        company_id: companyId, 
        page: pageNum, 
        limit 
      }).unwrap();

      console.log('API Response page', pageNum, ':', result);

      if (result.success) {
        setCompany(result.data.company);
        
        const paginationData = result.pagination;
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
          setHasMore(newContacts.length >= limit);
        }
      }
    } catch (err) {
      console.error('Error fetching company details:', err);
    } finally {
      setIsLoadingMore(false);
      isFetchingRef.current = false;
    }
  }, [companyId, fetchDetails, limit]);

  useEffect(() => {
    setPage(1);
    setContacts([]);
    setHasMore(true);
    fetchCompanyDetails(1, false);
  }, [companyId, fetchCompanyDetails]);

  // Reset local overrides when switching companies
  useEffect(() => {
    setManualContactStatus({});
  }, [companyId]);

  // Handle scroll to load more
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    if (!container || isLoadingMore || !hasMore || isFetchingRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
    
    if (scrollPercentage >= 0.8) {
      const nextPage = page + 1;
      console.log('Loading page:', nextPage);
      setPage(nextPage);
      fetchCompanyDetails(nextPage, true);
    }
  }, [page, isLoadingMore, hasMore, fetchCompanyDetails]);

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
    return String(employees);
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
          onClick={() => {
            if (isFromCampaign && navState?.campaignId) {
              navigate(`/master-data/campaign/${navState.campaignId}`);
              return;
            }
            navigate('/master-data/companies');
          }}
        >
          ← Back
        </button>

        {/* Error State */}
        {error && (
          <div className="error-banner">
            ❌ Failed to load company details
            <button className="retry-btn" onClick={() => fetchCompanyDetails(1, false)}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {isInitialLoading && !company ? (
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
                          {showContactManualShortlisting && (
                            <div className="contact-col">
                              <span className="col-label">Shortlist</span>
                              <select
                                className="status-filter-select"
                                value={String(manualContactStatus[contact._id] ?? false)}
                                onChange={(e) => {
                                  const next = e.target.value === 'true';
                                  setManualContactStatus(prev => ({ ...prev, [contact._id]: next }));
                                }}
                                title="Mock update (API will be added later)"
                              >
                                <option value="true">Shortlisted</option>
                                <option value="false">Not Shortlisted</option>
                              </select>
                            </div>
                          )}
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
