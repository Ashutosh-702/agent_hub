import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import SearchRequest, SearchResponse, Company
from .validator import InputValidator
from ..cache import CacheManager
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
        self.coresignal_api_key = coresignal_api_key  # Store for health check validation
        
        # Initialize components
        self.validator = InputValidator()
        self.query_parser = QueryParser(config_dir)
        self.cache_manager = CacheManager(
            mongo_uri=mongo_uri,
            default_ttl=cache_ttl_hours * 3600
        )
        
        # Track processing statistics for Agent SDK + MCP workflow
        self.stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_used': 0,   # Agent SDK + MCP workflow
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
            
            response = await self._process_with_agent_mcp(search_request)
            logger.info(f"Agent MCP returned {len(response.results.get('companies', []))} companies")
            
            
            tokens_used = response.metadata.get('tokens_used', 0)
            
            processing_time = time.time() - start_time
            response.metadata.update({
                'processing_time': processing_time,
                'cached': False,
                'search_id': search_id
            })
            
            # Update statistics
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
    
    async def _process_with_agent_mcp(self, search_request: SearchRequest) -> SearchResponse:
        """Step 4-7: Process query using Agent SDK + Coresignal MCP"""
        try:
            return await self.query_parser.parse_query(
                search_request.query,
                search_request.max_results,
                search_request.timeout,
                search_request.output_format
            )
        except Exception as e:
            raise LeadGenerationError(f"Agent MCP processing failed: {str(e)}")
    
    # Legacy methods removed - replaced by Agent SDK + MCP workflow
    

    
    # _create_response method removed - deprecated legacy method not used in MCP workflow
    
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
    
    def _update_stats(self, tokens_or_credits_used: int, processing_time: float):
        """Update processing statistics"""
        self.stats['total_searches'] += 1
        self.stats['total_tokens_used'] += tokens_or_credits_used  # For MCP workflow
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
    
    # explain_query method removed - Agent SDK handles query parsing automatically
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        # Agent SDK + MCP usage is tracked directly in stats['total_tokens_used']
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
        
        # Check essential configuration files (MCP integration requires fewer configs)
        try:
            required_configs = ['system_config.json']  # Only essential system config needed
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
        
        # Check CoreSignal API key configuration
        try:
            if not self.coresignal_api_key:
                health['components']['coresignal'] = 'missing API key'
                health['status'] = 'unhealthy'
            else:
                health['components']['coresignal'] = 'API key configured'
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