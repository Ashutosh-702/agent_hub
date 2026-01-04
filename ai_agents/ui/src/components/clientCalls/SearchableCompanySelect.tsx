import { useState, useMemo } from 'react';
import { useGetCompaniesQuery } from '../../store';
import { SearchableSelect } from '../hubspot/ui/SearchableSelect';

interface SearchableCompanySelectProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  required?: boolean;
}

export const SearchableCompanySelect = ({
  value,
  onChange,
  label = 'Company',
  placeholder = 'Select a company...',
  error,
  required = true,
}: SearchableCompanySelectProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  
  // Fetch companies - use search query if provided, otherwise fetch all
  const { data: companiesData, isLoading } = useGetCompaniesQuery({ 
    page: 1, 
    limit: 500,
    name: searchQuery && searchQuery.length >= 2 ? searchQuery : undefined
  });
  
  // Transform companies to options format
  const options = useMemo(() => {
    const companies = companiesData?.data || [];
    return companies.map((company) => {
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
  }, [companiesData]);
  
  // Handle search - debounced search is handled by the SearchableSelect component
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };
  
  return (
    <SearchableSelect
      options={options}
      value={value}
      onChange={onChange}
      onSearch={handleSearch}
      label={label}
      placeholder={placeholder}
      error={error}
      isLoading={isLoading}
      required={required}
    />
  );
};

