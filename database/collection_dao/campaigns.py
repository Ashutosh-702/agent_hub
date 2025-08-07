from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient


class CampaignsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaigns")

    async def create_campaign(self, campaign: dict):
        return await self.insert_one(campaign)
    
    async def get_campaigns(self):
        return await self.find_many({})
    
    async def get_campaign(self, campaign_id: str):
        return await self.find_one({"_id": campaign_id})
    

