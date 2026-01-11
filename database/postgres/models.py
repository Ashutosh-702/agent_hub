"""SQLAlchemy models for PostgreSQL database.

This module defines all database models for the Agent Hub application,
mapping MongoDB collections to PostgreSQL tables with a hybrid approach:
- Frequently queried fields are stored as native columns with indexes
- Complex nested data is stored in JSONB columns for flexibility
- ObjectId-style string IDs (24-char hex) are preserved for API compatibility
"""

from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, Index, 
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """User model for authentication.
    
    MongoDB Collection: users
    """
    __tablename__ = "users"
    
    # Primary key - 24-char hex string (ObjectId format)
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    
    # Core fields (indexed for queries)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    tokens: Mapped[List["UserToken"]] = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class UserToken(Base):
    """User authentication tokens.
    
    MongoDB Collection: user_tokens
    """
    __tablename__ = "user_tokens"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(24), ForeignKey("users.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tokens")
    
    # Composite index for token validation queries
    __table_args__ = (
        Index("ix_user_tokens_validation", "token", "is_revoked", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<UserToken(id={self.id}, user_id={self.user_id})>"


class Campaign(Base):
    """Campaign model for prospecting campaigns.
    
    MongoDB Collection: campaigns
    """
    __tablename__ = "campaigns"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    
    # Core fields (indexed for queries)
    name: Mapped[Optional[str]] = mapped_column(String(500), index=True)
    campaign_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    lifecycle_status: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    prospecting_status: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB fields for complex nested data
    prompts: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    segmentation: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    target: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    ownership: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    lifecycle: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    prospecting_cycle: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    sequence_enrollment: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)  # 'metadata' is reserved
    shortlisting_approach: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    company_runs: Mapped[List["CampaignCompanyRun"]] = relationship("CampaignCompanyRun", back_populates="campaign", cascade="all, delete-orphan")
    contact_runs: Mapped[List["CampaignContactRun"]] = relationship("CampaignContactRun", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name})>"


class Company(Base):
    """Company model for companies data.
    
    MongoDB Collection: companies
    """
    __tablename__ = "companies"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    
    # Core fields (indexed for queries)
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    primary_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Industry as array (for filtering)
    industry: Mapped[Optional[list]] = mapped_column(ARRAY(String(255)), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB fields for complex nested data
    identifiers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    profile: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    location: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    deep_research: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    red_flags_history: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    
    # Relationships
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    meetings: Mapped[List["Meeting"]] = relationship("Meeting", back_populates="company", cascade="all, delete-orphan")
    company_runs: Mapped[List["CampaignCompanyRun"]] = relationship("CampaignCompanyRun", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name})>"


class Contact(Base):
    """Contact model for contacts data.
    
    MongoDB Collection: contacts
    """
    __tablename__ = "contacts"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(24), ForeignKey("companies.id"), index=True)
    
    # Core fields (indexed for queries)
    firstname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    jobtitle: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Status fields
    webhook_sent: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    enrichment_status: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    is_relevant: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB fields for complex nested data
    contact_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    linkedin_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="contacts")
    contact_runs: Mapped[List["CampaignContactRun"]] = relationship("CampaignContactRun", back_populates="contact", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, email={self.email})>"


class CampaignCompanyRun(Base):
    """Junction table linking campaigns to companies.
    
    MongoDB Collection: campaign_company_runs
    """
    __tablename__ = "campaign_company_runs"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(24), ForeignKey("campaigns.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(24), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Status fields
    company_status: Mapped[bool] = mapped_column(Boolean, default=False)
    linkedin_contact_status: Mapped[bool] = mapped_column(Boolean, default=False)
    is_relevant: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)  # NULL = not processed yet
    sync_to_hubspot_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB for additional metadata
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="company_runs")
    company: Mapped["Company"] = relationship("Company", back_populates="company_runs")
    
    __table_args__ = (
        UniqueConstraint("campaign_id", "company_id", name="uq_campaign_company"),
        Index("ix_campaign_company_runs_composite", "campaign_id", "company_id"),
    )
    
    def __repr__(self) -> str:
        return f"<CampaignCompanyRun(id={self.id}, campaign_id={self.campaign_id}, company_id={self.company_id})>"


