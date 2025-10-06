"""AI agents processing schemas and models."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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


class CommonResponseModel(BaseModel):
    """Common response fields shared by all API responses"""
    identifier: str = Field(examples=["7bb3162a-3105-418d-aa6c-21a958ebc236"])
    success: bool
    errors: List
    failed_entries: List


class ListDataResponse(CommonResponseModel):
    """Response model for endpoints returning list data"""
    data: List


class DictDataResponse(CommonResponseModel):
    """Response model for endpoints returning dictionary data"""
    data: Dict

class FormSubmission(BaseModel):
    web_prompt: str
    persona_prompt: str
    industry: str
    employee_count: str
    revenue_min: str
    revenue_max: str
    location_type: str
    location: str
    keywords: str
    categories: str
    currency: str
    hubspot_email: str
    product_name: str
    business_team: str
    user_email: str



