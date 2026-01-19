"""PostgreSQL TaskLinks DAO."""

from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.postgres.base_dao import BasePostgresDao, generate_objectid
from database.postgres.models import TaskLink


class PostgresTaskLinksDao(BasePostgresDao):
    """PostgreSQL Data Access Object for task_links table."""
    
    model = TaskLink
    
    COLUMN_MAP = {
        "_id": "id",
        "task_id": "task_id",
        "entity_type": "entity_type",
        "entity_id": "entity_id",
        "link_reason": "link_reason",
        "created_at": "created_at",
    }
    
    JSONB_FIELDS = {}
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_link_idempotent(
        self,
        task_id: str,
        entity_type: str,
        entity_id: str,
        link_reason: str,
    ) -> str:
        """Create a task link with idempotency (ON CONFLICT DO NOTHING).
        
        Args:
            task_id: Task ID
            entity_type: Entity type (contact|company|deal)
            entity_id: Entity ID
            link_reason: Reason for link (primary, derived_company, etc.)
            
        Returns:
            Link ID (new or existing)
        """
        link_data = {
            "id": generate_objectid(),
            "task_id": task_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "link_reason": link_reason,
            "created_at": datetime.utcnow(),
        }
        
        # Remove sl_no - it's GENERATED ALWAYS
        if "sl_no" in link_data:
            del link_data["sl_no"]
        
        stmt = insert(TaskLink).values(**link_data)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_task_links_task_entity"
        )
        
        await self._session.execute(stmt)
        await self._session.commit()
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return link_data["id"]

    async def create_links_batch(
        self,
        links: List[Dict[str, Any]],
    ) -> int:
        """Create multiple task links with idempotency.
        
        Args:
            links: List of link dicts with task_id, entity_type, entity_id, link_reason
            
        Returns:
            Number of links created
        """
        count = 0
        for link in links:
            if "id" not in link:
                link["id"] = generate_objectid()
            if "created_at" not in link:
                link["created_at"] = datetime.utcnow()
            
            # Remove sl_no - it's GENERATED ALWAYS
            if "sl_no" in link:
                del link["sl_no"]
            
            stmt = insert(TaskLink).values(**link)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_task_links_task_entity"
            )
            
            result = await self._session.execute(stmt)
            count += result.rowcount
        
        await self._session.commit()
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return count

    async def get_links_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all links for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of link dicts
        """
        stmt = select(TaskLink).where(TaskLink.task_id == task_id)
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs
