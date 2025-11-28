from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
from bson import ObjectId


class CompaniesDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "companies")

    async def create_company(self, company: dict):
        return await self.insert_one(company)
    
    async def create_companies(self, companies: List[Dict[str, Any]]):
        return await self.insert_many(companies)
    
    async def get_companies(self, filters: dict = {}):
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_company(self, company_id: str):
        return await self.find_one({"_id": ObjectId(company_id)})

    async def get_company_by_filters(self, filters: dict = None):
        if filters is None:
            filters = {}

        filters = self._process_query_objectids(filters)
        return await self.find_one(filters)
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]):
        return await self.update_one({"_id": ObjectId(company_id)}, update_data)