"""
Data models for the SDR workflow
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Company(BaseModel):
    """Company model"""
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None


class Contact(BaseModel):
    """Contact data model"""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: str
    department: Optional[str] = None
    seniority: Optional[str] = None


class NodeResult(BaseModel):
    """Result from a workflow node"""
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0


class ErrorSummary(BaseModel):
    """Categorized error tracking for workflow"""
    skipped_companies: List[Dict[str, str]] = Field(default_factory=list)  # [{"company": "name", "reason": "not relevant"}]
    prospect_enrichment_failures: List[Dict[str, str]] = Field(default_factory=list)  # [{"company": "name", "error": "LinkedIn search failed"}]
    hubspot_failures: List[Dict[str, str]] = Field(default_factory=list)  # [{"contact": "name", "error": "duplicate found"}]
    web_enrichment_failures: List[Dict[str, str]] = Field(default_factory=list)  # [{"company": "name", "error": "web search failed"}]
    general_errors: List[str] = Field(default_factory=list)  # Other errors that don't fit categories


class WorkflowState(BaseModel):
    """LangGraph state model for SDR workflow"""
    # Basic workflow state
    companies: List[Company] = Field(default_factory=list)
    current_company_index: int = 0
    current_company: Optional[Company] = None
    
    # Enrichment data
    enriched_data: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    contacts: Dict[str, List[Contact]] = Field(default_factory=dict)
    
    # LinkedIn profiles data
    all_linkedin_profiles: List[Dict[str, Any]] = Field(default_factory=list)
    consolidated_prospects_file: Optional[str] = None
    
    # Errors and logging - Enhanced error categorization
    errors: List[str] = Field(default_factory=list)  # Keep for backward compatibility
    error_summary: ErrorSummary = Field(default_factory=ErrorSummary)  # New categorized errors
    logs: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Output files
    saved_files: List[str] = Field(default_factory=list)
    backup_files: List[str] = Field(default_factory=list)
    run_id: Optional[str | int] = None
    run_directories: Dict[str, str]
    
    class Config:
        arbitrary_types_allowed = True 