from bson.objectid import ObjectId
from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient


class CampaignsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaigns")

    async def create_campaign(self, campaign: dict):
        return await self.insert_one(campaign)
    
    async def get_campaigns(self, filters: dict = {}):
        return await self.find_many(filters)
    
    async def get_campaign(self, campaign_id: str):
        return await self.find_one({"_id": ObjectId(campaign_id)})
    
    async def update_campaign_status(self, campaign_id: str, status: str):
        return await self.update_one({"_id": ObjectId(campaign_id)}, {"$set": {"lifecycle":{"status": status}}})

    async def get_campaign_by_status(self, status: str):
        return await self.find_one({"lifecycle.status": status})


