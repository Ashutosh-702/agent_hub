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
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize query string by removing potentially harmful content.
        
        Args:
            query: Raw query string
            
        Returns:
            Sanitized query string
        """
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove HTML tags
        query = re.sub(r'<[^>]+>', '', query)
        
        # Remove special characters that could be used for injection
        query = re.sub(r'[<>"\';\\]', '', query)
        
        return query
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key string
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key:
            return False
        
        # Basic format validation - adjust based on actual CoreSignal API key format
        if len(api_key) < 10 or not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
    
    @staticmethod
    def normalize_output_format(format_str: str) -> str:
        """
        Normalize output format string.
        
        Args:
            format_str: Output format string
            
        Returns:
            Normalized format string
        """
        format_str = format_str.lower().strip()
        valid_formats = ['json', 'csv', 'summary']
        
        if format_str not in valid_formats:
            return 'json'  # Default fallback
        
        return format_str