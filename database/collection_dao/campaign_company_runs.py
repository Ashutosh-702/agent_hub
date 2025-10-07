from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, Union
from global_utils.exceptions import ApiException
from bson import ObjectId

class CampaignCompanyRunsDao(BaseMongoDao):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "campaign_company_runs")

    async def create_campaign_company_run(self, campaign_company_run: dict):
        return await self.insert_one(campaign_company_run)
    
    async def get_campaign_company_runs(self, query: dict = None):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)
        return await self.find_many(query)
    
    async def get_campaign_company_run(self, campaign_company_run_id: str):
        return await self.find_one({"_id": campaign_company_run_id})
    
    async def update_campaign_company_run(self, query: Dict[str, Any], update_clause: Dict[str, Any]):
        return await self.update_one(query, update_clause)

    async def get_campaign_company_runs_paginated(self, query: dict = None, page: int = 1, limit: int = 100):
        if query is None:
            query = {}

        query = self._process_query_objectids(query)
        return await self.get_paginated_response(query, page_size=limit, page_number=page)

    async def get_campaign_company_runs_count(self, query: dict = None):
        if query is None:
            query = {}

        return await self.collection.count_documents(query)

    def _process_query_objectids(self, query: Dict = None) -> Dict[str, Any]:

        if query is None:
            return {}
        
        processed_query = query.copy()
        objectid_fields = [
            "_id", "campaign_id", "company_id", "contact_id"
        ]
        
        for field in objectid_fields:
            if field in processed_query and processed_query[field] is not None:
                if isinstance(processed_query[field], str):
                    processed_query[field] = self._validate_and_convert_objectid(
                        processed_query[field], field
                    )
                elif isinstance(processed_query[field], list):
                    # Handle arrays of IDs
                    processed_query[field] = [
                        self._validate_and_convert_objectid(item, f"{field}[{i}]")
                        for i, item in enumerate(processed_query[field])
                        if item is not None
                    ]
        
        return processed_query

    def _validate_and_convert_objectid(self, value: Union[str, ObjectId], field_name: str = "id") -> ObjectId:

        if isinstance(value, ObjectId):
            return value
            
        if not value.strip():
            raise ApiException(f"{field_name} cannot be empty", status_code=400)
            
        return ObjectId(value)
