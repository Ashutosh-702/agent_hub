import os
from typing import Dict, Any

from .llm_dsl_generator import LLMDSLGenerator
from ..core.models import DSLQuery
from ..schema import SchemaManager


class QueryParser:
    """Main query parser using LLM for direct DSL generation."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.schema_manager = SchemaManager(f"{config_dir}/system_config.json")
        
        # Initialize LLM generator if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            # Model preference: env var > config file > default
            env_model = os.getenv('LLM_MODEL')
            config_model = self.schema_manager.config.get("llm_config", {}).get("model", "gpt-4o")
            model = env_model or config_model
            
            self.llm_generator = LLMDSLGenerator(
                api_key=api_key,
                model=model,
                schema_manager=self.schema_manager
            )
        else:
            self.llm_generator = None
    
    def parse_query(self, 
                   query: str, 
                   max_results: int = 20, 
                   from_offset: int = 0) -> DSLQuery:
        """
        Parse natural language query directly into DSL query using LLM.
        
        Args:
            query: Natural language search query
            max_results: Maximum number of results to return
            from_offset: Offset for pagination
            
        Returns:
            DSLQuery object
        """
        if not self.llm_generator:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        
        try:
            # Generate DSL directly from natural language
            dsl_dict = self.llm_generator.generate_dsl(query, max_results, from_offset)
            return DSLQuery(**dsl_dict)
        except Exception as e:
            # Fallback to simple query if LLM fails
            fallback_dsl = self._create_fallback_dsl(query, max_results, from_offset)
            return DSLQuery(**fallback_dsl)
    
    def _create_fallback_dsl(self, query: str, max_results: int, from_offset: int) -> Dict[str, Any]:
        """Create a fallback DSL query when LLM is unavailable."""
        return {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["company_name^3", "industry^2", "description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": max_results,
            "from": from_offset
        }
    
    def parse_query_with_context(self, 
                               query: str, 
                               context: Dict[str, Any] = None,
                               max_results: int = 20, 
                               from_offset: int = 0) -> DSLQuery:
        """
        Parse query with additional context or filters.
        
        Args:
            query: Natural language search query
            context: Additional context or filters to apply
            max_results: Maximum number of results to return
            from_offset: Offset for pagination
            
        Returns:
            DSLQuery object
        """
        # For now, we'll add context to the natural language query
        # In the future, we could modify the LLM prompt to handle context
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
        
        return self.parse_query(enhanced_query, max_results, from_offset)
    
    def explain_parse(self, query: str) -> Dict[str, Any]:
        """
        Parse query and return detailed explanation of what was generated.
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with parsing explanation
        """
        if not self.llm_generator:
            return {
                "original_query": query,
                "error": "LLM generator not available - OpenAI API key not configured",
                "generated_dsl": self._create_fallback_dsl(query, 20, 0),
                "interpretation": "Fallback multi-match query"
            }
        
        try:
            return self.llm_generator.explain_generation(query)
        except Exception as e:
            fallback_dsl = self._create_fallback_dsl(query, 20, 0)
            return {
                "original_query": query,
                "error": str(e),
                "generated_dsl": fallback_dsl,
                "interpretation": "Fallback multi-match query due to LLM error"
            }