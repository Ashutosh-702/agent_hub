"""PostgreSQL Deals DAO."""

from typing import List, Dict, Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import Deal


class PostgresDealsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for deals table."""
    
    model = Deal
    
    COLUMN_MAP = {
        "_id": "id",
        "company_id": "company_id",
        "owner_user_id": "owner_user_id",
        "name": "name",
        "stage": "stage",
        "amount": "amount",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "metadata": "metadata_json",
        "metadata_json": "metadata_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID.
        
        Args:
            deal_id: Deal ID
            
        Returns:
            Deal document or None
        """
        return await self.find_one({"_id": deal_id})

    async def search_deals(
        self,
        query: Optional[str] = None,
        company_id: Optional[str] = None,
        stage: Optional[str] = None,
        sl_no_lt: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search deals with filters and keyset pagination.
        
        Args:
            query: Search query for name
            company_id: Filter by company
            stage: Filter by stage
            sl_no_lt: Keyset pagination cursor
            limit: Max results
            
        Returns:
            List of deals ordered by sl_no DESC
        """
        conditions = []
        
        if query:
            conditions.append(Deal.name.ilike(f"%{query}%"))
        
        if company_id:
            conditions.append(Deal.company_id == company_id)
        
        if stage:
            conditions.append(Deal.stage == stage)
        
        if sl_no_lt is not None:
            conditions.append(Deal.sl_no < sl_no_lt)
        
        stmt = select(Deal)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Deal.sl_no.desc()).limit(limit)
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs
