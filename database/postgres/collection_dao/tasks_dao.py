"""PostgreSQL Tasks DAO."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.postgres.base_dao import BasePostgresDao, generate_objectid
from database.postgres.models import Task, TaskLink


class PostgresTasksDao(BasePostgresDao):
    """PostgreSQL Data Access Object for tasks table."""
    
    model = Task
    
    COLUMN_MAP = {
        "_id": "id",
        "primary_entity_type": "primary_entity_type",
        "primary_entity_id": "primary_entity_id",
        "type": "type",
        "status": "status",
        "priority": "priority",
        "due_at": "due_at",
        "snoozed_until": "snoozed_until",
        "completed_at": "completed_at",
        "assigned_to_user_id": "assigned_to_user_id",
        "owner_user_id": "owner_user_id",
        "created_by_user_id": "created_by_user_id",
        "title": "title",
        "description": "description",
        "source": "source",
        "source_ref": "source_ref",
        "idempotency_key": "idempotency_key",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "context_json": "context_json",
        "context": "context_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_task_idempotent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task with idempotency check.
        
        Checks for existing task by idempotency_key first, then inserts if not found.
        
        Args:
            task_data: Task data including idempotency_key (uses _id for MongoDB compatibility)
            
        Returns:
            The created or existing task
        """
        idempotency_key = task_data.get("idempotency_key")
        
        # Check for existing task if idempotency_key is provided
        if idempotency_key:
            existing = await self.find_one({"idempotency_key": idempotency_key})
            if existing:
                return existing
        
        # Convert id to _id for MongoDB compatibility with BasePostgresDao
        if "id" in task_data and "_id" not in task_data:
            task_data["_id"] = task_data["id"]
        elif "_id" in task_data and "id" not in task_data:
            task_data["id"] = task_data["_id"]
        elif "id" not in task_data and "_id" not in task_data:
            task_id = generate_objectid()
            task_data["id"] = task_id
            task_data["_id"] = task_id
        
        # Use BasePostgresDao's insert_one which handles all field mapping
        task_id = await self.insert_one(task_data)
        
        # Fetch and return the newly created task
        created = await self.find_one({"_id": task_id})
        return created

    async def list_tasks_inbox(
        self,
        statuses: Optional[List[str]] = None,
        assigned_to_user_id: Optional[str] = None,
        types: Optional[List[str]] = None,
        overdue: Optional[bool] = None,
        sl_no_lt: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List tasks for inbox view with filters and keyset pagination.
        
        Args:
            statuses: Filter by status(es)
            assigned_to_user_id: Filter by assignee
            types: Filter by task type(s)
            overdue: Filter overdue tasks (True/False/None)
            sl_no_lt: Keyset pagination cursor
            limit: Max results
            
        Returns:
            List of tasks ordered by sl_no DESC
        """
        conditions = []
        
        if statuses:
            conditions.append(Task.status.in_(statuses))
        
        if assigned_to_user_id:
            conditions.append(Task.assigned_to_user_id == assigned_to_user_id)
        
        if types:
            conditions.append(Task.type.in_(types))
        
        if sl_no_lt is not None:
            conditions.append(Task.sl_no < sl_no_lt)
        
        # Overdue filter - compute effective_due_at
        if overdue is True:
            now = datetime.utcnow()
            # Task is overdue if: status in (open, in_progress) AND effective_due_at < now
            # effective_due_at = CASE WHEN snoozed_until > now THEN snoozed_until ELSE due_at END
            conditions.append(Task.status.in_(["open", "in_progress"]))
            conditions.append(
                or_(
                    and_(Task.snoozed_until.isnot(None), Task.snoozed_until <= now, Task.due_at < now),
                    and_(Task.snoozed_until.is_(None), Task.due_at.isnot(None), Task.due_at < now),
                    and_(Task.snoozed_until.isnot(None), Task.snoozed_until > now, Task.snoozed_until < now)  # This is always false, just placeholder
                )
            )
        
        stmt = select(Task)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Task.sl_no.desc()).limit(limit)
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs

    async def list_tasks_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        statuses: Optional[List[str]] = None,
        assigned_to_user_id: Optional[str] = None,
        types: Optional[List[str]] = None,
        sl_no_lt: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List tasks linked to an entity with filters and keyset pagination.
        
        Uses JOIN on task_links to find all tasks associated with an entity.
        
        Args:
            entity_type: Entity type (contact|company|deal)
            entity_id: Entity ID
            statuses: Filter by status(es)
            assigned_to_user_id: Filter by assignee
            types: Filter by task type(s)
            sl_no_lt: Keyset pagination cursor
            limit: Max results
            
        Returns:
            List of tasks ordered by sl_no DESC
        """
        conditions = [
            TaskLink.entity_type == entity_type,
            TaskLink.entity_id == entity_id,
        ]
        
        if statuses:
            conditions.append(Task.status.in_(statuses))
        
        if assigned_to_user_id:
            conditions.append(Task.assigned_to_user_id == assigned_to_user_id)
        
        if types:
            conditions.append(Task.type.in_(types))
        
        if sl_no_lt is not None:
            conditions.append(Task.sl_no < sl_no_lt)
        
        stmt = (
            select(Task)
            .join(TaskLink, TaskLink.task_id == Task.id)
            .where(and_(*conditions))
            .order_by(Task.sl_no.desc())
            .limit(limit)
        )
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task document or None
        """
        return await self.find_one({"_id": task_id})

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> int:
        """Update a task.
        
        Args:
            task_id: Task ID
            updates: Fields to update
            
        Returns:
            Number of modified documents
        """
        return await self.update_one({"_id": task_id}, {"$set": updates})
