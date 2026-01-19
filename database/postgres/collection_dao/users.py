"""PostgreSQL Users DAO for authentication."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao, generate_objectid
from database.postgres.models import User


class PostgresUsersDao(BasePostgresDao):
    """PostgreSQL Data Access Object for users table."""
    
    model = User
    
    COLUMN_MAP = {
        "_id": "id",
        "email": "email",
        "password_hash": "password_hash",
        "name": "name",
        "is_active": "is_active",
        "last_login_at": "last_login_at",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {}
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_user(self, user: dict) -> str:
        """Create a new user.
        
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
        """Get user by ID.
        
        Args:
            user_id: User's ID as string
            projection: Fields to include/exclude (not fully implemented)
            
        Returns:
            User document or None
        """
        return await self.find_one({"_id": user_id}, projection=projection)

    async def get_user_by_email(self, email: str, projection: dict = None) -> Optional[Dict[str, Any]]:
        """Get user by email address.
        
        Args:
            email: User's email address
            projection: Fields to include/exclude
            
        Returns:
            User document or None
        """
        return await self.find_one({"email": email.lower().strip()}, projection=projection)

    async def update_user(self, user_id: str, update_data: dict) -> int:
        """Update user document.
        
        Args:
            user_id: User's ID as string
            update_data: Fields to update
            
        Returns:
            Number of modified documents
        """
        update_data["updated_at"] = datetime.utcnow()
        return await self.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )

    async def update_last_login(self, user_id: str) -> int:
        """Update user's last login timestamp.
        
        Args:
            user_id: User's ID as string
            
        Returns:
            Number of modified documents
        """
        now = datetime.utcnow()
        return await self.update_one(
            {"_id": user_id},
            {"$set": {"last_login_at": now, "updated_at": now}}
        )

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
        """
        user = await self.find_one({"email": email.lower().strip()}, projection={"_id": 1})
        return user is not None

    async def deactivate_user(self, user_id: str) -> int:
        """Deactivate a user account.
        
        Args:
            user_id: User's ID as string
            
        Returns:
            Number of modified documents
        """
        return await self.update_user(user_id, {"is_active": False})

    async def activate_user(self, user_id: str) -> int:
        """Activate a user account.
        
        Args:
            user_id: User's ID as string
            
        Returns:
            Number of modified documents
        """
        return await self.update_user(user_id, {"is_active": True})

    async def search_users(
        self,
        query: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search users by email or name.
        
        Args:
            query: Search query string
            limit: Max results
            
        Returns:
            List of users ordered by created_at DESC
        """
        conditions = []
        
        if query:
            # Case-insensitive search on email or name
            search_pattern = f"%{query}%"
            conditions.append(
                or_(
                    User.email.ilike(search_pattern),
                    User.name.ilike(search_pattern),
                )
            )
        
        stmt = select(User)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit)
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs


