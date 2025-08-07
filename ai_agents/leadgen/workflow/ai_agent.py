"""AI Agent processing schemas and models."""

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


class ProcessAddressRequest(BaseModel):
    """Request model for processing a single address"""

    raw_address: str = Field(..., description="The raw address string to process (clean and geocode)",
                             examples=["HousenoC592ndfloorCblockgreenwoodcitySector45,Gurugram,Haryana,122001"])
    get_coordinates: bool = Field(
        default=True, description="Whether to get coordinates from Google Geocoding API")
    max_output_tokens: Optional[int] = Field(
        default=None, description="Maximum number of tokens in the LLM response")
    verbose: bool = Field(
        default=False, description="Enable detailed hierarchical scoring analysis and verbose logging")


class Coordinates(BaseModel):
    """Coordinates model"""

    lat: Optional[float] = Field(description="Latitude")
    lng: Optional[float] = Field(description="Longitude")


class Viewport(BaseModel):
    """Viewport model for Google Maps bounce"""

    northeast: Coordinates = Field(
        description="Northeast corner of the viewport")
    southwest: Coordinates = Field(
        description="Southwest corner of the viewport")


class TokenUsage(BaseModel):
    """Token usage information from OpenAI API"""

    prompt_tokens: Optional[int] = Field(
        description="Number of tokens in the prompt")
    completion_tokens: Optional[int] = Field(
        description="Number of tokens in the completion")
    total_tokens: Optional[int] = Field(
        description="Total number of tokens used")


class ProcessAddressResponse(DictDataResponse):
    """Response model for single address processing endpoint"""
    data: Dict[str, Any] = Field(description="Processed address data")
