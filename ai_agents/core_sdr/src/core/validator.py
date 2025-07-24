import re
from typing import Dict, Any, Optional

from pydantic import ValidationError

from .models import SearchRequest


class InputValidator:
    
    @staticmethod
    def validate_search_request(data: Dict[str, Any]) -> SearchRequest:
        """
        Validate and normalize search request data.
        
        Args:
            data: Raw input data dictionary
            
        Returns:
            Validated SearchRequest object
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            return SearchRequest(**data)
        except ValidationError as e:
            raise ValidationError(f"Input validation failed: {e}")
    
    # Unused validation methods removed - MCP handles validation automatically:
    # - sanitize_query() - Agent SDK handles query sanitization
    # - validate_api_key() - MCP handles API key validation  
    # - normalize_output_format() - Format normalization not needed