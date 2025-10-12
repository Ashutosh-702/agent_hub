"""AI agents processing schemas and models."""

from re import match
from typing import Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from global_utils.constants import EMAIL_REGEX


class ResponseData(BaseModel):
    """Base response model with common fields for all API responses"""
    success: bool
    data: Union[List, Dict] = Field(default_factory=list)
    errors: List = Field(default_factory=list)
    identifier: str = Field(default_factory=lambda: str(uuid4()))
    failed_entries: List = Field(default_factory=list)
    pagination: Optional[Dict] = None

    def dict(self, *args, **kwargs):
        return super().dict(*args, **kwargs)


class FormSubmission(BaseModel):
    web_prompt: str
    persona_prompt: str
    industry: str
    employee_count: Optional[str] = None
    revenue_min: Optional[str] = None
    revenue_max: Optional[str] = None
    location_type: str
    location: str
    keywords: Optional[str] = None
    categories: Optional[str] = None
    currency: Optional[str] = None  
    hubspot_email: str
    product_name: str
    business_team: str
    user_email: str

    @field_validator('hubspot_email')
    def validate_hubspot_email(cls, hubspot_email):
        if hubspot_email and hubspot_email.strip() and not match(EMAIL_REGEX, hubspot_email):
            raise ValueError("hubspot email is invalid")

        return hubspot_email

    @field_validator('user_email')
    def validate_user_email(cls, user_email):
        if user_email and user_email.strip() and not match(EMAIL_REGEX, user_email):
            raise ValueError("user email is invalid")

        return user_email

class CampaignStatusUpdate(BaseModel):
    campaign_id: str
    status: str


class CompanyMappingList(BaseModel):
    campaign_id: str
    page: int = 1
    limit: int = 10


class CompanyListWithDetails(BaseModel):
    campaign_id: str


class CampaignContactData(BaseModel):
    campaign_id: str
    company_id: Optional[str] = None
    page: int = 1
    limit: int = 10


class LinkedinContactDetails(BaseModel):
    linkedin_url: str


class LushaGetContactEnrichment(BaseModel):
    campaign_id: str
    page: int = 1
    page_size: int = 50
    company_map_list: List[dict]
    departments: List[str]

class LushaContactEnrichment(BaseModel):
    contact_ids: List[str]
    company_source_id_name_mappings: dict
    campaign_id: str
    lusha_request_id: str

class SaveProspectsDataToMongo(BaseModel):
    prospects: List[dict]
    campaign_id: str
    company_name: str
    company_id: str