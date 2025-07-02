"""
Data models for the Designation Finder workflow
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CompanyDesignation(BaseModel):
    """Company and designation input model"""
    company_name: str
    designation: str


class LinkedInProfile(BaseModel):
    """LinkedIn profile result model"""
    name: str
    linkedin_url: str
    title: Optional[str] = None
    company_name: str
    designation_searched: str


class NodeResult(BaseModel):
    """Result from a workflow node"""
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0


class DesignationFinderState(BaseModel):
    """LangGraph state model for Designation Finder workflow - Single company processing"""
    # Single company input
    current_company_designation: Optional[CompanyDesignation] = None
    
    # Results for current company
    found_profiles: List[LinkedInProfile] = Field(default_factory=list)
    
    # Processing status
    processing_successful: bool = False
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Output configuration
    csv_file_path: Optional[str] = None
    run_id: Optional[str] = None
    run_directories: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True