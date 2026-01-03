from database.base_dao import BaseMongoDao
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, Optional
from bson import ObjectId
from datetime import datetime


class MeetingsDao(BaseMongoDao):
    """Data Access Object for meetings collection."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "meetings")

    async def create_meeting(self, meeting: dict) -> str:
        """Create a new meeting record."""
        meeting["created_at"] = datetime.utcnow()
        meeting["updated_at"] = datetime.utcnow()
        # insert_one already returns the inserted_id (ObjectId), not the InsertOneResult
        inserted_id = await self.insert_one(meeting)
        return str(inserted_id)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get a meeting by its ID."""
        return await self.find_one({"_id": ObjectId(meeting_id)})
    
    async def get_meeting_by_uuid(self, meeting_uuid: str) -> Optional[Dict[str, Any]]:
        """Get a meeting by its UUID."""
        return await self.find_one({"meeting_id": meeting_uuid})
    
    async def get_meetings(self, filters: dict = None) -> List[Dict[str, Any]]:
        """Get all meetings matching filters."""
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_meetings_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all meetings for a specific company."""
        return await self.find_many({"company_id": ObjectId(company_id)})
    
    async def get_meetings_by_contact(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get all meetings involving a specific contact."""
        return await self.find_many({"contact_ids": ObjectId(contact_id)})
    
    async def get_meetings_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all meetings with a specific status."""
        return await self.find_many({"status": status})
    
    async def get_completed_meetings(self) -> List[Dict[str, Any]]:
        """Get all completed meetings (for reflections history)."""
        return await self.find_many({"status": "completed"})
    
    async def update_meeting(self, meeting_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a meeting record."""
        update_data["updated_at"] = datetime.utcnow()
        has_operators = any(key.startswith('$') for key in update_data.keys())
        if not has_operators:
            update_data = {"$set": update_data}
        # update_one already returns modified_count (int), not UpdateResult
        modified_count = await self.update_one({"_id": ObjectId(meeting_id)}, update_data)
        return modified_count > 0
    
    async def update_meeting_status(self, meeting_id: str, status: str) -> bool:
        """Update meeting status."""
        return await self.update_meeting(meeting_id, {"status": status})
    
    async def append_transcript(self, meeting_id: str, transcript_entry: Dict[str, Any]) -> bool:
        """Append a transcript entry to the meeting."""
        result = await self.update_one(
            {"_id": ObjectId(meeting_id)},
            {
                "$push": {"transcript": transcript_entry},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def append_insight(self, meeting_id: str, insight: Dict[str, Any]) -> bool:
        """Append a live insight to the meeting."""
        result = await self.update_one(
            {"_id": ObjectId(meeting_id)},
            {
                "$push": {"live_insights": insight},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def update_insight(self, meeting_id: str, insight_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a specific insight in the meeting."""
        result = await self.update_one(
            {"_id": ObjectId(meeting_id), "live_insights.id": insight_id},
            {
                "$set": {f"live_insights.$.{key}": value for key, value in update_data.items()},
                "updated_at": datetime.utcnow()
            }
        )
        return result.modified_count > 0
    
    async def set_battlecard(self, meeting_id: str, battlecard: Dict[str, Any]) -> bool:
        """Set or update the battlecard for a meeting."""
        return await self.update_meeting(meeting_id, {"battlecard": battlecard})
    
    async def set_ai_reflections(self, meeting_id: str, ai_reflections: Dict[str, Any]) -> bool:
        """Set or update AI-generated reflections."""
        return await self.update_meeting(meeting_id, {"reflections.ai_generated": ai_reflections})
    
    async def set_manual_reflections(self, meeting_id: str, manual_reflections: Dict[str, Any]) -> bool:
        """Set or update manual reflections."""
        manual_reflections["updated_at"] = datetime.utcnow()
        return await self.update_meeting(meeting_id, {"reflections.manual": manual_reflections})
    
    async def set_summary(self, meeting_id: str, summary: str, key_discussion_points: List[str] = None) -> bool:
        """Set meeting summary and key discussion points."""
        update_data = {"summary": summary}
        if key_discussion_points:
            update_data["key_discussion_points"] = key_discussion_points
        return await self.update_meeting(meeting_id, update_data)
    
    async def set_action_items(self, meeting_id: str, action_items: List[Dict[str, Any]]) -> bool:
        """Set action items for the meeting."""
        return await self.update_meeting(meeting_id, {"action_items": action_items})
    
    async def set_next_steps(self, meeting_id: str, next_steps: List[str]) -> bool:
        """Set next steps for the meeting."""
        return await self.update_meeting(meeting_id, {"next_steps": next_steps})
    
    async def finalize_meeting(
        self,
        meeting_id: str,
        ended_at: datetime,
        summary: str,
        key_discussion_points: List[str],
        action_items: List[Dict[str, Any]],
        next_steps: List[str],
        objections_resolutions: List[Dict[str, Any]] = None,
        products_discussed: List[str] = None
    ) -> bool:
        """Finalize a meeting with all post-call data."""
        update_data = {
            "status": "completed",
            "ended_at": ended_at,
            "summary": summary,
            "key_discussion_points": key_discussion_points,
            "action_items": action_items,
            "next_steps": next_steps
        }
        if objections_resolutions:
            update_data["objections_resolutions"] = objections_resolutions
        if products_discussed:
            update_data["products_discussed"] = products_discussed
        return await self.update_meeting(meeting_id, update_data)
    
    async def get_previous_meetings(
        self,
        company_id: str = None,
        contact_ids: List[str] = None,
        product_ids: List[str] = None,
        exclude_meeting_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get previous meetings for context building."""
        query = {"status": "completed"}
        
        if company_id:
            query["company_id"] = ObjectId(company_id)
        
        if contact_ids:
            query["contact_ids"] = {"$in": [ObjectId(cid) for cid in contact_ids]}
        
        if product_ids:
            query["product_ids"] = {"$in": product_ids}
        
        if exclude_meeting_id:
            query["_id"] = {"$ne": ObjectId(exclude_meeting_id)}
        
        return await self.find_many(query)
    
    async def get_meetings_paginated(
        self,
        query: dict = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple:
        """Get paginated meetings list."""
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        response, pagination_info = await self.get_paginated_response(
            query, page_size=limit, page_number=page
        )
        return response, pagination_info
    
    async def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting (soft delete by setting is_deleted flag)."""
        return await self.update_meeting(meeting_id, {"is_deleted": True, "deleted_at": datetime.utcnow()})

