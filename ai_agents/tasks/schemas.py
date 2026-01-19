"""Pydantic schemas for the Tasks module."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ai_agents.tasks.constants import TaskStatus, TaskType, EntityType


# =============================================================================
# Request Schemas
# =============================================================================

class CreateTaskRequest(BaseModel):
    """Request to create a task."""
    primary_entity_type: EntityType
    primary_entity_id: str
    type: str = Field(..., description="Task type (call, followup_email, etc.)")
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    assigned_to_user_id: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    """Request to update a task."""
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    assigned_to_user_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class LemlistEventRequest(BaseModel):
    """Request from Lemlist webhook."""
    # Event type
    type: Optional[str] = Field(None, alias="type")
    
    # Contact info
    email: str = Field(..., description="Contact email (required for lookup)")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    contact_id: Optional[str] = Field(None, alias="contactId")
    
    # Campaign info
    campaign_id: Optional[str] = Field(None, alias="campaignId")
    lead_id: Optional[str] = Field(None, alias="leadId")
    message_id: Optional[str] = Field(None, alias="messageId")
    
    # Company info (for context)
    company_name: Optional[str] = Field(None, alias="companyName")
    company_domain: Optional[str] = Field(None, alias="companyDomain")
    company_industry: Optional[str] = Field(None, alias="companyIndustry")
    
    # Sender info
    sender: Optional[Dict[str, Any]] = None
    
    # HubSpot info
    hubspot_lead_id: Optional[int] = Field(None, alias="hubspotLeadId")
    
    # Allow storing full raw payload
    raw_payload: Optional[Dict[str, Any]] = Field(None, exclude=True)
    
    class Config:
        populate_by_name = True
        extra = "allow"  # Allow extra fields from Lemlist payload


class ListTasksParams(BaseModel):
    """Parameters for listing tasks."""
    statuses: Optional[List[TaskStatus]] = None
    types: Optional[List[str]] = None
    assigned_to_user_id: Optional[str] = None
    overdue: Optional[bool] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[str] = None
    sl_no_lt: Optional[int] = None
    limit: int = Field(50, ge=1, le=100)


# =============================================================================
# Response Schemas
# =============================================================================

class EntityBrief(BaseModel):
    """Brief entity info for task response."""
    id: str
    type: EntityType
    name: Optional[str] = None
    email: Optional[str] = None


class UserBrief(BaseModel):
    """Brief user info."""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None


class TaskLinkResponse(BaseModel):
    """Task link in response."""
    entity_type: EntityType
    entity_id: str
    entity_name: Optional[str] = None
    link_reason: str


class TaskResponse(BaseModel):
    """Task response."""
    id: str
    sl_no: int
    primary_entity_type: EntityType
    primary_entity_id: str
    type: str
    status: TaskStatus
    priority: int
    due_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to_user_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    source_ref: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    effective_due_at: Optional[datetime] = None
    is_overdue: bool = False
    
    # Optional enriched data
    primary_entity: Optional[EntityBrief] = None
    assigned_to: Optional[UserBrief] = None
    links: Optional[List[TaskLinkResponse]] = None


class TaskActivityResponse(BaseModel):
    """Task activity entry."""
    id: str
    sl_no: int
    task_id: str
    at: datetime
    actor_user_id: Optional[str] = None
    event_type: str
    diff_json: Dict[str, Any]
    
    # Optional enriched data
    actor: Optional[UserBrief] = None


class PaginatedNext(BaseModel):
    """Pagination cursor."""
    sl_no_lt: Optional[int] = None


class ListTasksResponse(BaseModel):
    """Response for list tasks."""
    items: List[TaskResponse]
    next: PaginatedNext


class ListActivityResponse(BaseModel):
    """Response for list activity."""
    items: List[TaskActivityResponse]
    next: PaginatedNext


class TaskDetailResponse(BaseModel):
    """Detailed task response with links."""
    task: TaskResponse
    links: List[TaskLinkResponse]
