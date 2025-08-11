from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any


class CompaniesDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "companies")

    async def create_company(self, company: dict):
        return await self.insert_one(company)
    
    async def create_companies(self, companies: List[Dict[str, Any]]):
        return await self.insert_many(companies)
    
    async def get_companies(self, filters: dict = {}):
        return await self.find_many(filters)
    
    async def get_company(self, company_id: str):
        return await self.find_one({"_id": company_id})
    

