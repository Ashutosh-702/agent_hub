"""AI agents processing schemas and models."""

import re
from re import match
from typing import Dict, List, Optional, Union
from uuid import uuid4

from attr.converters import optional
from pydantic import BaseModel, Field, field_validator, model_validator

from database.collection_dao import campaign_company_runs
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
    web_prompt: Optional[str] = None
    persona_prompt: Optional[str] = None
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
    shortlisting_approach: str


class CreateCampaignFromProspectingJob(BaseModel):
    web_prompt: Optional[str] = None
    persona_prompt: Optional[str] = None
    industry: str
    employee_count: Optional[str] = None
    revenue_min: Optional[str] = None
    revenue_max: Optional[str] = None
    location_type: str
    location: str
    keywords: Optional[str] = None
    categories: Optional[str] = None
    currency: Optional[str] = None  
    hubspot_email: Optional[str] = None
    product_name: Optional[str] = None
    business_team: Optional[str] = None
    user_email: Optional[str] = None
    shortlisting_approach: Optional[str] = None
    prospecting_cycle_status: Optional[str] = "prospecting"

class ManualCompanyQualification(BaseModel):
    campaign_id: str
    company_ids: Optional[List[str]] = None
    selection_type: str = "all"
    is_relevant: bool = True
    
    

    #here company_ids llist is dependent on the selection_type
    #if selection_type is "all", then company_ids should be None
    #if selection_type is "selected", then company_ids should be a list of company ids
   
    @field_validator('company_ids')
    @classmethod
    def normalize_company_ids(cls, company_ids: Optional[List[str]]):
        if company_ids is None:
            return None

        # normalize + de-dupe while preserving order
        seen = set()
        normalized: List[str] = []
        for idx, cid in enumerate(company_ids):
            if not isinstance(cid, str) or not cid.strip():
                raise ValueError(f"company_ids[{idx}] must be a non-empty string")
            cid = cid.strip()
            if cid not in seen:
                seen.add(cid)
                normalized.append(cid)
        return normalized

    @model_validator(mode='after')
    def validate_selection_type_and_limits(self):
        # Backwards/UX compatibility: allow "selective" as alias of "selected"
        if self.selection_type == "selective":
            self.selection_type = "selected"

        allowed = {"all", "selected"}
        if self.selection_type not in allowed:
            raise ValueError(f"selection_type must be one of {sorted(allowed)}")

        if self.selection_type == "all":
            # for all, ignore any accidentally provided list
            self.company_ids = None
            return self

        # selection_type == "selected"
        if not self.company_ids:
            raise ValueError("company_ids cannot be empty when selection_type is 'selected'")

        MAX_COMPANY_IDS = 500
        if len(self.company_ids) > MAX_COMPANY_IDS:
            raise ValueError(f"company_ids too large: {len(self.company_ids)} (max {MAX_COMPANY_IDS})")

        return self

class AiCompanyQualification(BaseModel):
    campaign_id: str
    web_prompt: Optional[str] = None

class ApolloContactList(BaseModel):
    campaign_id: str
    enrichment_status: Optional[bool] = False

class UpdateApolloContactEnrichmentStatus(BaseModel):
    campaign_id: str
    contact_ids: Optional[List[str]] = None
    selection_type: str = "all"
    is_relevant: bool = True

class GetCampaignContactList(BaseModel):
    campaign_id: str
    page: int = 1
    limit: int = 10

class CampaignContactList(BaseModel):
    campaign_id: str
    page: int = 1
    limit: int = 10
    contact_ids: Optional[List[str]] = None
    selection_type: str = "all"

    @field_validator('contact_ids')
    @classmethod
    def normalize_contact_ids(cls, contact_ids: Optional[List[str]]):
        if contact_ids is None:
            return None

        # normalize + de-dupe while preserving order
        seen = set()
        normalized: List[str] = []
        for idx, cid in enumerate(contact_ids):
            if not isinstance(cid, str) or not cid.strip():
                raise ValueError(f"contact_ids[{idx}] must be a non-empty string")
            cid = cid.strip()
            if cid not in seen:
                seen.add(cid)
                normalized.append(cid)
        return normalized

    @model_validator(mode='after')
    def validate_selection_type_and_limits(self):
        allowed = {"all", "selected"}
        if self.selection_type not in allowed:
            raise ValueError(f"selection_type must be one of {sorted(allowed)}")

        if self.selection_type == "all":
            # for all, ignore any accidentally provided list
            self.contact_ids = None
            return self

        # selection_type == "selected"
        if not self.contact_ids:
            raise ValueError("contact_ids cannot be empty when selection_type is 'selected'")

        MAX_COMPANY_IDS = 500
        if len(self.contact_ids) > MAX_COMPANY_IDS:
            raise ValueError(f"contact_ids too large: {len(self.contact_ids)} (max {MAX_COMPANY_IDS})")

        return self

    
