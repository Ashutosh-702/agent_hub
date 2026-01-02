"""
Inbox Events DAO - MongoDB operations for inbox data
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from database.base_dao import BaseMongoDao
from config.logging import logger


class InboxEventsDao(BaseMongoDao):
    """DAO for inbox_events collection"""

    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "inbox_events", "linkedin_sdr")

    async def create_indexes(self):
        """Create necessary indexes for inbox_events collection"""
        try:
            await self.collection.create_index("lead_id")
            await self.collection.create_index("channel")
            await self.collection.create_index("at")
            await self.collection.create_index("lemlist_inbox_id")
            await self.collection.create_index("lemlist_message_id", unique=True, sparse=True)
            await self.collection.create_index([("lead_id", 1), ("at", -1)])
            logger.info("Created indexes for inbox_events collection")
        except Exception as e:
            logger.warning(f"Error creating indexes for inbox_events: {e}")

    async def upsert_event(self, event: Dict[str, Any]) -> str:
        """Insert or update an event based on lemlist_message_id"""
        event["updated_at"] = datetime.utcnow()
        
        if event.get("lemlist_message_id"):
            # Upsert by lemlist_message_id
            result = await self.collection.update_one(
                {"lemlist_message_id": event["lemlist_message_id"]},
                {"$set": event, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )
            if result.upserted_id:
                return str(result.upserted_id)
            return event["lemlist_message_id"]
        else:
            # Regular insert for non-Lemlist events (e.g., calls)
            if "created_at" not in event:
                event["created_at"] = datetime.utcnow()
            result = await self.insert_one(event)
            return str(result)

    async def get_events_for_lead(
        self,
        lead_id: str,
        limit: int = 50,
        skip: int = 0,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get events for a lead, sorted by date descending"""
        query = {"lead_id": lead_id}
        if channel:
            query["channel"] = channel
            
        cursor = self.collection.find(query).sort("at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_events_for_lead(self, lead_id: str) -> int:
        """Count total events for a lead"""
        return await self.collection.count_documents({"lead_id": lead_id})

    async def get_unread_count(self, lead_id: str) -> int:
        """Count unread inbound events for a lead"""
        return await self.collection.count_documents({
            "lead_id": lead_id,
            "direction": "inbound",
            "read": {"$ne": True}
        })

    async def mark_events_read(self, lead_id: str) -> int:
        """Mark all events for a lead as read"""
        result = await self.collection.update_many(
            {"lead_id": lead_id, "direction": "inbound"},
            {"$set": {"read": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count

    async def get_latest_event_for_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent event for a lead"""
        return await self.collection.find_one(
            {"lead_id": lead_id},
            sort=[("at", -1)]
        )

    async def bulk_upsert_events(self, events: List[Dict[str, Any]]) -> int:
        """Bulk upsert events"""
        if not events:
            return 0
            
        from pymongo import UpdateOne
        
        operations = []
        now = datetime.utcnow()
        
        for event in events:
            event["updated_at"] = now
            
            if event.get("lemlist_message_id"):
                operations.append(
                    UpdateOne(
                        {"lemlist_message_id": event["lemlist_message_id"]},
                        {"$set": event, "$setOnInsert": {"created_at": now}},
                        upsert=True
                    )
                )
            else:
                # For non-Lemlist events, use lead_id + at as unique key
                event["created_at"] = now
                operations.append(
                    UpdateOne(
                        {"lead_id": event["lead_id"], "at": event["at"], "channel": event["channel"]},
                        {"$set": event, "$setOnInsert": {"created_at": now}},
                        upsert=True
                    )
                )
        
        if operations:
            result = await self.collection.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count
        return 0

    async def count_events(self, query: Dict[str, Any] = None) -> int:
        """Count events matching query"""
        return await self.collection.count_documents(query or {})

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline"""
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)


class InboxLeadsDao(BaseMongoDao):
    """DAO for inbox_leads collection - aggregated lead inbox data"""

    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "inbox_leads", "linkedin_sdr")

    async def create_indexes(self):
        """Create necessary indexes for inbox_leads collection"""
        try:
            await self.collection.create_index("lead_id", unique=True)
            await self.collection.create_index("lemlist_inbox_id", sparse=True)
            await self.collection.create_index("lemlist_contact_id", sparse=True)
            await self.collection.create_index("temperature")
            await self.collection.create_index("status")
            await self.collection.create_index("in_sequence")
            await self.collection.create_index("unread_count")
            await self.collection.create_index("owner.email")
            await self.collection.create_index([("last_touch.at", -1)])
            await self.collection.create_index([("company.name", "text"), ("contact.name", "text")])
            logger.info("Created indexes for inbox_leads collection")
        except Exception as e:
            logger.warning(f"Error creating indexes for inbox_leads: {e}")

    async def upsert_lead(self, lead: Dict[str, Any]) -> str:
        """Insert or update a lead"""
        lead["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"lead_id": lead["lead_id"]},
            {"$set": lead, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        return lead["lead_id"]

    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by ID"""
        return await self.find_one({"lead_id": lead_id})

    async def get_lead_by_lemlist_inbox(self, lemlist_inbox_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by Lemlist inbox ID"""
        return await self.find_one({"lemlist_inbox_id": lemlist_inbox_id})

    async def get_lead_by_lemlist_contact(self, lemlist_contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by Lemlist contact ID"""
        return await self.find_one({"lemlist_contact_id": lemlist_contact_id})

    async def search_leads(
        self,
        query: Optional[str] = None,
        channel: Optional[str] = None,
        temperature: Optional[str] = None,
        status: Optional[str] = None,
        in_sequence: Optional[str] = None,
        stage_status: Optional[str] = None,
        owner_email: Optional[str] = None,
        sort: str = "recent",
        tab: str = "all",
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search and filter leads"""
        
        filter_query: Dict[str, Any] = {}
        
        # Text search
        if query:
            filter_query["$or"] = [
                {"company.name": {"$regex": query, "$options": "i"}},
                {"contact.name": {"$regex": query, "$options": "i"}},
                {"contact.email": {"$regex": query, "$options": "i"}}
            ]
        
        # Channel filter
        if channel:
            filter_query["channels_present"] = channel
        
        # Temperature filter
        if temperature:
            filter_query["temperature"] = temperature
        
        # Status filter
        if status:
            filter_query["status"] = status
        
        # Sequence filter
        if in_sequence == "yes":
            filter_query["in_sequence"] = True
        elif in_sequence == "no":
            filter_query["in_sequence"] = False
        
        # Stage status filter (only when in_sequence)
        if stage_status and in_sequence != "no":
            filter_query["sequence.stage_status"] = stage_status
        
        # Owner filter
        if owner_email:
            filter_query["owner.email"] = owner_email
        
        # Tab-specific filters
        if tab == "attention":
            # Needs attention: unread > 0 OR waiting_on_us OR overdue step
            filter_query["$or"] = filter_query.get("$or", []) + [
                {"unread_count": {"$gt": 0}},
                {"status": "waiting_on_us"},
                {"in_sequence": True, "next_step_at": {"$lt": datetime.utcnow()}}
            ]
        elif tab == "sequence":
            filter_query["in_sequence"] = True
        
        # Sorting
        sort_field = [("last_touch.at", -1)]  # Default: recent
        if sort == "attention":
            sort_field = [("unread_count", -1), ("last_touch.at", 1)]
        elif sort == "hot":
            # Sort by temperature (hot first), then by recency
            sort_field = [("temperature", -1), ("last_touch.at", -1)]
        
        # Count total
        total = await self.collection.count_documents(filter_query)
        
        # Fetch with pagination
        skip = (page - 1) * page_size
        cursor = self.collection.find(filter_query).sort(sort_field).skip(skip).limit(page_size)
        leads = await cursor.to_list(length=page_size)
        
        return leads, total

    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status"""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def update_lead_temperature(
        self,
        lead_id: str,
        temperature: str,
        drivers: Optional[List[str]] = None
    ) -> bool:
        """Update lead temperature and drivers"""
        update = {"temperature": temperature, "updated_at": datetime.utcnow()}
        if drivers is not None:
            update["temperature_drivers"] = drivers
            
        result = await self.update_one({"lead_id": lead_id}, {"$set": update})
        return result > 0

    async def update_unread_count(self, lead_id: str, count: int) -> bool:
        """Update unread count for a lead"""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$set": {"unread_count": count, "updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def increment_unread_count(self, lead_id: str) -> bool:
        """Increment unread count by 1"""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$inc": {"unread_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def reset_unread_count(self, lead_id: str) -> bool:
        """Reset unread count to 0"""
        return await self.update_unread_count(lead_id, 0)

    async def update_last_touch(self, lead_id: str, last_touch: Dict[str, Any]) -> bool:
        """Update last touch for a lead"""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$set": {"last_touch": last_touch, "updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def add_channel(self, lead_id: str, channel: str) -> bool:
        """Add a channel to channels_present if not already there"""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$addToSet": {"channels_present": channel}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def bulk_upsert_leads(self, leads: List[Dict[str, Any]]) -> int:
        """Bulk upsert leads"""
        if not leads:
            return 0
            
        from pymongo import UpdateOne
        
        operations = []
        now = datetime.utcnow()
        
        for lead in leads:
            lead["updated_at"] = now
            operations.append(
                UpdateOne(
                    {"lead_id": lead["lead_id"]},
                    {"$set": lead, "$setOnInsert": {"created_at": now}},
                    upsert=True
                )
            )
        
        if operations:
            result = await self.collection.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count
        return 0

    async def get_all_lead_ids(self) -> List[str]:
        """Get all lead IDs"""
        cursor = self.collection.find({}, {"lead_id": 1})
        docs = await cursor.to_list(length=None)
        return [doc["lead_id"] for doc in docs]

    async def count_leads(self, query: Dict[str, Any] = None) -> int:
        """Count leads matching query"""
        return await self.collection.count_documents(query or {})

    async def find_leads(
        self,
        query: Dict[str, Any] = None,
        limit: int = 50,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Find leads matching query"""
        cursor = self.collection.find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit)


class InboxNotesDao(BaseMongoDao):
    """DAO for inbox_notes collection"""

    def __init__(self, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client, "inbox_notes", "linkedin_sdr")

    async def create_indexes(self):
        """Create necessary indexes"""
        try:
            await self.collection.create_index("lead_id")
            await self.collection.create_index([("lead_id", 1), ("at", -1)])
            logger.info("Created indexes for inbox_notes collection")
        except Exception as e:
            logger.warning(f"Error creating indexes for inbox_notes: {e}")

    async def add_note(self, lead_id: str, author: str, text: str) -> str:
        """Add a note for a lead"""
        note = {
            "lead_id": lead_id,
            "author": author,
            "text": text,
            "at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        result = await self.insert_one(note)
        return str(result)

    async def get_notes_for_lead(self, lead_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notes for a lead, sorted by date descending"""
        cursor = self.collection.find({"lead_id": lead_id}).sort("at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        result = await self.delete_one({"_id": ObjectId(note_id)})
        return result > 0

