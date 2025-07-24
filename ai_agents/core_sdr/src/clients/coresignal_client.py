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
    