class ManualCompanyQualificationResponse(BaseModel):
    campaign_id: str
    company_ids: List[str]
    status: str


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

class CountCompanyMappings(BaseModel):
    campaign_id: str

class Campaigns(BaseModel):
    page: int = 1
    limit: int = 10
    user_email: Optional[str] = None
    product_name: Optional[str] = None
    campaign_id: Optional[str] = None
    status: Optional[str] = None
    prospecting_cycle_status: Optional[str] = None


class ProspectingCampaigns(BaseModel):
    """Schema for fetching campaigns filtered by prospecting_cycle.status"""
    page: int = 1
    limit: int = 10
    prospecting_cycle_status: Optional[str] = None  # e.g., 'prospecting', 'company_qualification', 'contact_qualification', 'contact_enriched'

class Companies(BaseModel):
    page: int = 1
    limit: int = 10
    name: Optional[str] = None
    domain: Optional[str] = None

class CompanyContacts(BaseModel):
    company_id: str
    page: int = 1
    limit: int = 10

class CampaignDetailsWithCompanies(BaseModel):
    campaign_id: str
    company_status: Optional[bool] = None
    page: int = 1
    limit: int = 10


class CompanyQualificationProgress(BaseModel):
    campaign_id: str

class SyncToHubspot(BaseModel):
    campaign_id: str

class SaveContactPersonalization(BaseModel):
    """Schema for saving personalization data for a contact"""
    campaign_id: str
    contact_id: str
    email_id: str
    personalized_message: str
    ai_generated_deck: str  # Public URL of cloud storage

class BulkSaveContactPersonalization(BaseModel):
    """Schema for saving personalization data for multiple contacts"""
    campaign_id: str
    personalizations: List[Dict]  # List of {contact_id, email_id, personalized_message, ai_generated_deck}


class GetEnrollmentContacts(BaseModel):
    """Schema for fetching contacts ready for sequence enrollment"""
    campaign_id: str
    page: int = 1
    limit: int = 100


class EnrollContactsToSequence(BaseModel):
    """Schema for enrolling contacts to a Lemlist sequence"""
    campaign_id: str
    sequence_id: str
    sequence_name: str
    contact_ids: Optional[List[str]] = None  # If None, enroll all personalized contacts

class ApolloContactEnrichment(BaseModel):
    company_domain: List[str] = Field(description="List of company domains to enrich contacts for")
    interested_product: str = Field(description="Interested product to enrich contacts for")
    slack_metadata: Optional[Dict] = None

    @field_validator('company_domain')
    @classmethod
    def validate_domains(cls, v):
        
        domain_pattern = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
        
        for domain in v:
            if not isinstance(domain, str):
                raise ValueError(f"Each domain must be a string, got: {type(domain).__name__}")
            
            domain = domain.strip()
            
            # Check if domain contains invalid characters/prefixes or doesn't match format
            has_protocol = domain.startswith('http://') or domain.startswith('https://')
            has_www = domain.startswith('www.')
            has_path = '/' in domain
            has_port = ':' in domain and not domain.startswith('[')  # Exclude IPv6 addresses
            has_query = '?' in domain or '#' in domain
            invalid_format = not domain or not domain_pattern.match(domain)
            
            if has_protocol or has_www or has_path or has_port or has_query or invalid_format:
                raise ValueError(f"Invalid domain format: '{domain}'. Expected strict format like 'example.com' (no protocol, www, paths, ports, or query parameters)")
        
        return v
