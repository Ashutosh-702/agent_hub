"""Authentication API routes."""

from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException

from ai_agents.auth.schemas import (
    RegisterRequest,
    LoginRequest,
)
from ai_agents.auth.service import AuthService
from config.loaded_config import loaded_config


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_mongo_client():
    """Get MongoDB client from loaded config."""
    if not loaded_config.connection_manager:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    return loaded_config.connection_manager.mongo_client


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest):
    """
    Register a new user account.
    
    Creates a new user with the provided email, password, and name.
    Returns the user data and an authentication token.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (min 4 chars, must have uppercase, lowercase, number)
    - **name**: Display name (1-100 characters)
    """
    auth_service = AuthService(get_mongo_client())
    return await auth_service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name
    )


@router.post("/login")
async def login(payload: LoginRequest):
    """
    Login with email and password.
    
    Authenticates the user and returns a new token.
    Token is valid for 15 days.
    
    - **email**: Registered email address
    - **password**: User's password
    """
    auth_service = AuthService(get_mongo_client())
    return await auth_service.login(
        email=payload.email,
        password=payload.password
    )


@router.get("/me")
async def get_me(request: Request):
    """
    Get current authenticated user's profile.
    
    Returns the user data for the currently authenticated user.
    Requires a valid Bearer token in the Authorization header.
    """
    # User is already validated and attached by routing.py
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "success": True,
        "data": request.state.user
    }


@router.post("/logout")
async def logout(request: Request):
    """
    Logout current session.
    
    Revokes the current authentication token.
    The token will no longer be valid for future requests.
    """
    # Get token from header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ", 1)[1]
    
    auth_service = AuthService(get_mongo_client())
    return await auth_service.logout(token)


@router.post("/logout-all")
async def logout_all_devices(request: Request):
    """
    Logout from all devices.
    
    Revokes all authentication tokens for the current user.
    This will force logout from all active sessions.
    """
    # User is already validated and attached by routing.py
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = request.state.user["id"]
    
    auth_service = AuthService(get_mongo_client())
    return await auth_service.logout_all_devices(user_id)

