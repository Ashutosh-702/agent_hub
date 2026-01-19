"""PostgreSQL TaskActivity DAO."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao, generate_objectid
from database.postgres.models import TaskActivity


class PostgresTaskActivityDao(BasePostgresDao):
    """PostgreSQL Data Access Object for task_activity table."""
    
    model = TaskActivity
    
    COLUMN_MAP = {
        "_id": "id",
        "task_id": "task_id",
        "at": "at",
        "actor_user_id": "actor_user_id",
        "event_type": "event_type",
    }
    
    JSONB_FIELDS = {
        "diff_json": "diff_json",
        "diff": "diff_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def add_activity(
        self,
        task_id: str,
        event_type: str,
        diff_json: Dict[str, Any],
        actor_user_id: Optional[str] = None,
    ) -> str:
        """Add an activity entry for a task.
        
        Args:
            task_id: Task ID
            event_type: Type of event (created, updated, status_changed, etc.)
            diff_json: JSON diff with before/after values
            actor_user_id: User who performed the action
            
        Returns:
            Activity ID
        """
        activity_data = {
            "id": generate_objectid(),
            "task_id": task_id,
            "at": datetime.utcnow(),
            "actor_user_id": actor_user_id,
            "event_type": event_type,
            "diff_json": diff_json,
        }
        
        return await self.insert_one(activity_data)

    async def list_activity(
        self,
        task_id: str,
        sl_no_lt: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List activity for a task with keyset pagination.
        
        Args:
            task_id: Task ID
            sl_no_lt: Keyset pagination cursor
            limit: Max results
            
        Returns:
            List of activity entries ordered by sl_no DESC
        """
        conditions = [TaskActivity.task_id == task_id]
        
        if sl_no_lt is not None:
            conditions.append(TaskActivity.sl_no < sl_no_lt)
        
        stmt = (
            select(TaskActivity)
            .where(and_(*conditions))
            .order_by(TaskActivity.sl_no.desc())
            .limit(limit)
        )
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs
