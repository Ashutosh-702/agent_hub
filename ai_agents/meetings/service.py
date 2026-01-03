"""Core meeting service logic."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from bson import ObjectId

from config.loaded_config import loaded_config
from database.collection_dao.meetings import MeetingsDao
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.contacts import ContactsDao
from ai_agents.meetings.models import (
    MeetingRecord,
    MeetingStatus,
    CreateMeetingRequest,
    UpdateMeetingRequest,
    UpdateManualReflectionsRequest,
    ManualReflections,
)
from ai_agents.meetings.battlecard_generator import BattlecardGenerator
from ai_agents.meetings.reflections_generator import ReflectionsGenerator

logger = logging.getLogger(__name__)


class MeetingService:
    """
    Service layer for meeting operations.
    
    Provides business logic for:
    - Meeting CRUD operations
    - Battlecard generation
    - Reflections management
    """
    
    def __init__(self):
        """Initialize the meeting service."""
        self._meetings_dao: Optional[MeetingsDao] = None
        self._companies_dao: Optional[CompaniesDao] = None
        self._contacts_dao: Optional[ContactsDao] = None
        self._battlecard_generator = BattlecardGenerator()
        self._reflections_generator = ReflectionsGenerator()
    
    def _get_meetings_dao(self) -> MeetingsDao:
        """Get or create MeetingsDao instance."""
        if not self._meetings_dao:
            self._meetings_dao = MeetingsDao(loaded_config.connection_manager.mongo_client)
        return self._meetings_dao
    
    def _get_companies_dao(self) -> CompaniesDao:
        """Get or create CompaniesDao instance."""
        if not self._companies_dao:
            self._companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        return self._companies_dao
    
    def _get_contacts_dao(self) -> ContactsDao:
        """Get or create ContactsDao instance."""
        if not self._contacts_dao:
            self._contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
        return self._contacts_dao
    
    def _serialize_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize meeting data for API response."""
        if not meeting_data:
            return None
        
        # Convert ObjectId to string
        if "_id" in meeting_data:
            meeting_data["id"] = str(meeting_data["_id"])
            del meeting_data["_id"]
        
        if "company_id" in meeting_data and meeting_data["company_id"]:
            meeting_data["company_id"] = str(meeting_data["company_id"])
        
        if "contact_ids" in meeting_data:
            meeting_data["contact_ids"] = [str(cid) for cid in meeting_data["contact_ids"]]
        
        if "previous_meetings_refs" in meeting_data:
            meeting_data["previous_meetings_refs"] = [
                str(mid) for mid in meeting_data["previous_meetings_refs"]
            ]
        
        return meeting_data
    
    async def create_meeting(self, request: CreateMeetingRequest) -> Dict[str, Any]:
        """
        Create a new meeting record.
        
        Args:
            request: CreateMeetingRequest with meeting details
            
        Returns:
            Created meeting data
        """
        meetings_dao = self._get_meetings_dao()
        
        # Build meeting document
        meeting_data = {
            "meeting_id": str(uuid.uuid4()),
            "company_id": ObjectId(request.company_id),
            "contact_ids": [ObjectId(cid) for cid in request.contact_ids],
            "product_ids": request.product_ids,
            "call_type": request.call_type.value,
            "meeting_name": request.meeting_name,
            "notes": request.notes,
            "status": MeetingStatus.SCHEDULED.value,
            "scheduled_at": request.scheduled_at,
            "transcript": [],
            "live_insights": [],
            "action_items": [],
            "next_steps": [],
        }
        
        # Get company domain
        try:
            company = await self._get_companies_dao().get_company(request.company_id)
            if company:
                meeting_data["company_domain"] = company.get("domain")
        except Exception as e:
            logger.warning(f"Could not fetch company domain: {e}")
        
        # Create meeting
        meeting_id = await meetings_dao.create_meeting(meeting_data)
        
        # Fetch and return created meeting
        created = await meetings_dao.get_meeting(meeting_id)
        return self._serialize_meeting(created)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting by ID.
        
        Args:
            meeting_id: Meeting ID (MongoDB ObjectId string)
            
        Returns:
            Meeting data or None
        """
        meetings_dao = self._get_meetings_dao()
        meeting = await meetings_dao.get_meeting(meeting_id)
        return self._serialize_meeting(meeting)
    
    async def get_meeting_by_uuid(self, meeting_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting by its UUID.
        
        Args:
            meeting_uuid: Meeting UUID
            
        Returns:
            Meeting data or None
        """
        meetings_dao = self._get_meetings_dao()
        meeting = await meetings_dao.get_meeting_by_uuid(meeting_uuid)
        return self._serialize_meeting(meeting)
    
    async def get_meetings(
        self,
        status: Optional[str] = None,
        company_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get meetings with filters and pagination.
        
        Args:
            status: Filter by status
            company_id: Filter by company
            page: Page number
            limit: Items per page
            
        Returns:
            Dict with meetings list and pagination info
        """
        meetings_dao = self._get_meetings_dao()
        
        query = {}
        if status:
            query["status"] = status
        if company_id:
            query["company_id"] = ObjectId(company_id)
        
        meetings, pagination = await meetings_dao.get_meetings_paginated(
            query=query,
            page=page,
            limit=limit,
        )
        
        return {
            "meetings": [self._serialize_meeting(m) for m in meetings],
            "pagination": pagination,
        }
    
    async def update_meeting(
        self,
        meeting_id: str,
        request: UpdateMeetingRequest,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a meeting.
        
        Args:
            meeting_id: Meeting ID
            request: Update data
            
        Returns:
            Updated meeting data
        """
        meetings_dao = self._get_meetings_dao()
        
        update_data = request.model_dump(exclude_none=True)
        if "status" in update_data:
            update_data["status"] = update_data["status"].value
        
        if update_data:
            await meetings_dao.update_meeting(meeting_id, update_data)
        
        return await self.get_meeting(meeting_id)
    
    async def delete_meeting(self, meeting_id: str) -> bool:
        """
        Soft delete a meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            True if deleted
        """
        meetings_dao = self._get_meetings_dao()
        return await meetings_dao.delete_meeting(meeting_id)
    
    async def generate_battlecard(self, meeting_id: str) -> Dict[str, Any]:
        """
        Generate a battlecard for a meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Generated battlecard data
        """
        battlecard = await self._battlecard_generator.generate_battlecard_for_meeting(
            meeting_id=meeting_id,
            meetings_dao=self._get_meetings_dao(),
            companies_dao=self._get_companies_dao(),
            contacts_dao=self._get_contacts_dao(),
        )
        return battlecard.model_dump()
    
    async def generate_reflections(self, meeting_id: str) -> Dict[str, Any]:
        """
        Generate AI reflections for a meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Generated reflections data
        """
        reflections = await self._reflections_generator.regenerate_reflections(
            meeting_id=meeting_id,
            meetings_dao=self._get_meetings_dao(),
            companies_dao=self._get_companies_dao(),
            contacts_dao=self._get_contacts_dao(),
        )
        return reflections.model_dump()
    
    async def get_reflections(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get reflections for a meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Reflections data
        """
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None
        return meeting.get("reflections")
    
    async def update_manual_reflections(
        self,
        meeting_id: str,
        request: UpdateManualReflectionsRequest,
    ) -> Dict[str, Any]:
        """
        Update manual reflections for a meeting.
        
        Args:
            meeting_id: Meeting ID
            request: Manual reflections data
            
        Returns:
            Updated reflections
        """
        meetings_dao = self._get_meetings_dao()
        
        # Get current reflections
        meeting = await meetings_dao.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        current_reflections = meeting.get("reflections", {}) or {}
        current_manual = current_reflections.get("manual", {}) or {}
        
        # Merge with new data
        update_data = request.model_dump(exclude_none=True)
        merged = {**current_manual, **update_data}
        merged["updated_at"] = datetime.utcnow()
        
        # Save
        await meetings_dao.set_manual_reflections(meeting_id, merged)
        
        return merged
    
    async def get_meetings_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Get all meetings for a company.
        
        Args:
            company_id: Company ID
            
        Returns:
            List of meetings
        """
        meetings_dao = self._get_meetings_dao()
        meetings = await meetings_dao.get_meetings_by_company(company_id)
        return [self._serialize_meeting(m) for m in meetings]
    
    async def get_completed_meetings(self) -> List[Dict[str, Any]]:
        """
        Get all completed meetings (for reflections history).
        
        Returns:
            List of completed meetings
        """
        meetings_dao = self._get_meetings_dao()
        meetings = await meetings_dao.get_completed_meetings()
        return [self._serialize_meeting(m) for m in meetings]
    
    async def start_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Transition meeting to live status.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Updated meeting with WebSocket URL info
        """
        meetings_dao = self._get_meetings_dao()
        
        meeting = await meetings_dao.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Get the meeting UUID for WebSocket connection
        meeting_uuid = meeting.get("meeting_id")
        
        return {
            "meeting_id": meeting_id,
            "meeting_uuid": meeting_uuid,
            "websocket_url": f"/ws/meetings/{meeting_uuid}",
            "status": "ready",
        }
    
    async def get_meeting_context(self, meeting_id: str) -> Dict[str, Any]:
        """
        Generate meeting context for a live call using OpenAI.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Meeting context data
        """
        from ai_agents.meetings.context_generator import context_generator
        
        meetings_dao = self._get_meetings_dao()
        companies_dao = self._get_companies_dao()
        contacts_dao = self._get_contacts_dao()
        
        # Get meeting data
        meeting = await meetings_dao.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Get company data
        company_data = None
        company_id = meeting.get("company_id")
        if company_id:
            company_data = await companies_dao.get_company(str(company_id))
        
        # Get contacts data
        contacts_data = []
        contact_ids = meeting.get("contact_ids", [])
        for cid in contact_ids:
            contact = await contacts_dao.get_contact(str(cid))
            if contact:
                contacts_data.append(contact)
        
        # Get products
        products = meeting.get("product_ids", [])
        
        # Get previous meetings count
        previous_meetings = 0
        if company_id:
            previous = await meetings_dao.get_meetings_by_company(str(company_id))
            previous_meetings = len([m for m in previous if m.get("_id") != meeting.get("_id")])
        
        # Generate context using OpenAI
        context = await context_generator.generate_meeting_context(
            company_data=company_data,
            contacts_data=contacts_data,
            products=products,
            previous_meetings=previous_meetings,
            notes=meeting.get("notes"),
        )
        
        return context
    
    async def generate_summary(self, meeting_id: str) -> Dict[str, Any]:
        """
        Generate a post-call summary using OpenAI.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Generated summary data
        """
        from ai_agents.meetings.context_generator import context_generator
        
        meetings_dao = self._get_meetings_dao()
        companies_dao = self._get_companies_dao()
        contacts_dao = self._get_contacts_dao()
        
        # Get meeting data
        meeting = await meetings_dao.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Get transcript
        transcript = meeting.get("transcript", [])
        if not transcript:
            raise ValueError(f"Meeting {meeting_id} has no transcript to summarize")
        
        # Get company name
        company_name = ""
        company_id = meeting.get("company_id")
        if company_id:
            company = await companies_dao.get_company(str(company_id))
            if company:
                company_name = company.get("name", "")
        
        # Get contact names
        contacts = []
        contact_ids = meeting.get("contact_ids", [])
        for cid in contact_ids:
            contact = await contacts_dao.get_contact(str(cid))
            if contact:
                name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                if name:
                    contacts.append(name)
        
        # Calculate duration
        started_at = meeting.get("started_at")
        ended_at = meeting.get("ended_at")
        duration = 0
        if started_at and ended_at:
            duration = int((ended_at - started_at).total_seconds())
        
        # Generate summary using OpenAI
        summary = await context_generator.generate_post_call_summary(
            transcript=transcript,
            company_name=company_name,
            contacts=contacts,
            products=meeting.get("product_ids", []),
            meeting_duration=duration,
        )
        
        # Save summary to meeting
        update_data = {
            "summary": summary.get("summary"),
            "key_discussion_points": summary.get("keyPoints", []),
            "action_items": summary.get("actionItems", []),
            "next_steps": summary.get("nextSteps", []),
        }
        await meetings_dao.update_meeting(meeting_id, update_data)
        
        logger.info(f"Generated summary for meeting {meeting_id}")
        
        return summary
    
    async def transcribe_audio_file(
        self,
        meeting_id: str,
        audio_data: bytes,
        filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Transcribe an uploaded audio file for a meeting.
        
        Args:
            meeting_id: Meeting ID
            audio_data: Audio file bytes
            filename: Original filename
            
        Returns:
            List of transcript entries
        """
        from ai_agents.meetings.deepgram_service import transcribe_prerecorded_audio
        
        meetings_dao = self._get_meetings_dao()
        
        # Verify meeting exists
        meeting = await meetings_dao.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Transcribe audio using Deepgram
        transcript_entries = await transcribe_prerecorded_audio(audio_data, filename)
        
        # Save transcript to meeting
        for entry in transcript_entries:
            await meetings_dao.append_transcript(meeting_id, entry)
        
        # Update meeting status to completed
        await meetings_dao.update_meeting(meeting_id, {
            "status": "completed",
            "ended_at": datetime.utcnow(),
        })
        
        logger.info(f"Transcribed audio file for meeting {meeting_id}: {len(transcript_entries)} entries")
        
        return transcript_entries


# Singleton instance
meeting_service = MeetingService()

