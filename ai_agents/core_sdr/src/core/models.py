import re
from typing import Optional, Literal, Dict, Any, List

from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language search query")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results to return")
    timeout: int = Field(default=30, ge=5, le=300, description="Timeout in seconds")
    output_format: Literal["json", "csv", "summary"] = Field(default="json", description="Output format")
    
    @validator('query')
    def validate_query(cls, v):
        # Check for potential injection patterns
        dangerous_patterns = [
            r'<script', r'javascript:', r'eval\(', r'exec\(',
            r'DROP\s+TABLE', r'DELETE\s+FROM', r'INSERT\s+INTO',
            r'UPDATE\s+SET', r'UNION\s+SELECT', r';\s*(DROP|DELETE|INSERT|UPDATE)'
        ]
        
        query_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                raise ValueError("Query contains potentially dangerous patterns")
        
        return v.strip()


class ParsedEntity(BaseModel):
    location: Optional[Dict[str, str]] = None
    industry: Optional[List[str]] = None
    technology: Optional[List[str]] = None
    employees: Optional[Dict[str, int]] = None
    revenue: Optional[Dict[str, float]] = None
    founded: Optional[Dict[str, int]] = None
    company_type: Optional[str] = None
    is_public: Optional[bool] = None
    is_b2b: Optional[bool] = None


class DSLQuery(BaseModel):
    query: Dict[str, Any]
    size: int = 20
    from_: int = Field(default=0, alias="from")


class SearchResponse(BaseModel):
    search_id: str
    query: Dict[str, Any]
    results: Dict[str, Any]
    metadata: Dict[str, Any]


class Company(BaseModel):
    id: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    hq_location: Optional[str] = None
    employees_count: Optional[int] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    technologies: Optional[List[str]] = None
    is_public: Optional[bool] = None
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class CacheEntry(BaseModel):
    key: str
    query: str
    dsl_query: Dict[str, Any]
    results: List[Company]
    timestamp: float
    credits_used: int
    total_found: int