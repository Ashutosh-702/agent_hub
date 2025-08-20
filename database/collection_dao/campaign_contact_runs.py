from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

class CampaignContactRunsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaign_contact_runs")

    async def create_campaign_contact_run(self, campaign_contact_run: dict):
        return await self.insert_one(campaign_contact_run)
    
    async def get_campaign_contact_runs(self, filter: dict = {}):
        return await self.find_many(filter)
    
    async def get_campaign_contact_run(self, campaign_contact_run_id: str):
        return await self.find_one({"_id": campaign_contact_run_id})
    
    async def update_campaign_contact_run(self, query: Dict[str, Any], update_clause: Dict[str, Any]):
        return await self.update_one(query, update_clause)
