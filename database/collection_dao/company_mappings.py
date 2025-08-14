from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

class CompanyMappingsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "company_mappings")

    async def create_company_mapping(self, company_mapping: dict):
        return await self.insert_one(company_mapping)
    
    async def get_company_mappings(self, filter: dict = {}):
        return await self.find_many(filter)
    
    async def get_company_mapping(self, company_mapping_id: str):
        return await self.find_one({"_id": company_mapping_id})
    
    async def update_company_mapping(self, query: Dict[str, Any], update_clause: Dict[str, Any]):
        return await self.update_one(query, update_clause)
