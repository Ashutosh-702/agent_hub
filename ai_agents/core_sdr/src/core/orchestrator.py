import logging
import time
import uuid
from typing import Dict, Any, Optional,List
import re
from .models import SearchRequest, SearchResponse
from .validator import InputValidator
from ..cache import CacheManager
from ..formatters import format_search_response
from ..parsers import AgentMCPQueryProcessor
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
    4. Process with Agent MCP
    5. Process Results
    6. Format Response
    7. Update Statistics
    8. Cache Results
    9. Health Check
    10. Return Response
    """
    
    def __init__(self, 
                 coresignal_api_key: str,
                 coresignal_base_url: str = "https://api.coresignal.com",
                 mongo_uri: Optional[str] = None,
                 cache_ttl_hours: int = 24):
        
        
        self.coresignal_api_key = coresignal_api_key
        self.coresignal_base_url = coresignal_base_url
        self.validator = InputValidator()
        self.cache_manager = CacheManager(
            mongo_uri=mongo_uri,
            default_ttl=cache_ttl_hours * 3600
        )
        loader = AgentMCPQueryProcessor(system_instructions="")
        self.search_prompt = loader._load_prompt("system_search.txt")
        self.collect_prompt = loader._load_prompt("system_collect.txt")
        self.hybrid_prompt = loader._load_prompt("system_hybrid.txt")
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"Cache initialized: {cache_stats.get('cache_type', 'unknown')} - Connected: {self.cache_manager.is_connected()}")
        
        self.stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_used': 0,
            'total_processing_time': 0
        }
    
    async def process_search_request(self, request_data: Dict[str, Any]) -> SearchResponse:
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
            logger.info(f"Processing search request {search_id}")
            search_request = self._validate_input(request_data)
            logger.debug(f"Validated input: {search_request.query}")
            
            numbers_in_query = re.findall(r'\b(\d+)\b', search_request.query)
            requested_count = int(numbers_in_query[0]) if numbers_in_query else 5
            
            base_query = re.sub(r'\b\d+\b', '', search_request.query).strip()
            base_query = re.sub(r'\s+', ' ', base_query) 
            
            cache_params = {
                'timeout': search_request.timeout,
                'output_format': search_request.output_format
            }
            
            cached_result = self.cache_manager.get(base_query, cache_params)
            
            if cached_result:
                cached_count = len(cached_result.results)
                
                if cached_count >= requested_count:
                    logger.info(f"Cache hit - returning {requested_count} companies")
                    self.stats['cache_hits'] += 1
                    logger.info(f"Full cache hit for query: {search_request.query}")
                    logger.info(f"Cached company IDs: {cached_result.results}")

                    return await self._create_response_from_cache(cached_result, search_id, requested_count)
                else:
                    logger.info(f"Partial cache hit - have {cached_count}, getting more from agent")
                    self.stats['cache_hits'] += 1
                    remaining_request = SearchRequest(
                        query=search_request.query,
                        timeout=search_request.timeout,
                        output_format=search_request.output_format
                    )
                    
                    cached_company_ids = cached_result.results
                    new_response = await self._process_with_agent_mcp(remaining_request,cached_company_ids)
                    new_companies = new_response.results.get('companies', [])
                    # cached_names = {company.get('name', '').lower().strip() for company in cached_result.results}
                    unique_new_companies = [
                        company for company in new_companies 
                        if company.get('company_id', '') not in cached_company_ids
                    ]
                    all_companies = cached_company_ids + [company.get('company_id') for company in unique_new_companies]
                    logger.info(f"Combined {len(cached_company_ids)} cached + {len(unique_new_companies)} new = {len(all_companies)} total")
                    companies = new_response.results['companies']
                    company_ids = [c["company_id"] for c in companies]
                    try:
                        self.cache_manager.set(
                            query=base_query,
                            params=cache_params,
                            dsl_query=new_response.query,
                            results=company_ids,
                            credits_used=cached_result.credits_used + new_response.metadata.get('tokens_used', 0),
                            total_found=len(all_companies)
                        )
                        logger.info(f"Updated cache with {len(all_companies)} total companies")
                    except Exception as cache_error:
                        logger.warning(f"Failed to update cache: {cache_error}")
                    
                    
                    final_companies = all_companies[:requested_count]
                    lookup = {c["company_id"]: c for c in new_companies}

                    final_company_list = [
                        lookup.get(c, c) if isinstance(c, str) else c for c in final_companies
                    ]
                    
                    return SearchResponse(
                        search_id=search_id,
                        query=new_response.query,
                        results={
                            "total_found": len(all_companies),
                            "returned": len(final_company_list),
                            "companies": final_company_list
                        },
                        metadata={
                            "credits_used": new_response.metadata.get('tokens_used', 0),
                            "processing_time": time.time() - start_time,
                            "cached": True,
                            "partial_cache": True,
                            "cached_results": cached_count,
                            "new_results": len(new_companies),
                            "timestamp": time.time()
                        }
                    )
            
            logger.info(f"Cache miss")
            self.stats['cache_misses'] += 1
            
            response = await self._process_with_agent_mcp(search_request)
            logger.info(f"Agent MCP returned {len(response.results.get('companies', []))} companies")
            
            if (response.metadata.get('error') is None and response.results.get('companies') and len(response.results['companies']) > 0):
    
                try:
                    companies = response.results['companies']
                    company_ids = [c["company_id"] for c in companies]
                    self.cache_manager.set(
                        query=base_query,
                        params=cache_params,
                        dsl_query=response.query, 
                        results=company_ids,
                        credits_used=response.metadata.get('tokens_used', 0),
                        total_found=len(companies)
                    )
                    logger.debug(f"Cached {len(companies)} companies")
                    
                except Exception as cache_error:
                    logger.warning(f"Failed to cache results: {cache_error}")
            
            tokens_used = response.metadata.get('tokens_used', 0)
            
            processing_time = time.time() - start_time
            response.metadata.update({
                'processing_time': processing_time,
                'cached': False,
                'search_id': search_id
            })
            self._update_stats(tokens_used, processing_time)
            
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
    
    async def _process_with_agent_mcp(self, search_request: SearchRequest, cached_company_ids: Optional[List[str]] = None) -> SearchResponse:
        """Process query using Agent SDK + Coresignal MCP"""
        try:
            requested_count=0
            match = re.search(r'\b(\d+)\b', search_request.query)
            if match:
                requested_count = int(match.group(1))
            if cached_company_ids and len(cached_company_ids) >= requested_count:
                system_instructions = self.collect_prompt
            elif cached_company_ids:
                system_instructions = self.hybrid_prompt
            else:
                system_instructions = self.search_prompt
            self.agent_processor = AgentMCPQueryProcessor(system_instructions=system_instructions)
            return await self.agent_processor.process_query(
                search_request, cached_company_ids
            )
        except Exception as e:
            raise LeadGenerationError(f"Agent MCP processing failed: {str(e)}")
    
    
    async def _create_response_from_cache(self, cached_result, search_id: str, requested_count: int = None) -> SearchResponse:
        """Create response from cached data"""
        
        if requested_count is not None:
            raw_ids = cached_result.results[:requested_count]
        else:
            raw_ids = cached_result.results

        search_request = SearchRequest(
            query=cached_result.query,
            timeout=30,
            output_format="summary"
        )
        response = await self._process_with_agent_mcp(search_request, cached_company_ids=raw_ids)
        companies = response.results["companies"]
        
        return SearchResponse(
            search_id=search_id,
            query={
                "original": cached_result.query,
                "parsed_entities": {},
                "dsl": cached_result.dsl_query
            },
            results={
                "total_found": cached_result.total_found,
                "returned": len(companies),
                "companies": companies 
            },
            metadata={
                "credits_used": cached_result.credits_used,
                "processing_time": 0.0, 
                "cached": True,
                "timestamp": time.time(),
                "cached_at": cached_result.timestamp
            }
        )
    
    def _update_stats(self, tokens_or_credits_used: int, processing_time: float):
        """Update processing statistics"""
        self.stats['total_searches'] += 1
        self.stats['total_tokens_used'] += tokens_or_credits_used 
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
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
        try:
            if not self.coresignal_api_key:
                health['components']['coresignal'] = 'missing API key'
                health['status'] = 'unhealthy'
            else:
                health['components']['coresignal'] = 'API key configured'
        except Exception as e:
            health['components']['coresignal'] = f'error: {str(e)}'
            health['status'] = 'unhealthy'
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            if cache_stats.get('cache_type') == 'mongodb' and cache_stats.get('connected'):
                health['components']['cache'] = f"mongodb connected ({cache_stats.get('active_entries', 0)} entries)"
            elif cache_stats.get('cache_type') == 'mongodb':
                health['components']['cache'] = 'mongodb disconnected'
                health['status'] = 'degraded'
            else:
                health['components']['cache'] = 'no-op (no mongodb)'
        except Exception as e:
            health['components']['cache'] = f'error: {str(e)}'
            health['status'] = 'degraded'
        
        return health