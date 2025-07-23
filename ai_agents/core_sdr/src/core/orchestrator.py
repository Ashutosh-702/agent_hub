import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import SearchRequest, SearchResponse, Company, ParsedEntity, DSLQuery
from .validator import InputValidator
from ..cache import CacheManager
from ..clients import CoreSignalClient, CoreSignalAPIError
from ..formatters import format_search_response
from ..parsers import QueryParser

logger = logging.getLogger(__name__)


class LeadGenerationError(Exception):
    """Custom exception for lead generation errors."""
    pass


class LeadGenerationOrchestrator:
    """
    Main orchestrator that coordinates all components of the lead generation system.
    
    This implements Steps 1-10 from the prototype plan:
    1. User Input (handled by calling code)
    2. Input Validation
    3. Cache Check
    4. Query Parsing (NL → DSL)
    5. CoreSignal Search API
    6. Process Search Results
    7. Company Collection
    8. Format Results
    9. Update Caches
    10. Return to User
    """
    
    def __init__(self, 
                 coresignal_api_key: str,
                 coresignal_base_url: str = "https://api.coresignal.com",
                 config_dir: str = "config",
                 mongo_uri: Optional[str] = None,
                 cache_ttl_hours: int = 24):
        
        self.config_dir = Path(config_dir)
        
        # Initialize components
        self.validator = InputValidator()
        self.query_parser = QueryParser(config_dir)
        self.coresignal_client = CoreSignalClient(
            api_key=coresignal_api_key,
            base_url=coresignal_base_url
        )
        self.cache_manager = CacheManager(
            mongo_uri=mongo_uri,
            default_ttl=cache_ttl_hours * 3600
        )
        
        # Track processing statistics
        self.stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_credits_used': 0,
            'total_processing_time': 0
        }
    
    def process_search_request(self, request_data: Dict[str, Any]) -> SearchResponse:
        """
        Process a complete search request through all 10 steps.
        
        Args:
            request_data: Raw search request data
            
        Returns:
            SearchResponse with results and metadata
            
        Raises:
            LeadGenerationError: If processing fails
        """
        start_time = time.time()
        search_id = str(uuid.uuid4())
        
        try:
            # Step 1: Input received (handled by caller)
            logger.info(f"Processing search request {search_id}")
            
            # Step 2: Input Validation
            search_request = self._validate_input(request_data)
            logger.debug(f"Validated input: {search_request.query}")
            
            # Step 3: Cache Check
            cache_params = {
                'max_results': search_request.max_results,
                'timeout': search_request.timeout,
                'output_format': search_request.output_format
            }
            
            cached_result = self.cache_manager.get(search_request.query, cache_params)
            if cached_result:
                logger.info(f"Cache hit for query: {search_request.query}")
                self.stats['cache_hits'] += 1
                return self._create_response_from_cache(cached_result, search_id)
            
            logger.info(f"Cache miss for query: {search_request.query}")
            self.stats['cache_misses'] += 1
            
            # Step 4: Query Parsing (NL → DSL)
            entities, dsl_query = self._parse_query(search_request)
            logger.debug(f"Parsed entities: {entities}")
            
            # Step 5: CoreSignal Search API
            company_ids, total_found = self._search_companies(dsl_query)
            logger.info(f"Found {total_found} companies, got {len(company_ids)} IDs")
            
            # Step 6: Process Search Results
            limited_ids = self._limit_results(company_ids, search_request.max_results)
            
            # Step 7: Company Collection
            companies = self._collect_companies(limited_ids)
            logger.info(f"Collected {len(companies)} companies")
            
            # Step 8: Format Results (handled by caller, but we prepare the data)
            # Results are formatted later based on output_format
            
            # Step 9: Update Caches
            credits_used = self.coresignal_client.credits_used
            self._update_cache(search_request.query, cache_params, dsl_query.dict(), 
                             companies, credits_used, total_found)
            
            # Step 10: Return to User
            processing_time = time.time() - start_time
            response = self._create_response(
                search_id=search_id,
                original_query=search_request.query,
                entities=entities,
                dsl_query=dsl_query,
                companies=companies,
                total_found=total_found,
                credits_used=credits_used,
                processing_time=processing_time,
                cached=False
            )
            
            # Update statistics
            self._update_stats(credits_used, processing_time)
            
            logger.info(f"Completed search request {search_id} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Search request {search_id} failed: {str(e)}")
            raise LeadGenerationError(f"Search processing failed: {str(e)}")
    
    def _validate_input(self, request_data: Dict[str, Any]) -> SearchRequest:
        """Step 2: Input Validation"""
        try:
            return self.validator.validate_search_request(request_data)
        except Exception as e:
            raise LeadGenerationError(f"Input validation failed: {str(e)}")
    
    def _parse_query(self, search_request: SearchRequest) -> tuple[ParsedEntity, DSLQuery]:
        """Step 4: Query Parsing (NL → DSL)"""
        try:
            return self.query_parser.parse_query(
                search_request.query,
                search_request.max_results
            )
        except Exception as e:
            raise LeadGenerationError(f"Query parsing failed: {str(e)}")
    
    def _search_companies(self, dsl_query: DSLQuery) -> tuple[List[str], int]:
        """Step 5: CoreSignal Search API"""
        try:
            return self.coresignal_client.search_companies(dsl_query)
        except CoreSignalAPIError as e:
            raise LeadGenerationError(f"Company search failed: {str(e)}")
    
    def _limit_results(self, company_ids: List[str], max_results: int) -> List[str]:
        """Step 6: Process Search Results"""
        return company_ids[:max_results]
    
    def _collect_companies(self, company_ids: List[str]) -> List[Company]:
        """Step 7: Company Collection"""
        if not company_ids:
            return []
        
        try:
            # Use streaming collection for large batches
            if len(company_ids) > 20:
                return self.coresignal_client.collect_companies_streaming(company_ids)
            else:
                return self.coresignal_client.collect_companies_batch(company_ids)
        except Exception as e:
            logger.warning(f"Company collection partially failed: {str(e)}")
            # Return whatever we could collect
            return []
    
    def _update_cache(self, query: str, params: Dict[str, Any], dsl_query: Dict[str, Any],
                     companies: List[Company], credits_used: int, total_found: int):
        """Step 9: Update Caches"""
        try:
            self.cache_manager.set(
                query=query,
                params=params,
                dsl_query=dsl_query,
                results=companies,
                credits_used=credits_used,
                total_found=total_found
            )
        except Exception as e:
            logger.warning(f"Cache update failed: {str(e)}")
            # Don't fail the entire request if caching fails
    
    def _create_response(self, search_id: str, original_query: str, 
                        entities: ParsedEntity, dsl_query: DSLQuery,
                        companies: List[Company], total_found: int,
                        credits_used: int, processing_time: float,
                        cached: bool) -> SearchResponse:
        """Step 10: Create final response"""
        
        return SearchResponse(
            search_id=search_id,
            query={
                "original": original_query,
                "parsed_entities": entities.dict(exclude_none=True),
                "dsl": dsl_query.dict()
            },
            results={
                "total_found": total_found,
                "returned": len(companies),
                "companies": [company.dict() for company in companies]
            },
            metadata={
                "credits_used": credits_used,
                "processing_time": processing_time,
                "cached": cached,
                "timestamp": time.time()
            }
        )
    
    def _create_response_from_cache(self, cached_result, search_id: str) -> SearchResponse:
        """Create response from cached data"""
        
        return SearchResponse(
            search_id=search_id,
            query={
                "original": cached_result.query,
                "parsed_entities": {},  # Could be stored in cache if needed
                "dsl": cached_result.dsl_query
            },
            results={
                "total_found": cached_result.total_found,
                "returned": len(cached_result.results),
                "companies": [company.dict() for company in cached_result.results]
            },
            metadata={
                "credits_used": cached_result.credits_used,
                "processing_time": 0.0,  # Cached, so no processing time
                "cached": True,
                "timestamp": time.time(),
                "cached_at": cached_result.timestamp
            }
        )
    
    def _update_stats(self, credits_used: int, processing_time: float):
        """Update processing statistics"""
        self.stats['total_searches'] += 1
        self.stats['total_credits_used'] += credits_used
        self.stats['total_processing_time'] += processing_time
    
    def format_response(self, response: SearchResponse, format_type: str) -> str:
        """
        Format the search response in the requested format.
        
        Args:
            response: SearchResponse object
            format_type: Output format ('json', 'csv', 'summary')
            
        Returns:
            Formatted string
        """
        try:
            return format_search_response(response, format_type)
        except Exception as e:
            raise LeadGenerationError(f"Response formatting failed: {str(e)}")
    
    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Explain how a query would be parsed without executing it.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with parsing explanation
        """
        try:
            return self.query_parser.explain_parse(query)
        except Exception as e:
            raise LeadGenerationError(f"Query explanation failed: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        stats['api_usage'] = self.coresignal_client.get_api_usage()
        return stats
    
    def clear_cache(self) -> bool:
        """Clear all cached data"""
        try:
            return self.cache_manager.clear_all()
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Dictionary with health status of each component
        """
        health = {
            'status': 'healthy',
            'components': {},
            'timestamp': time.time()
        }
        
        # Check configuration files
        try:
            required_configs = ['query_mappings.json', 'industries.json', 
                              'technologies.json', 'locations.json']
            for config_file in required_configs:
                config_path = self.config_dir / config_file
                if not config_path.exists():
                    health['components']['config'] = f'Missing {config_file}'
                    health['status'] = 'unhealthy'
                    break
            else:
                health['components']['config'] = 'healthy'
        except Exception as e:
            health['components']['config'] = f'error: {str(e)}'
            health['status'] = 'unhealthy'
        
        # Check CoreSignal API connection (simple validation)
        try:
            if not self.coresignal_client.api_key:
                health['components']['coresignal'] = 'missing API key'
                health['status'] = 'unhealthy'
            else:
                health['components']['coresignal'] = 'configured'
        except Exception as e:
            health['components']['coresignal'] = f'error: {str(e)}'
            health['status'] = 'unhealthy'
        
        # Check cache system
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            if cache_stats.get('cache_type') == 'mongodb' and cache_stats.get('connected'):
                health['components']['cache'] = f"mongodb connected ({cache_stats.get('active_entries', 0)} entries)"
            elif cache_stats.get('cache_type') == 'mongodb':
                health['components']['cache'] = 'mongodb disconnected'
                health['status'] = 'degraded'  # Cache failure shouldn't make system unhealthy
            else:
                health['components']['cache'] = 'no-op (no mongodb)'
        except Exception as e:
            health['components']['cache'] = f'error: {str(e)}'
            health['status'] = 'degraded'
        
        return health