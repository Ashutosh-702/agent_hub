"""PostgreSQL Inbox DAOs - Events, Leads, and Notes."""

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao, generate_objectid
from database.postgres.models import InboxEvent, InboxLead, InboxNote
from config.logging import logger


class PostgresInboxEventsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for inbox_events table."""
    
    model = InboxEvent
    
    COLUMN_MAP = {
        "_id": "id",
        "lead_id": "lead_id",
        "channel": "channel",
        "direction": "direction",
        "at": "at",
        "read": "read",
        "lemlist_inbox_id": "lemlist_inbox_id",
        "lemlist_message_id": "lemlist_message_id",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "data": "data",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_indexes(self):
        """Indexes are managed by Alembic migrations."""
        logger.info("Indexes for inbox_events managed by Alembic migrations")

    async def upsert_event(self, event: Dict[str, Any]) -> str:
        """Insert or update an event.
        
        Args:
            event: Event document
            
        Returns:
            Event ID or lemlist_message_id
        """
        event["updated_at"] = datetime.utcnow()
        
        if event.get("lemlist_message_id"):
            # Try to find existing
            existing = await self.find_one({"lemlist_message_id": event["lemlist_message_id"]})
            if existing:
                await self.update_one(
                    {"lemlist_message_id": event["lemlist_message_id"]},
                    {"$set": event}
                )
                return event["lemlist_message_id"]
            else:
                if "created_at" not in event:
                    event["created_at"] = datetime.utcnow()
                result = await self.insert_one(event)
                return str(result)
        else:
            if "created_at" not in event:
                event["created_at"] = datetime.utcnow()
            result = await self.insert_one(event)
            return str(result)

    async def get_events_for_lead(self, lead_id: str, limit: int = 50, skip: int = 0,
                                   channel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get events for a lead.
        
        Args:
            lead_id: Lead ID
            limit: Max events to return
            skip: Events to skip
            channel: Optional channel filter
            
        Returns:
            List of event documents
        """
        query = {"lead_id": lead_id}
        if channel:
            query["channel"] = channel
        
        # Note: For proper sorting and pagination, we'd need to enhance base DAO
        events = await self.find_many(query)
        # Sort by 'at' descending
        events.sort(key=lambda x: x.get("at") or datetime.min, reverse=True)
        return events[skip:skip + limit]

    async def count_events_for_lead(self, lead_id: str) -> int:
        """Count events for a lead."""
        return await self.count_documents({"lead_id": lead_id})

    async def get_unread_count(self, lead_id: str) -> int:
        """Count unread inbound events."""
        return await self.count_documents({
            "lead_id": lead_id,
            "direction": "inbound",
            "read": False
        })

    async def mark_events_read(self, lead_id: str) -> int:
        """Mark all events for a lead as read."""
        return await self.update_many(
            {"lead_id": lead_id, "direction": "inbound"},
            {"$set": {"read": True, "updated_at": datetime.utcnow()}}
        )

    async def get_latest_event_for_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent event."""
        events = await self.find_many({"lead_id": lead_id})
        if not events:
            return None
        events.sort(key=lambda x: x.get("at") or datetime.min, reverse=True)
        return events[0] if events else None

    async def bulk_upsert_events(self, events: List[Dict[str, Any]]) -> int:
        """Bulk upsert events."""
        if not events:
            return 0
        
        count = 0
        for event in events:
            await self.upsert_event(event)
            count += 1
        return count

    async def count_events(self, query: Dict[str, Any] = None) -> int:
        """Count events matching query."""
        return await self.count_documents(query or {})


class PostgresInboxLeadsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for inbox_leads table."""
    
    model = InboxLead
    
    COLUMN_MAP = {
        "_id": "id",
        "lead_id": "lead_id",
        "lemlist_inbox_id": "lemlist_inbox_id",
        "lemlist_contact_id": "lemlist_contact_id",
        "temperature": "temperature",
        "status": "status",
        "in_sequence": "in_sequence",
        "unread_count": "unread_count",
        "owner.email": "owner_email",
        "last_touch.at": "last_touch_at",
        "next_step_at": "next_step_at",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "company": "company",
        "contact": "contact",
        "owner": "owner",
        "sequence": "sequence",
        "last_touch": "last_touch",
        "channels_present": "channels_present",
        "temperature_drivers": "temperature_drivers",
    }
    
    ARRAY_FIELDS = ["channels_present"]
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_indexes(self):
        """Indexes are managed by Alembic migrations."""
        logger.info("Indexes for inbox_leads managed by Alembic migrations")

    async def upsert_lead(self, lead: Dict[str, Any]) -> str:
        """Insert or update a lead."""
        lead["updated_at"] = datetime.utcnow()
        
        existing = await self.find_one({"lead_id": lead["lead_id"]})
        if existing:
            await self.update_one({"lead_id": lead["lead_id"]}, {"$set": lead})
            return lead["lead_id"]
        else:
            if "created_at" not in lead:
                lead["created_at"] = datetime.utcnow()
            await self.insert_one(lead)
            return lead["lead_id"]

    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by ID."""
        return await self.find_one({"lead_id": lead_id})

    async def get_lead_by_lemlist_inbox(self, lemlist_inbox_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by Lemlist inbox ID."""
        return await self.find_one({"lemlist_inbox_id": lemlist_inbox_id})

    async def get_lead_by_lemlist_contact(self, lemlist_contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead by Lemlist contact ID."""
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
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search and filter leads."""
        filter_query: Dict[str, Any] = {}
        
        # Text search (simplified - would need proper implementation)
        if query:
            # This would need JSONB text search
            pass
        
        if channel:
            filter_query["channels_present"] = {"$in": [channel]}
        
        if temperature:
            filter_query["temperature"] = temperature
        
        if status:
            filter_query["status"] = status
        
        if in_sequence == "yes":
            filter_query["in_sequence"] = True
        elif in_sequence == "no":
            filter_query["in_sequence"] = False
        
        if owner_email:
            filter_query["owner_email"] = owner_email
        
        # Get total count
        total = await self.count_documents(filter_query)
        
        # Get leads with pagination
        results, _ = await self.get_paginated_response(
            filter_query, 
            page_size=page_size, 
            page_number=page,
            sort_by=[("last_touch_at", -1)]
        )
        
        return results, total

    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status."""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def update_lead_temperature(self, lead_id: str, temperature: str,
                                       drivers: Optional[List[str]] = None) -> bool:
        """Update lead temperature."""
        update = {"temperature": temperature, "updated_at": datetime.utcnow()}
        if drivers is not None:
            update["temperature_drivers"] = drivers
        result = await self.update_one({"lead_id": lead_id}, {"$set": update})
        return result > 0

    async def update_unread_count(self, lead_id: str, count: int) -> bool:
        """Update unread count."""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$set": {"unread_count": count, "updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def increment_unread_count(self, lead_id: str) -> bool:
        """Increment unread count."""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$inc": {"unread_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def reset_unread_count(self, lead_id: str) -> bool:
        """Reset unread count to 0."""
        return await self.update_unread_count(lead_id, 0)

    async def update_last_touch(self, lead_id: str, last_touch: Dict[str, Any]) -> bool:
        """Update last touch."""
        update_data = {"last_touch": last_touch, "updated_at": datetime.utcnow()}
        if "at" in last_touch:
            update_data["last_touch_at"] = last_touch["at"]
        result = await self.update_one({"lead_id": lead_id}, {"$set": update_data})
        return result > 0

    async def add_channel(self, lead_id: str, channel: str) -> bool:
        """Add a channel to channels_present."""
        result = await self.update_one(
            {"lead_id": lead_id},
            {"$addToSet": {"channels_present": channel}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result > 0

    async def bulk_upsert_leads(self, leads: List[Dict[str, Any]]) -> int:
        """Bulk upsert leads."""
        if not leads:
            return 0
        
        count = 0
        for lead in leads:
            await self.upsert_lead(lead)
            count += 1
        return count

    async def get_all_lead_ids(self) -> List[str]:
        """Get all lead IDs."""
        leads = await self.find_many({})
        return [lead["lead_id"] for lead in leads]

    async def count_leads(self, query: Dict[str, Any] = None) -> int:
        """Count leads matching query."""
        return await self.count_documents(query or {})

    async def find_leads(self, query: Dict[str, Any] = None, limit: int = 50,
                         sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find leads matching query."""
        results, _ = await self.get_paginated_response(
            query or {},
            page_size=limit,
            page_number=1,
            sort_by=sort
        )
        return results


class PostgresInboxNotesDao(BasePostgresDao):
    """PostgreSQL Data Access Object for inbox_notes table."""
    
    model = InboxNote
    
    COLUMN_MAP = {
        "_id": "id",
        "lead_id": "lead_id",
        "author": "author",
        "text": "text",
        "at": "at",
        "created_at": "created_at",
    }
    
    JSONB_FIELDS = {}
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_indexes(self):
        """Indexes are managed by Alembic migrations."""
        logger.info("Indexes for inbox_notes managed by Alembic migrations")

    async def add_note(self, lead_id: str, author: str, text: str) -> str:
        """Add a note for a lead."""
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
        """Get notes for a lead."""
        notes = await self.find_many({"lead_id": lead_id})
        notes.sort(key=lambda x: x.get("at") or datetime.min, reverse=True)
        return notes[:limit]

    async def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        result = await self.delete_one({"_id": note_id})
        return result > 0


