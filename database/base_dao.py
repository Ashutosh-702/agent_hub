from typing import Any, Dict, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


class BaseMongoDao:

    def __init__(self, mongo_client: AsyncIOMotorClient, collection_name: str, database_name: str = "linkedin_sdr"):
        self.mongo_client = mongo_client
        self.collection = mongo_client[database_name][collection_name]

    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a single document into the collection."""
        result = await self.collection.insert_one(document)
        return result.inserted_id

    async def insert_many(self, documents: List[Dict[str, Any]], ordered: bool = False) -> List[Any]:
        """Insert multiple documents into the collection."""
        result = await self.collection.insert_many(documents, ordered=ordered)
        return result.inserted_ids

    async def find_one(self, query: Dict[str, Any], projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        document = await self.collection.find_one(filter=query, projection=projection)
        return document

    async def find_many(self, query: Dict[str, Any], projection: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query."""
        cursor = self.collection.find(filter=query, projection=projection)
        documents = await cursor.to_list(length=None)
        return documents

    async def update_one(self, query: Dict[str, Any], update_clause: Dict[str, Any]) -> int:
        """Update a single document matching the query."""
        result = await self.collection.update_one(query, update_clause)
        return result.modified_count

    async def find_one_and_update(self, query: Dict[str, Any], update_clause: Dict[str, Any],
                                  projection: Dict[str, Any] = None, return_modified: bool = True) -> int:
        """Update a single document matching the query."""
        result = await self.collection.find_one_and_update(
            filter=query,
            update=update_clause,
            projection=projection,
            return_document=return_modified
        )
        return result

    async def update_many(self, query: Dict[str, Any], update_clause: Dict[str, Any]) -> int:
        """Update multiple documents matching the query."""
        result = await self.collection.update_many(query, update_clause)
        return result.modified_count

    async def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete a single document matching the query."""
        result = await self.collection.delete_one(query)
        return result.deleted_count

    async def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching the query."""
        result = await self.collection.delete_many(query)
        return result.deleted_count

    async def get_paginated_response(self, filter_query, projection=None, page_size=10, page_number=1,
                                     sort_by=None):
        """
        Returns a paginated response for the given MongoDB query.

        :param filter_query: The filter query to apply.
        :param projection: The fields to include or exclude in the result.
        :param page_size: Number of documents per page.
        :param page_number: The page number to retrieve.
        :param sort_by: Sorting criteria for the query.
        :return: A tuple of (result, pagination_info).
        """
        result = []
        pagination_info = {
            "page_size": page_size,
            "page_number": page_number,
            "has_next": False,
            "total_records": 0
        }

        try:
            # Count total records
            total_records = await self.collection.count_documents(filter_query)
            pagination_info["total_records"] = total_records

            # Determine if there is a next page
            pagination_info["has_next"] = total_records - page_size * page_number > 0

            cursor = self.collection.find(filter_query, projection)
            if sort_by:
                cursor = cursor.sort(sort_by)
            # Apply pagination
            if page_size != -1:
                cursor = cursor.skip(page_size * (page_number - 1)).limit(page_size)

            # Fetch results
            result = await cursor.to_list(length=page_size)

        except Exception as e:
            print(f"An error occurred: {e}")

        return result, pagination_info

    async def start_session(self):
        return await self.mongo_client.start_session()

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
                    processed_query[field] = self._validate_and_convert_objectid(processed_query[field], field)
                elif isinstance(processed_query[field], dict) and '$in' in processed_query[field]:
                    # Handle arrays of IDs
                    valid_items = []
                    in_operator_values = processed_query[field]['$in']

                    for position, object_id_string in enumerate(in_operator_values):
                        if object_id_string is not None:
                            field_name = f"{field}[{position}]"
                            converted_item = self._validate_and_convert_objectid(object_id_string, field_name)
                            valid_items.append(converted_item)

                    processed_query[field]['$in'] = valid_items

        return processed_query

    def _validate_and_convert_objectid(self, value: Union[str, ObjectId], field_name: str = "id") -> ObjectId:

        if isinstance(value, ObjectId):
            return value

        if not value.strip():
            raise Exception(
                f"{field_name} cannot be empty", status_code=400)

        return ObjectId(value)
        