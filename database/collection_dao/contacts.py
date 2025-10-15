from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
from bson import ObjectId


class ContactsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "contacts")

    async def create_contact(self, contact: dict):
        contact = self._process_query_objectids(contact)
        return await self.insert_one(contact)
    
    async def create_contacts(self, contacts: List[Dict[str, Any]]):
        return await self.insert_many(contacts)
    
    async def get_contacts(self, filters: dict = {}):
        return await self.find_many(filters)
    
    async def get_contact(self, contact_id: str, projection: dict = None):
        if projection is None:
            projection = {}

        return await self.find_one({"_id": ObjectId(contact_id)}, projection=projection)

    async def update_contact(self, contact_id: str, update_clause: dict):
        return await self.update_one({"_id": ObjectId(contact_id)}, update_clause)
    