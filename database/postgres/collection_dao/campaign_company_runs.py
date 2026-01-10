"""PostgreSQL Campaign Company Runs DAO."""

from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import CampaignCompanyRun


class PostgresCampaignCompanyRunsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for campaign_company_runs table."""
    
    model = CampaignCompanyRun
    
    COLUMN_MAP = {
        "_id": "id",
        "campaign_id": "campaign_id",
        "company_id": "company_id",
        "company_status": "company_status",
        "linkedin_contact_status": "linkedin_contact_status",
        "is_relevant": "is_relevant",
        "sync_to_hubspot_status": "sync_to_hubspot_status",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "metadata": "metadata_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_campaign_company_run(self, campaign_company_run: dict) -> str:
        """Create a new campaign company run.
        
        Args:
            campaign_company_run: Campaign company run document
            
        Returns:
            Inserted document ID
        """
        campaign_company_run = self._process_query_objectids(campaign_company_run)
        return await self.insert_one(campaign_company_run)

    async def get_campaign_company_runs(self, query: dict = None) -> List[Dict[str, Any]]:
        """Get campaign company runs matching query.
        
        Args:
            query: Query filters
            
        Returns:
            List of campaign company run documents
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.find_many(query)

    async def get_campaign_company_run(self, campaign_company_run_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign company run by ID.
        
        Args:
            campaign_company_run_id: Campaign company run ID
            
        Returns:
            Campaign company run document or None
        """
        return await self.find_one({"_id": campaign_company_run_id})

    async def update_campaign_company_run(self, query: Dict[str, Any] = None, 
                                          update_clause: Dict[str, Any] = None) -> int:
        """Update a campaign company run.
        
        Args:
            query: Query to find document
            update_clause: Update clause
            
        Returns:
            Number of modified documents
        """
        if query is None:
            query = {}
        if update_clause is None:
            update_clause = {}
        query = self._process_query_objectids(query)
        return await self.update_one(query, update_clause)

    async def update_campaign_company_runs(self, query: Dict[str, Any] = None,
                                           update_clause: Dict[str, Any] = None) -> int:
        """Update multiple campaign company runs.
        
        Args:
            query: Query to find documents
            update_clause: Update clause
            
        Returns:
            Number of modified documents
        """
        if query is None:
            query = {}
        if update_clause is None:
            update_clause = {}
        query = self._process_query_objectids(query)
        return await self.update_many(query, update_clause)

    async def update_campaign_company_run_by_campaign_id(self, campaign_id: str,
                                                         update_clause: Dict[str, Any]) -> int:
        """Bulk update by campaign_id.
        
        Args:
            campaign_id: Campaign ID
            update_clause: Update clause
            
        Returns:
            Number of modified documents
        """
        query = {"campaign_id": campaign_id}
        query = self._process_query_objectids(query)
        return await self.update_many(query, update_clause)

    async def get_campaign_company_runs_paginated(self, query: dict = None, page: int = 1,
                                                   limit: int = 100, projection: dict = None) -> tuple:
        """Get paginated campaign company runs.
        
        Args:
            query: Query filters
            page: Page number
            limit: Items per page
            projection: Fields to include/exclude
            
        Returns:
            Tuple of (results, pagination_info)
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.get_paginated_response(query, page_size=limit, page_number=page, projection=projection)

    async def get_campaign_company_runs_count(self, query: dict = None) -> int:
        """Count campaign company runs.
        
        Args:
            query: Query filters
            
        Returns:
            Count of matching documents
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.count_documents(query)


