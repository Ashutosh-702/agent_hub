from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

class CampaignContactRunsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaign_contact_runs")

    async def create_campaign_contact_run(self, campaign_contact_run: dict):
        campaign_contact_run = self._process_query_objectids(campaign_contact_run)
        return await self.insert_one(campaign_contact_run)
    
    async def get_campaign_contact_runs(self, query: dict = None):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)
        return await self.find_many(query)
    
    async def get_campaign_contact_run(self, campaign_contact_run_id: str):
        return await self.find_one({"_id": campaign_contact_run_id})
    
    async def update_campaign_contact_run(self, query: Dict[str, Any]=None, update_clause: Dict[str, Any]=None):
        if query is None:
            query = {}
        if update_clause is None:
            update_clause = {}
        query = self._process_query_objectids(query)
        update_clause = self._process_query_objectids(update_clause)
        return await self.update_one(query, update_clause)

    async def update_campaign_contact_runs(self, query: Dict[str, Any]=None, update_clause: Dict[str, Any]=None):
        if query is None:
            query = {}
        if update_clause is None:
            update_clause = {}
        query = self._process_query_objectids(query)
        return await self.update_many(query, update_clause)

    async def get_campaign_contact_runs_count(self, query: dict = None):
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.count_documents(query)
    
    async def get_campaign_contact_runs_paginated(
        self, query: dict = None, 
        page: int = 1, limit: int = 100, 
        sort_by: list = None, 
        projection: dict = None
    ):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)

        if sort_by is None:
            sort_by = []

        if projection is None:
            projection = {}

        return await self.get_paginated_response(
            query, page_size=limit,
            page_number=page, sort_by=sort_by, 
            projection=projection
        )

    async def get_exportable_contacts_count(self, campaign_id: str) -> int:
        """Get total count of contacts eligible for export (is_relevant=True, enrichment_status=True)"""
        query = {
            "campaign_id": campaign_id,
            "is_relevant": True,
            "enrichment_status": True
        }
        query = self._process_query_objectids(query)
        return await self.count_documents(query)

    async def get_exportable_contact_ids(
        self, 
        campaign_id: str, 
        page: int = 1, 
        limit: int = 500
    ) -> list:
        """Get contact runs for export with pagination (is_relevant=True, enrichment_status=True)"""
        query = {
            "campaign_id": campaign_id,
            "is_relevant": True,
            "enrichment_status": True
        }
        query = self._process_query_objectids(query)
        
        skip = (page - 1) * limit
        
        # Fetch with pagination
        cursor = self.collection.find(query).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        
        return results
