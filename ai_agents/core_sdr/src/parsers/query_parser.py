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
    
    async def parse_query_with_context(self, 
                                     query: str, 
                                     context: Dict[str, Any] = None,
                                     max_results: int = 20, 
                                     timeout: int = 30,
                                     output_format: str = "json") -> SearchResponse:
        """
        Parse query with additional context or filters.
        
        Args:
            query: Natural language search query
            context: Additional context or filters to apply
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
            output_format: Output format preference
            
        Returns:
            SearchResponse object
        """
        # Add context to the natural language query
        enhanced_query = query
        if context:
            context_parts = []
            if "exclude_industries" in context:
                excluded = ", ".join(context["exclude_industries"])
                context_parts.append(f"excluding {excluded} industries")
            if "required_technologies" in context:
                required = ", ".join(context["required_technologies"])
                context_parts.append(f"using {required}")
            if "min_funding" in context:
                context_parts.append(f"with at least ${context['min_funding']} funding")
            
            if context_parts:
                enhanced_query = f"{query} ({'; '.join(context_parts)})"
        
        return await self.parse_query(enhanced_query, max_results, timeout, output_format)
    
    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Explain what the agent would search for without executing.
        Useful for debugging and transparency.
        """
        return self.agent_processor.explain_query(query)
    
    def explain_parse(self, query: str) -> Dict[str, Any]:
        """
        Parse query and return detailed explanation of what was generated.
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with parsing explanation
        """
        return self.explain_query(query)