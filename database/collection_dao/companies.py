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

    async def get_company_by_domain(self, domain: str):
        """Get a company by its domain (checks identifiers.source_domain first, then primary_domain)."""
        # Try to find by identifiers.source_domain (new format)
        company = await self.find_one({"identifiers.source_domain": domain})
        if company:
            return company
        
        # Try to find by primary_domain field (legacy format)
        company = await self.find_one({"primary_domain": domain})
        if company:
            return company
        
        # Also try website_url containing the domain
        company = await self.find_one({"website_url": {"$regex": domain, "$options": "i"}})
        return company
    
    async def get_company_by_source_domain(self, source_domain: str):
        """Get a company by identifiers.source_domain field."""
        return await self.find_one({"identifiers.source_domain": source_domain})

    async def get_company_by_filters(self, filters: dict = None):
        if filters is None:
            filters = {}

        filters = self._process_query_objectids(filters)
        return await self.find_one(filters)
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]):
        has_operators = any(key.startswith('$') for key in update_data.keys())
        if not has_operators:
            update_data = {"$set": update_data}
            
        return await self.update_one({"_id": ObjectId(company_id)}, update_data)
    
    async def get_companies_paginated(self, query: dict = None, page: int = 1, limit: int = 100):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)
        response, pagination_info = await self.get_paginated_response(query, page_size=limit, page_number=page)
        return response, pagination_info