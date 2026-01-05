"""Users collection DAO for authentication."""

from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
from bson import ObjectId
from datetime import datetime


class UsersDao(BaseMongoDao):
    """Data Access Object for users collection."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "users")

    async def create_user(self, user: dict) -> ObjectId:
        """
        Create a new user.
        
        Args:
            user: User document with email, password_hash, name
            
        Returns:
            Inserted document ID
        """
        now = datetime.utcnow()
        user["created_at"] = now
        user["updated_at"] = now
        user["is_active"] = user.get("is_active", True)
        user["email"] = user["email"].lower().strip()
        return await self.insert_one(user)

    async def get_user_by_id(self, user_id: str, projection: dict = None) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User's ObjectId as string
            projection: Fields to include/exclude
            
        Returns:
            User document or None
        """
        return await self.find_one({"_id": ObjectId(user_id)}, projection=projection)

    async def get_user_by_email(self, email: str, projection: dict = None) -> Optional[Dict[str, Any]]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            projection: Fields to include/exclude
            
        Returns:
            User document or None
        """
        return await self.find_one({"email": email.lower().strip()}, projection=projection)

    async def update_user(self, user_id: str, update_data: dict) -> int:
        """
        Update user document.
        
        Args:
            user_id: User's ObjectId as string
            update_data: Fields to update
            
        Returns:
            Number of modified documents
        """
        update_data["updated_at"] = datetime.utcnow()
        return await self.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

    async def update_last_login(self, user_id: str) -> int:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Number of modified documents
        """
        now = datetime.utcnow()
        return await self.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login_at": now, "updated_at": now}}
        )

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
        """
        user = await self.find_one({"email": email.lower().strip()}, projection={"_id": 1})
        return user is not None

    async def deactivate_user(self, user_id: str) -> int:
        """
        Deactivate a user account.
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Number of modified documents
        """
        return await self.update_user(user_id, {"is_active": False})

    async def activate_user(self, user_id: str) -> int:
        """
        Activate a user account.
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Number of modified documents
        """
        return await self.update_user(user_id, {"is_active": True})
