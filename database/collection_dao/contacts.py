from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any


class ContactsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "contacts")

    async def create_contact(self, contact: dict):
        return await self.insert_one(contact)
    
    async def create_contacts(self, contacts: List[Dict[str, Any]]):
        return await self.insert_many(contacts)
    
    async def get_contacts(self, filters: dict = {}):
        return await self.find_many(filters)
    
    async def get_contact(self, contact_id: str):
        return await self.find_one({"_id": contact_id})
    

