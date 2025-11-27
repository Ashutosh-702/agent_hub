from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ApolloResponseSchema(BaseModel):
    company_name: str
    company_id: str
    person_seniorities: Optional[List[str]] = None
    contact_email_status: Optional[List[str]] = None
    page: int = 1
    per_page: int = 10
    enrich_contacts: bool = False
    reveal_personal_emails: bool = False
    reveal_phone_number: bool = False
    additional_params: Optional[Dict[str, Any]] = None
    
class SearchEnrichPeopleSchema(BaseModel):
    person_seniorities: Optional[List[str]] = None  
    contact_email_status: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    page: int = 1
    per_page: int = 10
    enrich_contacts: bool = False
    reveal_personal_emails: bool = False
    reveal_phone_number: bool = False
    additional_params: Optional[Dict[str, Any]] = None

class SearchPeopleSchema(BaseModel):
    person_seniorities: Optional[List[str]] = None
    contact_email_status: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    page: int = 1
    per_page: int = 10
    additional_params: Optional[Dict[str, Any]] = None

class ContactsSaveToDbSchema(BaseModel):
    person_data: Dict[str, Any] = Field(..., description="The person data from the Apollo API")
    enriched_data: Optional[Dict[str, Any]] = Field(..., description="The enriched data from the Apollo API")
    company_id: str = Field(..., description="The company ID")