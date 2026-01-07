from bson.objectid import ObjectId
from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient


class CampaignsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaigns")

    async def create_campaign(self, campaign: dict):
        return await self.insert_one(campaign)
    
    async def get_campaigns(self, filters: dict = None):
        if filters is None:
            filters = {}

        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_campaign(self, campaign_id: str):
        return await self.find_one({"_id": ObjectId(campaign_id)})

    async def update_campaign(self, campaign_id: str, update_data: dict):
        return await self.update_one({"_id": ObjectId(campaign_id)}, {"$set": update_data})
    
    async def update_campaign_status(self, campaign_id: str, status: str):
        return await self.update_one({"_id": ObjectId(campaign_id)}, {"$set": {"lifecycle":{"status": status}}})

    async def get_campaign_by_status(self, status: str):
        return await self.find_one({"lifecycle.status": status})

    async def get_campaigns_paginated(self, query: dict = None, page: int = 1, limit: int = 10):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)
        response, pagination_info = await self.get_paginated_response(query, page_size=limit, page_number=page)
        return response, pagination_info

    async def check_campaign_name_exists(self, campaign_name: str, exclude_campaign_id: str = None) -> bool:
        """Check if a campaign with the given name already exists.
        
        Args:
            campaign_name: The campaign name to check
            exclude_campaign_id: Optional campaign ID to exclude from check (for updates)
            
        Returns:
            True if campaign name exists, False otherwise
        """
        query = {"name": campaign_name}
        if exclude_campaign_id:
            query["_id"] = {"$ne": ObjectId(exclude_campaign_id)}
        
        existing = await self.find_one(query)
        return existing is not None
    
    async def get_campaign_by_name(self, campaign_name: str):
        """Get a campaign by its name."""
        return await self.find_one({"name": campaign_name})
