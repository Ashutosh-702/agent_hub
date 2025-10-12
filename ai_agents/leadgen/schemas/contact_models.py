# ai_agents/leadgen/schemas/contact_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

class ContactData(BaseModel):
    """Contact information model"""
    firstname: str
    lastname: str
    email: List[str] = Field(default_factory=list)
    phone: List[str] = Field(default_factory=list)
    jobtitle: Optional[str] = None
    company: str
    company_id: ObjectId

    class Config:
        arbitrary_types_allowed = True  

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
    contact_data: ContactData
    linkedin_data: LinkedInData
    metadata: ContactMetadata

    class Config:
        arbitrary_types_allowed = True  
        # Allow ObjectId serialization
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ContactCampaignMetadata(BaseModel):
    """Metadata for contact campaign mapping"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContactCampaignMapping(BaseModel):
    """Contact campaign mapping model"""
    campaign_id: str
    company_id: ObjectId
    contact_id: str
    metadata: ContactCampaignMetadata

    class Config:
        arbitrary_types_allowed = True  # For ObjectId support
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }