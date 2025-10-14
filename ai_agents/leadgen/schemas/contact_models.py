# ai_agents/leadgen/schemas/contact_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class ContactData(BaseModel):
    """Contact information model"""
    firstname: str
    lastname: str
    email: List[str] = Field(default_factory=list)
    phone: List[str] = Field(default_factory=list)
    jobtitle: Optional[str] = None
    company: str


class LinkedInData(BaseModel):
    """LinkedIn information model"""
    linkedin_url: Optional[str] = None
    source: str = "LUSHA-ENRICHER"


class ContactMetadata(BaseModel):
    """Contact metadata model"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    lusha_raw_data: Optional[Any] = None


class ContactDocument(BaseModel):
    """Complete contact document model"""
    company_id: str
    contact_data: ContactData
    linkedin_data: LinkedInData
    metadata: ContactMetadata

    def dict(self, *args, **kwargs):
        return super().dict(*args, **kwargs)


class ContactCampaignMetadata(BaseModel):
    """Metadata for contact campaign mapping"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContactCampaignMapping(BaseModel):
    """Contact campaign mapping model"""
    campaign_id: str
    company_id: str
    contact_id: str
    metadata: ContactCampaignMetadata

    def dict(self, *args, **kwargs):
        return super().dict(*args, **kwargs)
