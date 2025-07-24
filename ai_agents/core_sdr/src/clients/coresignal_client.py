import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import httpx

from ..core.models import Company, DSLQuery

logger = logging.getLogger(__name__)


class CoreSignalAPIError(Exception):
    """Custom exception for CoreSignal API errors."""
    pass


class CoreSignalClient:
    """Client for interacting with CoreSignal API."""
    
    def __init__(self, 
                 api_key: str,
                 base_url: str = "https://api.coresignal.com",
                 timeout: int = 30,
                 max_workers: int = 5):
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_workers = max_workers
        
        self.session = httpx.Client(
            timeout=timeout,
            headers={
                'apikey': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'LeadGenPrototype/1.0'
            }
        )
        
        # Track API usage
        self.credits_used = 0
        self.requests_made = 0
        self.last_request_time = 0
        
        # Rate limiting (adjust based on your API limits)
        self.min_request_interval = 0.1  # 100ms between requests
    
    def __del__(self):
        """Clean up HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to CoreSignal API with error handling and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data as dictionary
            
        Raises:
            CoreSignalAPIError: If API request fails
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.requests_made += 1
            self.last_request_time = time.time()
            
            # Check for API errors
            if response.status_code == 401:
                raise CoreSignalAPIError("Invalid API key or authentication failed")
            elif response.status_code == 403:
                raise CoreSignalAPIError("API access forbidden - check permissions")
            elif response.status_code == 429:
                raise CoreSignalAPIError("Rate limit exceeded - please wait")
            elif response.status_code >= 400:
                raise CoreSignalAPIError(f"API error {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Track credits if available in response
            if 'credits_used' in data:
                self.credits_used += data['credits_used']
            elif method == 'POST' and 'company_multi_source/search' in endpoint:
                # Estimate credits for search requests
                self.credits_used += 1
            elif method == 'GET' and 'company_multi_source/collect' in endpoint:
                # Estimate credits for collect requests
                self.credits_used += 1
            
            return data
            
        except httpx.TimeoutException:
            raise CoreSignalAPIError(f"Request timeout after {self.timeout} seconds")
        except httpx.RequestError as e:
            raise CoreSignalAPIError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise CoreSignalAPIError(f"Invalid JSON response: {str(e)}")
    
    def search_companies(self, dsl_query: DSLQuery) -> Tuple[List[str], int]:
        """
        Search for companies using DSL query.
        
        Args:
            dsl_query: Elasticsearch DSL query
            
        Returns:
            Tuple of (company_ids, total_found)
            
        Raises:
            CoreSignalAPIError: If search fails
        """
        logger.info(f"Searching companies with DSL query")
        
        try:
            # Extract size from DSL query and remove it
            query_dict = dsl_query.dict(by_alias=True)
            size = query_dict.pop('size', 20)  # Remove size from query body
            from_offset = query_dict.pop('from', 0)  # Remove from as well
            
            response = self._make_request(
                'POST',
                f'/cdapi/v2/company_multi_source/search/es_dsl?size={size}&from={from_offset}',
                json=query_dict
            )
            if isinstance(response, list):
                company_ids = [str(company_id) for company_id in response]
                total_found = len(company_ids)
            else:
                company_ids = []
                total_found = 0
                
                if 'hits' in response:
                    hits = response['hits']
                    total_found = hits.get('total', {}).get('value', 0)
                    
                    for hit in hits.get('hits', []):
                        if '_id' in hit:
                            company_ids.append(hit['_id'])
                        elif '_source' in hit and 'id' in hit['_source']:
                            company_ids.append(str(hit['_source']['id']))
            
            logger.info(f"Found {total_found} companies, returning {len(company_ids)} IDs")
            return company_ids, total_found
            
        except Exception as e:
            logger.error(f"Company search failed: {str(e)}")
            raise CoreSignalAPIError(f"Company search failed: {str(e)}")
    
    def collect_company(self, company_id: str) -> Optional[Company]:
        """
        Collect detailed information for a single company.
        
        Args:
            company_id: Company ID to collect
            
        Returns:
            Company object or None if collection fails
        """
        try:
            response = self._make_request(
                'GET',
                f'/cdapi/v2/company_multi_source/collect/{company_id}'
            )
            
            # Convert response to Company model
            return self._response_to_company(response, company_id)
            
        except CoreSignalAPIError as e:
            logger.warning(f"Failed to collect company {company_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error collecting company {company_id}: {str(e)}")
            return None
    
    def collect_companies_batch(self, company_ids: List[str], 
                              max_workers: Optional[int] = None) -> List[Company]:
        """
        Collect detailed information for multiple companies in parallel.
        
        Args:
            company_ids: List of company IDs to collect
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of Company objects (may be fewer than input if some fail)
        """
        if not company_ids:
            return []
        
        max_workers = max_workers or self.max_workers
        companies = []
        
        logger.info(f"Collecting {len(company_ids)} companies with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all collection tasks
            future_to_id = {
                executor.submit(self.collect_company, company_id): company_id
                for company_id in company_ids
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_id):
                company_id = future_to_id[future]
                try:
                    company = future.result()
                    if company:
                        companies.append(company)
                        logger.debug(f"Successfully collected company {company_id}")
                    else:
                        logger.warning(f"No data returned for company {company_id}")
                except Exception as e:
                    logger.error(f"Failed to collect company {company_id}: {str(e)}")
        
        logger.info(f"Successfully collected {len(companies)} out of {len(company_ids)} companies")
        return companies
    
    def collect_companies_streaming(self, company_ids: List[str], 
                                  batch_size: int = 10) -> List[Company]:
        """
        Collect companies in smaller batches to manage memory and API limits.
        
        Args:
            company_ids: List of company IDs to collect
            batch_size: Number of companies to collect per batch
            
        Returns:
            List of Company objects
        """
        all_companies = []
        
        for i in range(0, len(company_ids), batch_size):
            batch_ids = company_ids[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_ids)} companies")
            
            batch_companies = self.collect_companies_batch(batch_ids)
            all_companies.extend(batch_companies)
            
            # Brief pause between batches to be respectful to the API
            if i + batch_size < len(company_ids):
                time.sleep(0.5)
        
        return all_companies
    
    def _response_to_company(self, response: Dict[str, Any], company_id: str) -> Company:
        """
        Convert API response to Company model.
        
        Args:
            response: API response data
            company_id: Company ID
            
        Returns:
            Company object
        """
        # Extract key fields from the response
        # Note: Field mapping may need adjustment based on actual CoreSignal response format
        
        # Handle nested data structures
        def safe_get(data, path, default=None):
            """Safely get nested dictionary values."""
            try:
                for key in path.split('.'):
                    data = data[key]
                return data
            except (KeyError, TypeError):
                return default
        
        # Extract technologies (limit to top 5)
        technologies = []
        tech_data = safe_get(response, 'technologies_used', [])
        if isinstance(tech_data, list):
            technologies = [
                tech.get('technology', tech) if isinstance(tech, dict) else str(tech)
                for tech in tech_data[:5]
            ]
        
        # Build location string
        location_parts = []
        if safe_get(response, 'hq_city'):
            location_parts.append(safe_get(response, 'hq_city'))
        if safe_get(response, 'hq_state'):
            location_parts.append(safe_get(response, 'hq_state'))
        if safe_get(response, 'hq_country'):
            location_parts.append(safe_get(response, 'hq_country'))
        
        hq_location = ', '.join(location_parts) if location_parts else None
        
        return Company(
            id=company_id,
            company_name=safe_get(response, 'company_name'),
            industry=safe_get(response, 'industry'),
            hq_location=hq_location,
            employees_count=safe_get(response, 'employees_count'),
            founded_year=safe_get(response, 'founded_year'),
            website=safe_get(response, 'website'),
            technologies=technologies,
            is_public=safe_get(response, 'is_public'),
            description=safe_get(response, 'description'),
            raw_data=response  # Store full response for additional processing
        )
    
    def get_api_usage(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'credits_used': self.credits_used,
            'requests_made': self.requests_made,
            'last_request_time': self.last_request_time
        }
    
    def reset_usage_tracking(self):
        """Reset API usage tracking counters."""
        self.credits_used = 0
        self.requests_made = 0
        self.last_request_time = 0