import re
from typing import Optional, Literal, Dict, Any, List

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language search query")
    timeout: int = Field(default=30, ge=5, le=300, description="Timeout in seconds")
    output_format: Literal["json", "csv", "summary"] = Field(default="json", description="Output format")
    
    @field_validator('query')
    def validate_query(cls, v):
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
    results: List[str]
    timestamp: float
    credits_used: int
    total_found: int

class CompanySearchResult(BaseModel):
    """Individual company result from Coresignal MCP"""
    company_id: str = Field(..., description="Unique identifier for the company")
    name: str = Field(..., description="Company name")
    description: str = Field(..., description="Brief company description")

class CoreSignalMCPResponse(BaseModel):
    """Response format for Agent SDK with Coresignal MCP"""
    companies: List[CompanySearchResult] = Field(default_factory=list, description="List of companies found")