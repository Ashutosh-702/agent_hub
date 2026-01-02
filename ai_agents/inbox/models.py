"""
Inbox Module - Pydantic Models and MongoDB Document Schemas
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============ Enums ============

class Channel(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    CALL = "call"


class Temperature(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    IN_CONVERSATION = "in_conversation"
    WAITING_ON_LEAD = "waiting_on_lead"
    WAITING_ON_US = "waiting_on_us"
    MEETING_SCHEDULED = "meeting_scheduled"
    DEAL_OPEN = "deal_open"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DORMANT = "dormant"


class StageStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXITED = "exited"


class Direction(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# ============ Embedded Models ============

class Company(BaseModel):
    name: str
    domain: Optional[str] = None


class Contact(BaseModel):
    id: str
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None


class Owner(BaseModel):
    name: str
    email: str


class SequenceStep(BaseModel):
    step_name: str
    channel: Channel
    step_number: int


class SequenceEnrollment(BaseModel):
    outreach_campaign_id: str
    outreach_campaign_name: str
    current_stage: SequenceStep
    stage_status: StageStatus = StageStatus.ACTIVE
    last_step_at: Optional[datetime] = None
    next_step_at: Optional[datetime] = None
    exit_reason: Optional[Literal["replied", "bounced", "manual_stop", "converted"]] = None


class LastTouch(BaseModel):
    channel: Channel
    direction: Direction
    snippet: str
    at: datetime


class EventMeta(BaseModel):
    subject: Optional[str] = None
    message_status: Optional[MessageStatus] = None
    call_duration_sec: Optional[int] = None
    meeting_id: Optional[str] = None
    sequence: Optional[Dict[str, Any]] = None
    external_link: Optional[str] = None
    lemlist_inbox_id: Optional[str] = None
    lemlist_message_id: Optional[str] = None


class Note(BaseModel):
    id: str
    at: datetime
    author: str
    text: str


# ============ Main Models ============

class LeadSummary(BaseModel):
    lead_id: str
    company: Company
    contact: Contact
    owner: Owner
    channels_present: List[Channel] = []
    temperature: Temperature = Temperature.COLD
    temperature_drivers: List[str] = []
    status: LeadStatus = LeadStatus.NEW
    in_sequence: bool = False
    sequence: Optional[SequenceEnrollment] = None
    last_touch: Optional[LastTouch] = None
    next_step_at: Optional[datetime] = None
    unread_count: int = 0


class EngagementEvent(BaseModel):
    id: str
    lead_id: str
    channel: Channel
    direction: Direction
    at: datetime
    title: Optional[str] = None
    content: str
    meta: Optional[EventMeta] = None


class LeadDetail(BaseModel):
    summary: LeadSummary
    events: List[EngagementEvent] = []
    notes: List[Note] = []


# ============ API Request/Response Models ============

class ListLeadsParams(BaseModel):
    query: Optional[str] = None
    channel: Optional[Channel] = None
    temperature: Optional[Temperature] = None
    status: Optional[LeadStatus] = None
    in_sequence: Optional[Literal["any", "yes", "no"]] = "any"
    stage_status: Optional[StageStatus] = None
    owner_email: Optional[str] = None
    sort: Optional[Literal["recent", "attention", "hot"]] = "recent"
    tab: Optional[Literal["all", "attention", "sequence"]] = "all"
    page: int = 1
    page_size: int = 50


class ListLeadsResponse(BaseModel):
    leads: List[LeadSummary]
    total: int
    page: int
    page_size: int
    has_next: bool


class UpdateLeadRequest(BaseModel):
    temperature: Optional[Temperature] = None
    status: Optional[LeadStatus] = None
    temperature_drivers: Optional[List[str]] = None


class UpdateSequenceRequest(BaseModel):
    stage_status: Optional[StageStatus] = None


class AddNoteRequest(BaseModel):
    text: str


class AttentionReason(BaseModel):
    type: Literal["unread_reply", "overdue_step", "waiting_on_us", "hot_stale"]
    message: str


# ============ MongoDB Document Models ============

class InboxEventDocument(BaseModel):
    """MongoDB document for storing engagement events"""
    lead_id: str
    channel: Channel
    direction: Direction
    at: datetime
    title: Optional[str] = None
    content: str
    meta: Optional[Dict[str, Any]] = None
    lemlist_inbox_id: Optional[str] = None
    lemlist_message_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class InboxLeadDocument(BaseModel):
    """MongoDB document for storing aggregated lead inbox data"""
    lead_id: str
    company: Dict[str, Any]
    contact: Dict[str, Any]
    owner: Dict[str, Any]
    channels_present: List[str] = []
    temperature: str = "cold"
    temperature_drivers: List[str] = []
    status: str = "new"
    in_sequence: bool = False
    sequence: Optional[Dict[str, Any]] = None
    last_touch: Optional[Dict[str, Any]] = None
    next_step_at: Optional[datetime] = None
    unread_count: int = 0
    lemlist_inbox_id: Optional[str] = None
    lemlist_contact_id: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ============ Lemlist API Response Models ============

class LemlistUser(BaseModel):
    user_id: str = Field(alias="userId")
    sender: bool = False
    read: bool = False

    class Config:
        populate_by_name = True


class LemlistContact(BaseModel):
    id: str = Field(alias="_id")
    full_name: Optional[str] = Field(None, alias="fullName")
    email: Optional[str] = None

    class Config:
        populate_by_name = True


class LemlistInbox(BaseModel):
    id: str = Field(alias="_id")
    opportunities: List[str] = []
    last_activity_at: Optional[datetime] = Field(None, alias="lastActivityAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    channels: List[str] = []
    team_id: Optional[str] = Field(None, alias="teamId")
    contact_id: Optional[str] = Field(None, alias="contactId")
    users: List[LemlistUser] = []
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    have_replies: bool = Field(False, alias="haveReplies")
    last_replied_at: Optional[datetime] = Field(None, alias="lastRepliedAt")
    last_replied_channel: Optional[str] = Field(None, alias="lastRepliedChannel")
    contact: Optional[LemlistContact] = None

    class Config:
        populate_by_name = True


class LemlistPagination(BaseModel):
    total_items: int = Field(0, alias="totalItems")
    current_page: int = Field(1, alias="currentPage")
    next_page: Optional[int] = Field(None, alias="nextPage")
    previous_page: Optional[int] = Field(None, alias="previousPage")
    per_page: int = Field(10, alias="perPage")
    total_pages: int = Field(1, alias="totalPages")

    class Config:
        populate_by_name = True


class LemlistInboxListResponse(BaseModel):
    data: List[LemlistInbox] = []
    pagination: Optional[LemlistPagination] = None


class LemlistMessage(BaseModel):
    id: str = Field(alias="_id")
    inbox_id: Optional[str] = Field(None, alias="inboxId")
    channel: str = "email"
    direction: str = "outbound"  # "inbound" or "outbound"
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    subject: Optional[str] = None
    body: Optional[str] = None
    text: Optional[str] = None  # Plain text version
    status: Optional[str] = None  # sent, delivered, read, failed

    class Config:
        populate_by_name = True


# ============ Webhook Event Models ============

class LemlistWebhookEvent(BaseModel):
    event_type: str = Field(alias="type")
    inbox_id: Optional[str] = Field(None, alias="inboxId")
    contact_id: Optional[str] = Field(None, alias="contactId")
    message_id: Optional[str] = Field(None, alias="messageId")
    channel: Optional[str] = None
    timestamp: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

