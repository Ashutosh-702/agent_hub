"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ========================
# Request Schemas
# ========================

class RegisterRequest(BaseModel):
    """Registration request payload."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=4, description="User's password")
    name: str = Field(..., min_length=1, max_length=100, description="User's display name")


class LoginRequest(BaseModel):
    """Login request payload."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# ========================
# Response Schemas
# ========================

class UserResponse(BaseModel):
    """User data in responses (excludes sensitive fields)."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")


class AuthResponse(BaseModel):
    """Authentication response with user and token."""
    
    success: bool = Field(default=True)
    data: dict = Field(..., description="Response data containing user and token")


class MeResponse(BaseModel):
    """Response for /auth/me endpoint."""
    
    success: bool = Field(default=True)
    data: UserResponse = Field(..., description="Current user data")


class LogoutResponse(BaseModel):
    """Response for logout endpoint."""
    
    success: bool = Field(default=True)
    message: str = Field(default="Successfully logged out")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    success: bool = Field(default=False)
    detail: str = Field(..., description="Error message")


# ========================
# Internal Schemas
# ========================

class UserCreate(BaseModel):
    """Internal schema for creating a user."""
    
    email: str
    password_hash: str
    name: str
    is_active: bool = True


class TokenData(BaseModel):
    """Token validation data."""
    
    user_id: str
    token: str
    expires_at: datetime
    is_revoked: bool = False

