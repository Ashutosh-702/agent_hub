"""PostgreSQL Meetings DAO."""

from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import Meeting


class PostgresMeetingsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for meetings table."""
    
    model = Meeting
    
    COLUMN_MAP = {
        "_id": "id",
        "meeting_id": "meeting_id",
        "company_id": "company_id",
        "meeting_name": "meeting_name",
        "call_type": "call_type",
        "status": "status",
        "notes": "notes",
        "company_domain": "company_domain",
        "is_deleted": "is_deleted",
        "scheduled_at": "scheduled_at",
        "started_at": "started_at",
        "ended_at": "ended_at",
        "deleted_at": "deleted_at",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "summary": "summary",
    }
    
    JSONB_FIELDS = {
        "contact_ids": "contact_ids",
        "product_ids": "product_ids",
        "transcript": "transcript",
        "live_insights": "live_insights",
        "action_items": "action_items",
        "next_steps": "next_steps",
        "key_discussion_points": "key_discussion_points",
        "objections_resolutions": "objections_resolutions",
        "products_discussed": "products_discussed",
        "battlecard": "battlecard",
        "reflections": "reflections",
    }
    
    ARRAY_FIELDS = [
        "contact_ids", 
        "product_ids", 
        "transcript", 
        "live_insights", 
        "action_items", 
        "next_steps", 
        "key_discussion_points", 
        "objections_resolutions"
    ]
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_meeting(self, meeting: dict) -> str:
        """Create a new meeting.
        
        Args:
            meeting: Meeting document
            
        Returns:
            Inserted document ID
        """
        meeting["created_at"] = datetime.utcnow()
        meeting["updated_at"] = datetime.utcnow()
        inserted_id = await self.insert_one(meeting)
        return str(inserted_id)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get a meeting by its ObjectId.
        
        Args:
            meeting_id: Meeting ObjectId
            
        Returns:
            Meeting document or None
        """
        return await self.find_one({"_id": meeting_id})
    
    async def get_meeting_by_uuid(self, meeting_uuid: str) -> Optional[Dict[str, Any]]:
        """Get a meeting by its UUID.
        
        Args:
            meeting_uuid: Meeting UUID
            
        Returns:
            Meeting document or None
        """
        return await self.find_one({"meeting_id": meeting_uuid})
    
    async def get_meetings(self, filters: dict = None) -> List[Dict[str, Any]]:
        """Get all meetings matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            List of meeting documents
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_meetings_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all meetings for a company.
        
        Args:
            company_id: Company ID
            
        Returns:
            List of meeting documents
        """
        return await self.find_many({"company_id": company_id})
    
    async def get_meetings_by_contact(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get all meetings involving a contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            List of meeting documents
        """
        # This requires JSONB array containment query
        return await self.find_many({"contact_ids": {"$in": [contact_id]}})
    
    async def get_meetings_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all meetings with a specific status.
        
        Args:
            status: Meeting status
            
        Returns:
            List of meeting documents
        """
        return await self.find_many({"status": status})
    
    async def get_completed_meetings(self) -> List[Dict[str, Any]]:
        """Get all completed meetings.
        
        Returns:
            List of completed meeting documents
        """
        return await self.find_many({"status": "completed"})
    
    async def update_meeting(self, meeting_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a meeting.
        
        Args:
            meeting_id: Meeting ObjectId
            update_data: Fields to update
            
        Returns:
            True if updated
        """
        update_data["updated_at"] = datetime.utcnow()
        has_operators = any(key.startswith('$') for key in update_data.keys())
        if not has_operators:
            update_data = {"$set": update_data}
        modified_count = await self.update_one({"_id": meeting_id}, update_data)
        return modified_count > 0
    
    async def update_meeting_status(self, meeting_id: str, status: str) -> bool:
        """Update meeting status.
        
        Args:
            meeting_id: Meeting ObjectId
            status: New status
            
        Returns:
            True if updated
        """
        return await self.update_meeting(meeting_id, {"status": status})
    
    async def append_transcript(self, meeting_id: str, transcript_entry: Dict[str, Any]) -> bool:
        """Append a transcript entry.
        
        Args:
            meeting_id: Meeting ObjectId
            transcript_entry: Transcript entry to append
            
        Returns:
            True if updated
        """
        result = await self.update_one(
            {"_id": meeting_id},
            {
                "$push": {"transcript": transcript_entry},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result > 0
    
    async def append_insight(self, meeting_id: str, insight: Dict[str, Any]) -> bool:
        """Append a live insight.
        
        Args:
            meeting_id: Meeting ObjectId
            insight: Insight to append
            
        Returns:
            True if updated
        """
        result = await self.update_one(
            {"_id": meeting_id},
            {
                "$push": {"live_insights": insight},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result > 0
    
    async def update_insight(self, meeting_id: str, insight_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a specific insight.
        
        Note: This is more complex with JSONB and may need special handling.
        
        Args:
            meeting_id: Meeting ObjectId
            insight_id: Insight ID
            update_data: Fields to update
            
        Returns:
            True if updated
        """
        # For JSONB arrays, we need to fetch, modify, and save
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return False
        
        insights = meeting.get("live_insights", [])
        updated = False
        for insight in insights:
            if insight.get("id") == insight_id:
                insight.update(update_data)
                updated = True
                break
        
        if updated:
            return await self.update_meeting(meeting_id, {"live_insights": insights})
        return False
    
    async def set_battlecard(self, meeting_id: str, battlecard: Dict[str, Any]) -> bool:
        """Set the battlecard.
        
        Args:
            meeting_id: Meeting ObjectId
            battlecard: Battlecard data
            
        Returns:
            True if updated
        """
        return await self.update_meeting(meeting_id, {"battlecard": battlecard})
    
    async def set_ai_reflections(self, meeting_id: str, ai_reflections: Dict[str, Any]) -> bool:
        """Set AI-generated reflections.
        
        Args:
            meeting_id: Meeting ObjectId
            ai_reflections: AI reflections data
            
        Returns:
            True if updated
        """
        meeting = await self.get_meeting(meeting_id)
        reflections = meeting.get("reflections", {}) if meeting else {}
        reflections["ai_generated"] = ai_reflections
        return await self.update_meeting(meeting_id, {"reflections": reflections})
    
    async def set_manual_reflections(self, meeting_id: str, manual_reflections: Dict[str, Any]) -> bool:
        """Set manual reflections.
        
        Args:
            meeting_id: Meeting ObjectId
            manual_reflections: Manual reflections data
            
        Returns:
            True if updated
        """
        manual_reflections["updated_at"] = datetime.utcnow()
        meeting = await self.get_meeting(meeting_id)
        reflections = meeting.get("reflections", {}) if meeting else {}
        reflections["manual"] = manual_reflections
        return await self.update_meeting(meeting_id, {"reflections": reflections})
    
    async def set_summary(self, meeting_id: str, summary: str, 
                         key_discussion_points: List[str] = None) -> bool:
        """Set meeting summary.
        
        Args:
            meeting_id: Meeting ObjectId
            summary: Summary text
            key_discussion_points: List of key points
            
        Returns:
            True if updated
        """
        update_data = {"summary": summary}
        if key_discussion_points:
            update_data["key_discussion_points"] = key_discussion_points
        return await self.update_meeting(meeting_id, update_data)
    
    async def set_action_items(self, meeting_id: str, action_items: List[Dict[str, Any]]) -> bool:
        """Set action items.
        
        Args:
            meeting_id: Meeting ObjectId
            action_items: List of action items
            
        Returns:
            True if updated
        """
        return await self.update_meeting(meeting_id, {"action_items": action_items})
    
    async def set_next_steps(self, meeting_id: str, next_steps: List[str]) -> bool:
        """Set next steps.
        
        Args:
            meeting_id: Meeting ObjectId
            next_steps: List of next steps
            
        Returns:
            True if updated
        """
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
        """Finalize a meeting with all post-call data.
        
        Args:
            meeting_id: Meeting ObjectId
            ended_at: End timestamp
            summary: Meeting summary
            key_discussion_points: Key points discussed
            action_items: List of action items
            next_steps: List of next steps
            objections_resolutions: Objections and resolutions
            products_discussed: Products mentioned
            
        Returns:
            True if updated
        """
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
        """Get previous meetings for context.
        
        Args:
            company_id: Company ID filter
            contact_ids: Contact IDs filter
            product_ids: Product IDs filter
            exclude_meeting_id: Meeting ID to exclude
            
        Returns:
            List of meeting documents
        """
        query = {"status": "completed"}
        
        if company_id:
            query["company_id"] = company_id
        
        if contact_ids:
            query["contact_ids"] = {"$in": contact_ids}
        
        if product_ids:
            query["product_ids"] = {"$in": product_ids}
        
        if exclude_meeting_id:
            query["_id"] = {"$ne": exclude_meeting_id}
        
        return await self.find_many(query)
    
    async def get_meetings_paginated(self, query: dict = None, page: int = 1,
                                     limit: int = 20) -> tuple:
        """Get paginated meetings.
        
        Args:
            query: Query filters
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (results, pagination_info)
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.get_paginated_response(query, page_size=limit, page_number=page)
    
    async def delete_meeting(self, meeting_id: str) -> bool:
        """Soft delete a meeting.
        
        Args:
            meeting_id: Meeting ObjectId
            
        Returns:
            True if updated
        """
        return await self.update_meeting(meeting_id, {
            "is_deleted": True, 
            "deleted_at": datetime.utcnow()
        })


