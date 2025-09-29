from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

class CampaignCompanyRunsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaign_company_runs")

    async def create_campaign_company_run(self, campaign_company_run: dict):
        return await self.insert_one(campaign_company_run)
    
    async def get_campaign_company_runs(self, query: dict = None):
        if query is None:
            query = {}

        return await self.find_many(query)
    
    async def get_campaign_company_run(self, campaign_company_run_id: str):
        return await self.find_one({"_id": campaign_company_run_id})
    
    async def update_campaign_company_run(self, query: Dict[str, Any], update_clause: Dict[str, Any]):
        return await self.update_one(query, update_clause)

    async def get_campaign_company_runs_paginated(self, query: dict = None, page: int = 1, limit: int = 100):
        if query is None:
            query = {}
            
        return await self.get_paginated_response(query, page_size=limit, page_number=page)

    async def get_campaign_company_runs_count(self, query: dict = None):
        if query is None:
            query = {}

        return await self.collection.count_documents(query)
