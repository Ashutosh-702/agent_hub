"""
Data models for the SDR workflow
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, model_validator
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


class CompanyRelevance(BaseModel):
    """Company relevance assessment model"""
    company_name: str
    is_relevant: bool
    confidence_level: str  # "high", "medium", "low"
    reasoning: str
    key_factors: List[str] = Field(default_factory=list)
    assessment_timestamp: Optional[str] = None
    website_analyzed: Optional[str] = None
    industry_identified: Optional[str] = None


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
    
    # Company relevance tracking
    company_relevance_assessments: List[CompanyRelevance] = Field(default_factory=list)
    
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
    run_directories: Dict[str, str] = Field(default_factory=dict)
    
    # Progress tracking - Enhanced with per-company and final tracking
    company_progress_files: List[str] = Field(default_factory=list)  # Individual company progress files
    final_progress_files: List[str] = Field(default_factory=list)    # Final consolidated results files
    linkedin_save_count: int = 0                                     # Count of LinkedIn progress saves
    hubspot_save_count: int = 0                                      # Count of HubSpot progress saves
    
    # Workflow totals tracking
    total_linkedin_prospects: int = 0                               # Total LinkedIn prospects found across all companies
    total_hubspot_created: int = 0                                  # Total HubSpot contacts created
    total_hubspot_duplicates: int = 0                               # Total HubSpot duplicates found
    total_hubspot_failed: int = 0                                   # Total HubSpot creation failures
    
    # Missing fields used in workflows
    companies_to_process_count: int = 0                             # Total companies to process
    processed_companies_count: int = 0                              # Companies actually processed
    final_results: List[Dict[str, Any]] = Field(default_factory=list)  # Final workflow results
    hubspot_results: List[Dict[str, Any]] = Field(default_factory=list)  # HubSpot operation results
    
    @model_validator(mode='before')
    @classmethod
    def ensure_error_summary(cls, values):
        """Ensure error_summary is properly initialized"""
        if isinstance(values, dict):
            if 'error_summary' not in values or values['error_summary'] is None:
                values['error_summary'] = ErrorSummary()
        return values
    
    class Config:
        arbitrary_types_allowed = True
        # Ensure proper validation for LangGraph compatibility
        validate_assignment = True 