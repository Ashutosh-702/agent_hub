"""Core meeting service logic."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from bson import ObjectId

from config.loaded_config import loaded_config
from database.factory import get_meetings_dao, get_companies_dao, get_contacts_dao
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
from ai_agents.meetings.post_call_analyzer import PostCallAnalyzer
from ai_agents.meetings.red_flag_detector import RedFlagDetector

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
        self._meetings_dao: Optional[Any] = None
        self._companies_dao: Optional[Any] = None
        self._contacts_dao: Optional[Any] = None
        self._battlecard_generator = BattlecardGenerator()
        self._reflections_generator = ReflectionsGenerator()
        self._post_call_analyzer = PostCallAnalyzer()
        self._red_flag_detector = RedFlagDetector()
    
    def _get_meetings_dao(self):
        """Get or create MeetingsDao instance."""
        if not self._meetings_dao:
            self._meetings_dao = get_meetings_dao(loaded_config.connection_manager)
        return self._meetings_dao
    
    def _get_companies_dao(self):
        """Get or create CompaniesDao instance."""
        if not self._companies_dao:
            self._companies_dao = get_companies_dao(loaded_config.connection_manager)
        return self._companies_dao
    
    def _get_contacts_dao(self):
        """Get or create ContactsDao instance."""
        if not self._contacts_dao:
            self._contacts_dao = get_contacts_dao(loaded_config.connection_manager)
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
    
    async def _get_meeting_by_id_or_uuid(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Helper to get meeting by either ObjectId or UUID.
        
        Args:
            meeting_id: Meeting ID (ObjectId or UUID)
            
        Returns:
            Meeting data or None
        """
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        objectid_pattern = re.compile(r'^[0-9a-f]{24}$', re.IGNORECASE)
        
        if uuid_pattern.match(meeting_id):
            return await self.get_meeting_by_uuid(meeting_id)
        elif objectid_pattern.match(meeting_id):
            return await self.get_meeting(meeting_id)
        else:
            # Try ObjectId first, then UUID
            try:
                return await self.get_meeting(meeting_id)
            except:
                return await self.get_meeting_by_uuid(meeting_id)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting by ID (supports both ObjectId and UUID).
        
        Args:
            meeting_id: Meeting ID (MongoDB ObjectId string or UUID)
            
        Returns:
            Meeting data or None
        """
        meetings_dao = self._get_meetings_dao()
        # Try ObjectId first
        try:
            from bson import ObjectId
            # Validate if it's a valid ObjectId format
            ObjectId(meeting_id)
            meeting = await meetings_dao.get_meeting(meeting_id)
            return self._serialize_meeting(meeting)
        except (ValueError, Exception):
            # If ObjectId conversion fails, try UUID
            try:
                meeting = await meetings_dao.get_meeting_by_uuid(meeting_id)
                return self._serialize_meeting(meeting)
            except Exception:
                return None
    
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
        # Handle both list format and legacy double-nested format {"transcript": [...]}
        if isinstance(transcript, dict) and "transcript" in transcript:
            transcript = transcript.get("transcript", [])
        if not transcript or not isinstance(transcript, list):
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
    
    async def analyze_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Analyze a completed meeting and generate comprehensive post-call summary.
        
        Args:
            meeting_id: Meeting ID (ObjectId or UUID)
            
        Returns:
            Analysis with summary, key points, objections, action items, next steps, follow-up draft
        """
        meetings_dao = self._get_meetings_dao()
        companies_dao = self._get_companies_dao()
        contacts_dao = self._get_contacts_dao()
        
        # Get raw meeting data (not serialized) for internal operations
        # This preserves _id which we need for updates
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if uuid_pattern.match(meeting_id):
            meeting = await meetings_dao.get_meeting_by_uuid(meeting_id)
        else:
            meeting = await meetings_dao.get_meeting(meeting_id)
        
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Get transcript
        transcript = meeting.get("transcript", [])
        logger.info(f"📝 Raw transcript type: {type(transcript)}, value preview: {str(transcript)[:200] if transcript else 'None'}")
        
        # Handle both list format and legacy double-nested format {"transcript": [...]}
        if isinstance(transcript, dict) and "transcript" in transcript:
            transcript = transcript.get("transcript", [])
        if not transcript or not isinstance(transcript, list):
            raise ValueError(f"Meeting {meeting_id} has no transcript to analyze")
        
        # Get company data
        company_data = None
        company_id = meeting.get("company_id")
        if company_id:
            company_data = await companies_dao.get_company(str(company_id))
        
        # Get contact data
        contact_data = None
        contact_ids = meeting.get("contact_ids", [])
        # Handle both list format and legacy double-nested format {"contact_ids": [...]}
        if isinstance(contact_ids, dict) and "contact_ids" in contact_ids:
            contact_ids = contact_ids.get("contact_ids", [])
        if contact_ids and isinstance(contact_ids, list) and len(contact_ids) > 0:
            contact_data = await contacts_dao.get_contact(str(contact_ids[0]))
        
        # Get previous meetings
        previous_meetings = []
        if company_id:
            # Get the actual meeting _id for exclusion (using raw meeting, so _id is available)
            meeting_obj_id = meeting.get("_id")
            previous = await meetings_dao.get_previous_meetings(
                company_id=str(company_id),
                exclude_meeting_id=str(meeting_obj_id) if meeting_obj_id else None,
            )
            previous_meetings = previous[:3]
        
        # Get company name
        company_name = company_data.get("name", "") if company_data else ""
        
        # Log API key status for debugging
        api_key = loaded_config.openai_api_key
        logger.info(f"Analyzing meeting {meeting_id}. OpenAI API key present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
        
        # Get product_ids and unwrap if double-nested
        product_ids = meeting.get("product_ids", [])
        if isinstance(product_ids, dict) and "product_ids" in product_ids:
            product_ids = product_ids.get("product_ids", [])
        if not isinstance(product_ids, list):
            product_ids = []
        
        # Analyze meeting
        analysis = await self._post_call_analyzer.analyze_meeting(
            transcript=transcript,
            company_data=company_data,
            contact_data=contact_data,
            products=product_ids,
            previous_meetings=previous_meetings,
            company_name=company_name,
        )
        
        # Save to meeting - use the actual _id from the raw meeting document
        meeting_obj_id = meeting.get("_id")
        if meeting_obj_id:
            update_data = {
                "summary": analysis.get("summary"),
                "key_discussion_points": analysis.get("key_discussion_points", []),
                "action_items": analysis.get("action_items", []),
                "next_steps": analysis.get("next_steps", []),
                "objections_resolutions": analysis.get("objections_resolutions", []),
            }
            await meetings_dao.update_meeting(str(meeting_obj_id), update_data)
        
        logger.info(f"Analyzed meeting {meeting_id}")
        return analysis
    
    async def get_follow_up_draft(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get the follow-up email draft for a meeting.
        
        Args:
            meeting_id: Meeting ID (ObjectId or UUID)
            
        Returns:
            Follow-up message with subject and body
        """
        meetings_dao = self._get_meetings_dao()
        
        # Get meeting (handles both UUID and ObjectId)
        meeting = await self._get_meeting_by_id_or_uuid(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Check if we have a summary with follow-up message
        summary = meeting.get("summary")
        if not summary:
            # Generate analysis if not done
            analysis = await self.analyze_meeting(meeting_id)
            return analysis.get("follow_up_message", {
                "subject": "Meeting Follow-up",
                "body": "Thank you for your time today."
            })
        
        # Try to get from stored analysis or generate
        # For now, we'll regenerate to ensure we have the draft
        analysis = await self.analyze_meeting(meeting_id)
        return analysis.get("follow_up_message", {
            "subject": "Meeting Follow-up",
            "body": "Thank you for your time today."
        })


# Singleton instance
meeting_service = MeetingService()

