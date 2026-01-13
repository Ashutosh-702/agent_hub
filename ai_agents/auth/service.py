"""Authentication service for Agent Hub."""

import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime
from fastapi import HTTPException

from database.factory import get_users_dao, get_user_tokens_dao
from config.loaded_config import loaded_config
from ai_agents.auth.utils import (
    hash_password,
    verify_password,
    generate_token,
    calculate_expiry,
    validate_email,
    validate_password,
)


logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, connection_manager=None):
        """
        Initialize AuthService with database connection.
        
        Args:
            connection_manager: Optional ConnectionManager instance.
                              If not provided, uses loaded_config.connection_manager
        """
        cm = connection_manager or loaded_config.connection_manager
        self.users_dao = get_users_dao(cm)
        self.tokens_dao = get_user_tokens_dao(cm)

    def _user_to_response(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert user document to response format (removes sensitive fields).
        
        Args:
            user: User document from database
            
        Returns:
            User dict safe for response
        """
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at"),
        }

    async def register(
        self, 
        email: str, 
        password: str, 
        name: str
    ) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password (plain text)
            name: User's display name
            
        Returns:
            Dict with user data and authentication token
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Validate email format
        if not validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate name
        if not name or len(name.strip()) < 1:
            raise HTTPException(status_code=400, detail="Name is required")
        
        # Check if email already exists
        if await self.users_dao.email_exists(email):
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user document
        user_doc = {
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "name": name.strip(),
            "is_active": True,
        }
        
        # Insert user
        user_id = await self.users_dao.create_user(user_doc)
        logger.info(f"Created new user: {email}")
        
        # Generate token
        token = generate_token()
        _, expires_at = calculate_expiry()
        
        # Store token
        await self.tokens_dao.create_token(
            user_id=str(user_id),
            token=token,
            expires_at=expires_at
        )
        
        # Get created user
        user = await self.users_dao.get_user_by_id(str(user_id))
        
        return {
            "success": True,
            "data": {
                "user": self._user_to_response(user),
                "token": token,
                "expires_at": expires_at.isoformat(),
            }
        }

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and return a token.
        
        Args:
            email: User's email address
            password: User's password (plain text)
            
        Returns:
            Dict with user data and authentication token
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user = await self.users_dao.get_user_by_email(email)
        
        if not user:
            logger.warning(f"Login failed: user not found for {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"Login failed: user {email} is inactive")
            raise HTTPException(status_code=401, detail="Account is inactive")
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            logger.warning(f"Login failed: invalid password for {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login timestamp
        await self.users_dao.update_last_login(str(user["_id"]))
        
        # Generate new token
        token = generate_token()
        _, expires_at = calculate_expiry()
        
        # Store token
        await self.tokens_dao.create_token(
            user_id=str(user["_id"]),
            token=token,
            expires_at=expires_at
        )
        
        logger.info(f"User logged in: {email}")
        
        # Get updated user (with last_login_at)
        user = await self.users_dao.get_user_by_id(str(user["_id"]))
        
        return {
            "success": True,
            "data": {
                "user": self._user_to_response(user),
                "token": token,
                "expires_at": expires_at.isoformat(),
            }
        }

    async def validate_token_and_get_user(self, token: str) -> Dict[str, Any]:
        """
        Validate a token and return the associated user.
        Called by routing.py for every protected request.
        
        Args:
            token: Authentication token
            
        Returns:
            User dict (safe for response, no password_hash)
            
        Raises:
            HTTPException: If token is invalid, expired, or revoked
        """
        # Get valid token (not revoked, not expired)
        token_doc = await self.tokens_dao.get_valid_token(token)
        
        if not token_doc:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get user
        user = await self.users_dao.get_user_by_id(str(token_doc["user_id"]))
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        return self._user_to_response(user)

    async def logout(self, token: str) -> Dict[str, Any]:
        """
        Logout by revoking the current token.
        
        Args:
            token: Token to revoke
            
        Returns:
            Success message
        """
        await self.tokens_dao.revoke_token(token)
        logger.info("Token revoked (logout)")
        
        return {
            "success": True,
            "message": "Successfully logged out"
        }

    async def logout_all_devices(self, user_id: str) -> Dict[str, Any]:
        """
        Logout from all devices by revoking all tokens for a user.
        
        Args:
            user_id: User ID to logout
            
        Returns:
            Success message with count of revoked tokens
        """
        count = await self.tokens_dao.revoke_all_user_tokens(user_id)
        logger.info(f"Revoked {count} tokens for user {user_id}")
        
        return {
            "success": True,
            "message": f"Logged out from {count} device(s)"
        }

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User dict or None
        """
        user = await self.users_dao.get_user_by_id(user_id)
        if user:
            return self._user_to_response(user)
        return None

