"""User tokens collection DAO for authentication."""

import logging
from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)


class UserTokensDao(BaseMongoDao):
    """Data Access Object for user_tokens collection."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "user_tokens")

    async def create_token(self, user_id: str, token: str, expires_at: datetime) -> ObjectId:
        """
        Create a new authentication token.
        
        Args:
            user_id: User's ObjectId as string
            token: Generated token string (UUID)
            expires_at: Token expiration timestamp
            
        Returns:
            Inserted document ID
        """
        token_doc = {
            "user_id": ObjectId(user_id),
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_revoked": False,
        }
        return await self.insert_one(token_doc)

    async def get_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token document by token string.
        
        Args:
            token: Token string to lookup
            
        Returns:
            Token document or None
        """
        return await self.find_one({"token": token})

    async def get_valid_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token only if it's valid (not revoked and not expired).
        
        Args:
            token: Token string to lookup
            
        Returns:
            Token document if valid, None otherwise
        """
        now = datetime.utcnow()
        
        # First check if token exists at all
        any_token = await self.find_one({"token": token})
        if not any_token:
            logger.warning(f"Token not found in database: {token[:8]}...")
        else:
            logger.debug(f"Token found: is_revoked={any_token.get('is_revoked')}, expires_at={any_token.get('expires_at')}, now={now}")
        
        token_doc = await self.find_one({
            "token": token,
            "is_revoked": False,
            "expires_at": {"$gt": now}
        })
        
        if token_doc:
            logger.debug(f"Token is valid for user_id: {token_doc.get('user_id')}")
        else:
            logger.warning(f"Token validation failed - not valid")
            
        return token_doc

    async def revoke_token(self, token: str) -> int:
        """
        Revoke a token (logout).
        
        Args:
            token: Token string to revoke
            
        Returns:
            Number of modified documents
        """
        return await self.update_one(
            {"token": token},
            {"$set": {"is_revoked": True}}
        )

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (force logout from all devices).
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Number of modified documents
        """
        return await self.update_many(
            {"user_id": ObjectId(user_id), "is_revoked": False},
            {"$set": {"is_revoked": True}}
        )

    async def get_user_tokens(self, user_id: str, include_revoked: bool = False) -> List[Dict[str, Any]]:
        """
        Get all tokens for a user.
        
        Args:
            user_id: User's ObjectId as string
            include_revoked: Whether to include revoked tokens
            
        Returns:
            List of token documents
        """
        query = {"user_id": ObjectId(user_id)}
        if not include_revoked:
            query["is_revoked"] = False
        return await self.find_many(query)

    async def cleanup_expired_tokens(self) -> int:
        """
        Delete all expired tokens (cleanup job).
        
        Returns:
            Number of deleted documents
        """
        return await self.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })

    async def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid.
        
        Args:
            token: Token string to check
            
        Returns:
            True if token is valid (exists, not revoked, not expired)
        """
        token_doc = await self.get_valid_token(token)
        return token_doc is not None
