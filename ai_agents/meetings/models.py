"""Pydantic models for the Client Calls / Meetings module."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class MeetingStatus(str, Enum):
    """Meeting status enum."""
    SCHEDULED = "scheduled"
    PREP = "prep"
    LIVE = "live"
    COMPLETED = "completed"


class CallType(str, Enum):
    """Type of call/meeting."""
    GOOGLE_MEETING = "google_meeting"
    PHONE_CALL = "phone_call"
    IN_PERSON = "in_person"


class InsightType(str, Enum):
    """Types of live insights that can be detected."""
    OBJECTION = "objection"
    BUYING_SIGNAL = "buying_signal"
    COMPETITOR = "competitor"
    PRICING_QUESTION = "pricing_question"
    PRODUCT_OPPORTUNITY = "product_opportunity"
    RISK_FLAG = "risk_flag"
    ACTION_ITEM = "action_item"


class RelationshipStatus(str, Enum):
    """Relationship status assessment."""
    COLD = "cold"
    WARMING = "warming"
    ENGAGED = "engaged"
    CHAMPION = "champion"


class ConfidenceLevel(str, Enum):
    """Confidence level for deals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    """Priority levels for follow-ups."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============ Transcript Models ============

class TranscriptEntry(BaseModel):
    """A single entry in the meeting transcript."""
    timestamp: float = Field(..., description="Timestamp in seconds from meeting start")
    speaker: str = Field(..., description="Speaker identifier: 'user' or 'other'")
    text: str = Field(..., description="The transcribed text")
    is_final: bool = Field(default=True, description="Whether this is a final or interim transcript")


# ============ Live Insight Models ============

class EvidenceRefs(BaseModel):
    """References to evidence supporting an insight."""
    transcript_spans: List[str] = Field(default_factory=list, description="Relevant transcript quotes")
    research_snippets: List[str] = Field(default_factory=list, description="Relevant research snippets")


class LiveInsight(BaseModel):
    """A live insight generated during a call."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique insight ID")
    timestamp: float = Field(..., description="Timestamp when insight was generated")
    type: InsightType = Field(..., description="Type of insight")
    message: str = Field(..., description="Short insight message (max 80 chars)")
    suggested_response: str = Field(default="", description="Suggested response or action")
    evidence: str = Field(default="", description="Quote from transcript that triggered this")
    evidence_refs: EvidenceRefs = Field(default_factory=EvidenceRefs)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score 0-1")
    is_pinned: bool = Field(default=False, description="Whether user pinned this insight")
    is_action_item: bool = Field(default=False, description="Whether marked as action item")


# ============ Action Item Models ============

class ActionItem(BaseModel):
    """An action item from the meeting."""
    text: str = Field(..., description="Action item description")
    owner: Optional[str] = Field(None, description="Person responsible")
    due_date: Optional[datetime] = Field(None, description="Due date if specified")
    completed: bool = Field(default=False)


class ObjectionResolution(BaseModel):
    """An objection raised and how it was resolved."""
    objection: str = Field(..., description="The objection raised")
    resolution: str = Field(..., description="How it was addressed")


# ============ Battlecard Models ============

class BattlecardSection(BaseModel):
    """A section of the battlecard."""
    title: str
    content: str
    bullet_points: List[str] = Field(default_factory=list)


class Battlecard(BaseModel):
    """Pre-meeting battlecard with all preparation materials."""
    generated_at: Optional[datetime] = None
    
    # Sections
    company_snapshot: Optional[BattlecardSection] = None
    contact_snapshot: Optional[BattlecardSection] = None
    why_now_product_fit: Optional[BattlecardSection] = None
    talking_points: List[str] = Field(default_factory=list)
    likely_objections: List[Dict[str, str]] = Field(default_factory=list, description="List of {objection, response}")
    discovery_questions: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    
    # Additional guidance
    recommended_agenda: Optional[str] = None
    key_risks: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)
    
    # User annotations
    user_notes: Optional[str] = None


# ============ Reflections Models ============

class RecommendedFollowUp(BaseModel):
    """A recommended follow-up action."""
    action: str = Field(..., description="The follow-up action")
    priority: Priority = Field(default=Priority.MEDIUM)
    suggested_timeline: Optional[str] = Field(None, description="When to do this")


class AIReflections(BaseModel):
    """AI-generated post-call reflections."""
    generated_at: Optional[datetime] = None
    what_went_well: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    key_learnings: List[str] = Field(default_factory=list)
    relationship_status: Optional[RelationshipStatus] = None
    deal_health_score: Optional[float] = Field(None, ge=0, le=100, description="0-100 score")
    recommended_follow_ups: List[RecommendedFollowUp] = Field(default_factory=list)
    competitive_positioning: Optional[str] = None
    stakeholder_analysis: Optional[str] = None
    risk_assessment: List[str] = Field(default_factory=list)


class ManualReflections(BaseModel):
    """User's manual post-call reflections."""
    updated_at: Optional[datetime] = None
    personal_notes: Optional[str] = None
    what_went_well: List[str] = Field(default_factory=list)
    what_to_improve: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    follow_up_commitments: List[str] = Field(default_factory=list)
    internal_action_items: List[str] = Field(default_factory=list)
    confidence_level: Optional[ConfidenceLevel] = None
    next_call_focus: Optional[str] = None


class MeetingReflections(BaseModel):
    """Combined AI and manual reflections."""
    ai_generated: Optional[AIReflections] = None
    manual: Optional[ManualReflections] = None


# ============ Meeting Record Model ============