class CampaignContactRun(Base):
    """Junction table linking campaigns to contacts with enrichment data.
    
    MongoDB Collection: campaign_contact_runs
    """
    __tablename__ = "campaign_contact_runs"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(24), ForeignKey("campaigns.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(24), ForeignKey("companies.id"), nullable=False, index=True)
    contact_id: Mapped[str] = mapped_column(String(24), ForeignKey("contacts.id"), nullable=False, index=True)
    
    # Status fields
    is_relevant: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)  # NULL = not processed yet
    enrichment_status: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)  # NULL = not processed yet
    personalization_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Contact enrichment data
    email_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    personalized_message: Mapped[Optional[str]] = mapped_column(Text)
    ai_generated_deck: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB for additional metadata and sequence enrollment
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    sequence_enrollment: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="contact_runs")
    company: Mapped["Company"] = relationship("Company")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="contact_runs")
    
    __table_args__ = (
        UniqueConstraint("campaign_id", "contact_id", name="uq_campaign_contact"),
        Index("ix_campaign_contact_runs_composite", "campaign_id", "contact_id"),
    )
    
    def __repr__(self) -> str:
        return f"<CampaignContactRun(id={self.id}, campaign_id={self.campaign_id}, contact_id={self.contact_id})>"


class Meeting(Base):
    """Meeting model for client calls.
    
    MongoDB Collection: meetings
    """
    __tablename__ = "meetings"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)  # UUID
    company_id: Mapped[Optional[str]] = mapped_column(String(24), ForeignKey("companies.id"), index=True)
    
    # Meeting details
    meeting_name: Mapped[Optional[str]] = mapped_column(String(500))
    call_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled", index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    company_domain: Mapped[Optional[str]] = mapped_column(String(255))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Post-call summary
    summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # JSONB for arrays and complex nested data
    contact_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)  # Array of ObjectId strings
    product_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)  # Array of product strings
    transcript: Mapped[Optional[list]] = mapped_column(JSONB, default=list)  # Array of transcript entries
    live_insights: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    action_items: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    next_steps: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    key_discussion_points: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    objections_resolutions: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    products_discussed: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    battlecard: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    reflections: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="meetings")
    
    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, meeting_id={self.meeting_id}, status={self.status})>"


class InboxLead(Base):
    """Aggregated lead inbox data.
    
    MongoDB Collection: inbox_leads
    """
    __tablename__ = "inbox_leads"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Lemlist identifiers
    lemlist_inbox_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    lemlist_contact_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Lead status fields
    temperature: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    in_sequence: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    owner_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Timestamps
    last_touch_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    next_step_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB for complex nested data
    company: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    contact: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    owner: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    sequence: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    last_touch: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    channels_present: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    temperature_drivers: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    
    # Relationships
    events: Mapped[List["InboxEvent"]] = relationship("InboxEvent", back_populates="lead", cascade="all, delete-orphan")
    notes: Mapped[List["InboxNote"]] = relationship("InboxNote", back_populates="lead", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<InboxLead(id={self.id}, lead_id={self.lead_id})>"


class InboxEvent(Base):
    """Inbox events (messages, calls, etc.).
    
    MongoDB Collection: inbox_events
    """
    __tablename__ = "inbox_events"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(100), ForeignKey("inbox_leads.lead_id"), nullable=False, index=True)
    
    # Event details
    channel: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    direction: Mapped[Optional[str]] = mapped_column(String(20))  # inbound/outbound
    at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Lemlist identifiers
    lemlist_inbox_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    lemlist_message_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # JSONB for event data
    data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    lead: Mapped["InboxLead"] = relationship("InboxLead", back_populates="events")
    
    __table_args__ = (
        Index("ix_inbox_events_lead_at", "lead_id", "at"),
        Index("ix_inbox_events_composite", "lead_id", "at", "channel"),
    )
    
    def __repr__(self) -> str:
        return f"<InboxEvent(id={self.id}, lead_id={self.lead_id}, channel={self.channel})>"


class InboxNote(Base):
    """Notes on inbox leads.
    
    MongoDB Collection: inbox_notes
    """
    __tablename__ = "inbox_notes"
    
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(100), ForeignKey("inbox_leads.lead_id"), nullable=False, index=True)
    
    # Note content
    author: Mapped[Optional[str]] = mapped_column(String(255))
    text: Mapped[Optional[str]] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    lead: Mapped["InboxLead"] = relationship("InboxLead", back_populates="notes")
    
    __table_args__ = (
        Index("ix_inbox_notes_lead_at", "lead_id", "at"),
    )
    
    def __repr__(self) -> str:
        return f"<InboxNote(id={self.id}, lead_id={self.lead_id})>"


