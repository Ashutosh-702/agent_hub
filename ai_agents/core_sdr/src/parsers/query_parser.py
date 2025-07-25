import os
from typing import Dict, Any

from .agent_mcp_query_processor import AgentMCPQueryProcessor
from ..core.models import SearchRequest, SearchResponse


class QueryParser:
    """Main query parser using Agent SDK with Coresignal MCP."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        
        # Initialize Agent MCP processor
        try:
            self.agent_processor = AgentMCPQueryProcessor(config_dir)
        except Exception as e:
            raise ValueError(f"Failed to initialize Agent MCP processor: {str(e)}")
    
    async def parse_query(self, 
                         query: str, 
                         max_results: int = 20, 
                         timeout: int = 30,
                         output_format: str = "json") -> SearchResponse:
        """
        Parse natural language query using Agent SDK with Coresignal MCP.
        
        Args:
            query: Natural language search query
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
            output_format: Output format preference
            
        Returns:
            SearchResponse object with companies and metadata
        """
        # Create search request
        search_request = SearchRequest(
            query=query,
            max_results=max_results,
            timeout=timeout,
            output_format=output_format
        )
        
        # Process using Agent MCP processor
        return await self.agent_processor.process_query(search_request)