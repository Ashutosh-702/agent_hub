import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useLazyGetCompaniesQuery } from '../../store';
import { SearchableSelect } from '../hubspot/ui/SearchableSelect';
import type { Company } from '../../store/api/companyApi';

interface SearchableCompanySelectProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  required?: boolean;
}

const PAGE_SIZE = 5;
const VIRTUALIZATION_THRESHOLD = 10; // Keep max 10 items before current viewport

export const SearchableCompanySelect = ({
  value,
  onChange,
  label = 'Company',
  placeholder = 'Select a company...',
  error,
  required = true,
}: SearchableCompanySelectProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [allCompanies, setAllCompanies] = useState<Company[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  
  // Track loaded page ranges for virtualization
  const loadedPagesRef = useRef<Set<number>>(new Set());
  const scrollDirectionRef = useRef<'up' | 'down'>('down');
  
  const [fetchCompanies] = useLazyGetCompaniesQuery();
  
  // Load companies for a specific page
  const loadPage = useCallback(async (page: number, isNewSearch = false) => {
    if (loadedPagesRef.current.has(page) && !isNewSearch) return;
    
    try {
      const result = await fetchCompanies({
        page,
        limit: PAGE_SIZE,
        name: searchQuery && searchQuery.length >= 2 ? searchQuery : undefined
      }).unwrap();
      
      const newCompanies = result.data || [];
      const pagination = result.pagination;
      
      setTotalRecords(pagination?.total_records || 0);
      setHasMore(pagination?.has_next || false);
      
      loadedPagesRef.current.add(page);
      
      setAllCompanies(prev => {
        if (isNewSearch) {
          return newCompanies;
        }
        
        // Add new companies, avoiding duplicates
        const existingIds = new Set(prev.map(c => c._id));
        const uniqueNewCompanies = newCompanies.filter(c => !existingIds.has(c._id));
        
        // If scrolling down, append; if scrolling up, prepend
        if (scrollDirectionRef.current === 'down') {
          return [...prev, ...uniqueNewCompanies];
        } else {
          return [...uniqueNewCompanies, ...prev];
        }
      });
      
      return newCompanies;
    } catch (err) {
      console.error('Failed to load companies:', err);
      return [];
    }
  }, [fetchCompanies, searchQuery]);
  
  // Initial load
  useEffect(() => {
    const initLoad = async () => {
      setIsInitialLoading(true);
      loadedPagesRef.current.clear();
      setAllCompanies([]);
      setCurrentPage(1);
      await loadPage(1, true);
      setIsInitialLoading(false);
    };
    initLoad();
  }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Handle load more (scroll down)
  const handleLoadMore = useCallback(async () => {
    if (isLoadingMore || !hasMore) return;
    
    setIsLoadingMore(true);
    scrollDirectionRef.current = 'down';
    const nextPage = currentPage + 1;
    
    await loadPage(nextPage);
    setCurrentPage(nextPage);
    
    // Virtualization: Remove companies that are too far above current viewport
    setAllCompanies(prev => {
      if (prev.length > VIRTUALIZATION_THRESHOLD + PAGE_SIZE) {
        // Remove oldest items (from the beginning)
        const itemsToRemove = prev.length - VIRTUALIZATION_THRESHOLD - PAGE_SIZE;
        if (itemsToRemove > 0) {
          // Clear the pages that were removed
          const pagesToClear = Math.floor(itemsToRemove / PAGE_SIZE);
          for (let i = 1; i <= pagesToClear; i++) {
            loadedPagesRef.current.delete(i);
          }
          return prev.slice(itemsToRemove);
        }
      }
      return prev;
    });
    
    setIsLoadingMore(false);
  }, [currentPage, hasMore, isLoadingMore, loadPage]);
  
  // Transform companies to options format
  const options = useMemo(() => {
    return allCompanies.map((company) => {
      const companyId = company._id;
      const companyName = company.identifiers?.name || 'Unknown Company';
      const domain = company.metadata?.api_response?.primary_domain || 
                     company.metadata?.api_response?.website_url?.replace(/^https?:\/\//, '').replace(/\/$/, '') || 
                     '';
      
      return {
        value: companyId,
        label: companyName,
        secondary: domain,
      };
    });
  }, [allCompanies]);
  
  // Handle search - reset pagination when search changes
  const handleSearch = useCallback((query: string) => {
    if (query !== searchQuery) {
      setSearchQuery(query);
      setCurrentPage(1);
      loadedPagesRef.current.clear();
      setHasMore(true);
    }
  }, [searchQuery]);
  
  return (
    <SearchableSelect
      options={options}
      value={value}
      onChange={onChange}
      onSearch={handleSearch}
      onLoadMore={handleLoadMore}
      hasMore={hasMore}
      isLoadingMore={isLoadingMore}
      totalCount={totalRecords}
      label={label}
      placeholder={placeholder}
      error={error}
      isLoading={isInitialLoading}
      required={required}
    />
  );
};

