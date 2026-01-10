"""PostgreSQL Campaign Contact Runs DAO."""

from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import CampaignContactRun


class PostgresCampaignContactRunsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for campaign_contact_runs table."""
    
    model = CampaignContactRun
    
    COLUMN_MAP = {
        "_id": "id",
        "campaign_id": "campaign_id",
        "company_id": "company_id",
        "contact_id": "contact_id",
        "is_relevant": "is_relevant",
        "enrichment_status": "enrichment_status",
        "personalization_status": "personalization_status",
        "email_id": "email_id",
        "personalized_message": "personalized_message",
        "ai_generated_deck": "ai_generated_deck",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "metadata": "metadata_json",
        "sequence_enrollment": "sequence_enrollment",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_campaign_contact_run(self, campaign_contact_run: dict) -> str:
        """Create a new campaign contact run.
        
        Args:
            campaign_contact_run: Campaign contact run document
            
        Returns:
            Inserted document ID
        """
        campaign_contact_run = self._process_query_objectids(campaign_contact_run)
        return await self.insert_one(campaign_contact_run)
    
    async def get_campaign_contact_runs(self, query: dict = None) -> List[Dict[str, Any]]:
        """Get campaign contact runs matching query.
        
        Args:
            query: Query filters
            
        Returns:
            List of campaign contact run documents
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.find_many(query)
    
    async def get_campaign_contact_run(self, campaign_contact_run_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign contact run by ID.
        
        Args:
            campaign_contact_run_id: Campaign contact run ID
            
        Returns:
            Campaign contact run document or None
        """
        return await self.find_one({"_id": campaign_contact_run_id})
    
    async def update_campaign_contact_run(self, query: Dict[str, Any] = None,
                                          update_clause: Dict[str, Any] = None) -> int:
        """Update a campaign contact run.
        
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

    async def update_campaign_contact_runs(self, query: Dict[str, Any] = None,
                                           update_clause: Dict[str, Any] = None) -> int:
        """Update multiple campaign contact runs.
        
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

    async def get_campaign_contact_runs_count(self, query: dict = None) -> int:
        """Count campaign contact runs.
        
        Args:
            query: Query filters
            
        Returns:
            Count of matching documents
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.count_documents(query)
    
    async def get_campaign_contact_runs_paginated(self, query: dict = None, page: int = 1,
                                                   limit: int = 100, sort_by: list = None,
                                                   projection: dict = None) -> tuple:
        """Get paginated campaign contact runs.
        
        Args:
            query: Query filters
            page: Page number
            limit: Items per page
            sort_by: Sorting criteria
            projection: Fields to include/exclude
            
        Returns:
            Tuple of (results, pagination_info)
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        
        if sort_by is None:
            sort_by = []
            
        return await self.get_paginated_response(
            query, page_size=limit, page_number=page, sort_by=sort_by, projection=projection
        )