class MeetingRecord(BaseModel):
    """Complete meeting record document."""
    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId as string")
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID for the meeting")
    
    # Core references
    company_domain: Optional[str] = None
    company_id: Optional[str] = None
    contact_ids: List[str] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)
    
    # Meeting metadata
    call_type: Optional[CallType] = None
    meeting_name: Optional[str] = None
    notes: Optional[str] = None
    status: MeetingStatus = Field(default=MeetingStatus.SCHEDULED)
    
    # Timestamps
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Live data
    transcript: List[TranscriptEntry] = Field(default_factory=list)
    live_insights: List[LiveInsight] = Field(default_factory=list)
    
    # Post-call summary
    summary: Optional[str] = None
    key_discussion_points: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    objections_resolutions: List[ObjectionResolution] = Field(default_factory=list)
    products_discussed: List[str] = Field(default_factory=list)
    
    # Related meetings
    previous_meetings_refs: List[str] = Field(default_factory=list)
    
    # Battlecard and reflections
    battlecard: Optional[Battlecard] = None
    reflections: Optional[MeetingReflections] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ============ Request/Response Models ============

class CreateMeetingRequest(BaseModel):
    """Request to create a new meeting."""
    company_id: str = Field(..., description="Company ID from masterdata")
    contact_ids: List[str] = Field(..., min_length=1, description="At least one contact required")
    product_ids: List[str] = Field(..., min_length=1, description="At least one product required")
    call_type: CallType = Field(..., description="Type of call: google_meeting, phone_call, or in_person")
    meeting_name: Optional[str] = None
    notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class UpdateMeetingRequest(BaseModel):
    """Request to update meeting fields."""
    meeting_name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[MeetingStatus] = None
    scheduled_at: Optional[datetime] = None


class UpdateManualReflectionsRequest(BaseModel):
    """Request to update manual reflections."""
    personal_notes: Optional[str] = None
    what_went_well: Optional[List[str]] = None
    what_to_improve: Optional[List[str]] = None
    key_takeaways: Optional[List[str]] = None
    follow_up_commitments: Optional[List[str]] = None
    internal_action_items: Optional[List[str]] = None
    confidence_level: Optional[ConfidenceLevel] = None
    next_call_focus: Optional[str] = None


class GenerateBattlecardRequest(BaseModel):
    """Request to generate a battlecard."""
    meeting_id: str


class StartMeetingRequest(BaseModel):
    """Request to start a live meeting."""
    meeting_id: str


class EndMeetingRequest(BaseModel):
    """Request to end a live meeting."""
    meeting_id: str


# ============ WebSocket Message Models ============

class WSMessageBase(BaseModel):
    """Base WebSocket message."""
    type: str


class WSAudioChunk(WSMessageBase):
    """Audio chunk from browser."""
    type: str = "audio_chunk"
    data: bytes


class WSMarkMoment(WSMessageBase):
    """Mark a moment in the transcript."""
    type: str = "mark_moment"
    timestamp: float
    note: Optional[str] = None


class WSPinInsight(WSMessageBase):
    """Pin an insight."""
    type: str = "pin_insight"
    insight_id: str


class WSAddActionItem(WSMessageBase):
    """Convert insight to action item."""
    type: str = "add_action_item"
    insight_id: str


class WSEndMeeting(WSMessageBase):
    """End the meeting."""
    type: str = "end_meeting"


class WSTranscriptInterim(WSMessageBase):
    """Interim transcript from server."""
    type: str = "transcript_interim"
    text: str
    timestamp: float


class WSTranscriptFinal(WSMessageBase):
    """Final transcript from server."""
    type: str = "transcript_final"
    text: str
    speaker: str
    timestamp: float


class WSInsight(WSMessageBase):
    """Single insight from server."""
    type: str = "insight"
    insight: LiveInsight


class WSInsightBatch(WSMessageBase):
    """Batch of insights from server."""
    type: str = "insight_batch"
    insights: List[LiveInsight]


class WSMeetingEnded(WSMessageBase):
    """Meeting ended message with summary."""
    type: str = "meeting_ended"
    summary: str
    key_discussion_points: List[str]
    action_items: List[ActionItem]
    next_steps: List[str]


class WSError(WSMessageBase):
    """Error message."""
    type: str = "error"
    message: str


# ============ Context Models for Insights Engine ============

class CompanyContext(BaseModel):
    """Company context for insights engine."""
    about: Optional[str] = None
    industry: Optional[str] = None
    recent_news: List[str] = Field(default_factory=list)
    key_initiatives: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    pain_points_inferred: List[str] = Field(default_factory=list)


class ProductContext(BaseModel):
    """Product context for insights engine."""
    name: str
    key_features: List[str] = Field(default_factory=list)
    differentiators: List[str] = Field(default_factory=list)
    common_objections: Dict[str, str] = Field(default_factory=dict)
    case_studies: List[str] = Field(default_factory=list)
    pricing_guidance: Optional[str] = None


class ContactContext(BaseModel):
    """Contact context for insights engine."""
    name: str
    title: Optional[str] = None
    persona_insights: Optional[str] = None
    previous_interactions: List[str] = Field(default_factory=list)


class PreviousMeetingContext(BaseModel):
    """Previous meeting context for insights engine."""
    date: str
    summary: Optional[str] = None
    objections_raised: List[str] = Field(default_factory=list)
    next_steps_agreed: List[str] = Field(default_factory=list)
    products_discussed: List[str] = Field(default_factory=list)


class InsightGenerationContext(BaseModel):
    """Full context for insight generation."""
    recent_transcript: List[TranscriptEntry] = Field(default_factory=list)
    company_research: Optional[CompanyContext] = None
    products: List[ProductContext] = Field(default_factory=list)
    contact: Optional[ContactContext] = None
    previous_meetings: List[PreviousMeetingContext] = Field(default_factory=list)

