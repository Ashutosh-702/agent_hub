"""PostgreSQL TaskTypePolicy DAO."""

from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import TaskTypePolicy


class PostgresTaskTypePoliciesDao(BasePostgresDao):
    """PostgreSQL Data Access Object for task_type_policies table."""
    
    model = TaskTypePolicy
    
    COLUMN_MAP = {
        "type": "type",
        "default_sla_minutes": "default_sla_minutes",
        "default_priority": "default_priority",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {}
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_policy(self, task_type: str) -> Optional[Dict[str, Any]]:
        """Get policy for a task type.
        
        Args:
            task_type: Task type (e.g., 'call', 'followup_email')
            
        Returns:
            Policy dict or None
        """
        stmt = select(TaskTypePolicy).where(TaskTypePolicy.type == task_type)
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        if instance is None:
            return None
        
        return {
            "type": instance.type,
            "default_sla_minutes": instance.default_sla_minutes,
            "default_priority": instance.default_priority,
        }

    async def get_all_policies(self) -> list:
        """Get all task type policies.
        
        Returns:
            List of policy dicts
        """
        stmt = select(TaskTypePolicy)
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return [
            {
                "type": inst.type,
                "default_sla_minutes": inst.default_sla_minutes,
                "default_priority": inst.default_priority,
            }
            for inst in instances
        ]
