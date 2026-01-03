"""WebSocket endpoint for live meeting transcription and insights."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from config.loaded_config import loaded_config
from database.collection_dao.meetings import MeetingsDao
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.contacts import ContactsDao
from ai_agents.meetings.models import (
    TranscriptEntry,
    LiveInsight,
    InsightGenerationContext,
    CompanyContext,
    ProductContext,
    ContactContext,
    PreviousMeetingContext,
)
from ai_agents.meetings.deepgram_service import create_transcription_service
from ai_agents.meetings.insights_engine import InsightsEngine
from ai_agents.meetings.reflections_generator import ReflectionsGenerator

logger = logging.getLogger(__name__)


class MeetingWebSocketHandler:
    """
    Handler for live meeting WebSocket connections.
    
    Manages:
    - Audio streaming to Deepgram
    - Transcript streaming to client
    - Real-time insight generation
    - Meeting state management
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        meeting_id: str,
        meetings_dao: MeetingsDao,
        companies_dao: Optional[CompaniesDao] = None,
        contacts_dao: Optional[ContactsDao] = None,
    ):
        """
        Initialize the WebSocket handler.
        
        Args:
            websocket: FastAPI WebSocket connection
            meeting_id: UUID of the meeting
            meetings_dao: DAO for meeting operations
            companies_dao: DAO for company operations
            contacts_dao: DAO for contact operations
        """
        self.websocket = websocket
        self.meeting_id = meeting_id
        self.meetings_dao = meetings_dao
        self.companies_dao = companies_dao
        self.contacts_dao = contacts_dao
        
        self._meeting_data: Optional[Dict[str, Any]] = None
        self._db_meeting_id: Optional[str] = None
        self._start_time: Optional[datetime] = None
        self._is_running = False
        
        # Store event loop for thread-safe callbacks from Deepgram
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Services
        self._transcription_service = None
        self._insights_engine: Optional[InsightsEngine] = None
        self._reflections_generator = ReflectionsGenerator()
        
        # State
        self._transcript: list = []
        self._insights: list = []
        
    async def _send_json(self, data: Dict[str, Any]):
        """Send JSON message to client."""
        if self.websocket.client_state == WebSocketState.CONNECTED:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    def _on_transcript_interim_sync(self, text: str, timestamp: float):
        """Sync wrapper for interim transcript callback (called from Deepgram thread)."""
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self._on_transcript_interim(text, timestamp),
                self._event_loop
            )
    
    def _on_transcript_final_sync(self, text: str, speaker: str, timestamp: float):
        """Sync wrapper for final transcript callback (called from Deepgram thread)."""
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self._on_transcript_final(text, speaker, timestamp),
                self._event_loop
            )
    
    def _on_transcription_error_sync(self, message: str):
        """Sync wrapper for transcription error callback (called from Deepgram thread)."""
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self._on_transcription_error(message),
                self._event_loop
            )
    
    async def _on_transcript_interim(self, text: str, timestamp: float):
        """Handle interim transcript from Deepgram."""
        logger.info(f"Received interim transcript: {text[:100]}...")
        await self._send_json({
            "type": "transcript_interim",
            "text": text,
            "timestamp": timestamp,
        })
    
    async def _on_transcript_final(self, text: str, speaker: str, timestamp: float):
        """Handle final transcript from Deepgram."""
        logger.info(f"Received final transcript: {text[:100]}... (speaker: {speaker})")
        
        # Create transcript entry
        entry = TranscriptEntry(
            timestamp=timestamp,
            speaker=speaker,
            text=text,
            is_final=True,
        )
        
        # Add to local buffer
        self._transcript.append(entry.model_dump())
        
        # Add to insights engine
        if self._insights_engine:
            self._insights_engine.add_transcript_entry(entry)
        
        # Save to database
        if self._db_meeting_id:
            await self.meetings_dao.append_transcript(
                self._db_meeting_id,
                entry.model_dump()
            )
        
        # Send to client
        await self._send_json({
            "type": "transcript_final",
            "text": text,
            "speaker": speaker,
            "timestamp": timestamp,
        })
        logger.debug("Sent transcript_final message to client")
        
        # Check if we should generate insights
        if self._insights_engine and self._insights_engine.should_generate_insights(timestamp, text):
            asyncio.create_task(self._generate_and_send_insights(timestamp))
    
    async def _on_transcription_error(self, message: str):
        """Handle transcription error."""
        await self._send_json({
            "type": "error",
            "message": f"Transcription error: {message}",
        })
    
    async def _generate_and_send_insights(self, current_time: float):
        """Generate insights and send to client."""
        if not self._insights_engine:
            return
        
        try:
            new_insights = await self._insights_engine.generate_insights(current_time)
            
            for insight in new_insights:
                # Save to database
                if self._db_meeting_id:
                    await self.meetings_dao.append_insight(
                        self._db_meeting_id,
                        insight.model_dump()
                    )
                
                # Add to local buffer
                self._insights.append(insight.model_dump())
                
                # Send to client
                await self._send_json({
                    "type": "insight",
                    "insight": insight.model_dump(),
                })
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
    
    async def _load_meeting_context(self) -> InsightGenerationContext:
        """Load context for the meeting from database."""
        context = InsightGenerationContext()
        
        if not self._meeting_data:
            return context
        
        # Load company research
        company_id = self._meeting_data.get("company_id")
        if company_id and self.companies_dao:
            try:
                company = await self.companies_dao.get_company(str(company_id))
                if company:
                    enriched = company.get("enriched_data", {})
                    web_analysis = enriched.get("web_search_analysis", {})
                    research = web_analysis.get("research_summary", {})
                    
                    context.company_research = CompanyContext(
                        about=research.get("about") or company.get("description"),
                        industry=company.get("industry"),
                        recent_news=research.get("recent_news", []),
                        key_initiatives=research.get("key_initiatives", []),
                        tech_stack=research.get("tech_stack", []),
                        pain_points_inferred=research.get("pain_points", []),
                    )
            except Exception as e:
                logger.error(f"Error loading company context: {e}")
        
        # Load product context
        product_ids = self._meeting_data.get("product_ids", [])
        from ai_agents.meetings.battlecard_generator import PRODUCT_INFO
        for pid in product_ids:
            if pid in PRODUCT_INFO:
                p = PRODUCT_INFO[pid]
                context.products.append(ProductContext(
                    name=p["name"],
                    key_features=p["key_features"],
                    differentiators=p["differentiators"],
                    common_objections=p["common_objections"],
                ))
        
        # Load contact context
        contact_ids = self._meeting_data.get("contact_ids", [])
        if contact_ids and self.contacts_dao:
            try:
                contact_id = str(contact_ids[0])
                contact = await self.contacts_dao.get_contact(contact_id)
                if contact:
                    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    context.contact = ContactContext(
                        name=name,
                        title=contact.get("job_title"),
                        persona_insights=None,
                        previous_interactions=[],
                    )
            except Exception as e:
                logger.error(f"Error loading contact context: {e}")
        
        # Load previous meetings
        if company_id:
            try:
                previous = await self.meetings_dao.get_previous_meetings(
                    company_id=str(company_id),
                    exclude_meeting_id=self._db_meeting_id,
                )
                for pm in previous[:3]:
                    ended_at = pm.get("ended_at")
                    date_str = ended_at.strftime("%Y-%m-%d") if isinstance(ended_at, datetime) else str(ended_at)[:10] if ended_at else "Unknown"
                    
                    context.previous_meetings.append(PreviousMeetingContext(
                        date=date_str,
                        summary=pm.get("summary"),
                        objections_raised=[o.get("objection", "") for o in pm.get("objections_resolutions", [])],
                        next_steps_agreed=pm.get("next_steps", []),
                        products_discussed=pm.get("products_discussed", []),
                    ))
            except Exception as e:
                logger.error(f"Error loading previous meetings: {e}")
        
        return context
    
    async def initialize(self) -> bool:
        """
        Initialize the meeting session.
        
        Returns:
            True if initialization successful
        """
        try:
            # Store event loop for thread-safe callbacks
            self._event_loop = asyncio.get_running_loop()
            
            # Find meeting by UUID
            self._meeting_data = await self.meetings_dao.get_meeting_by_uuid(self.meeting_id)
            
            if not self._meeting_data:
                await self._send_json({
                    "type": "error",
                    "message": f"Meeting {self.meeting_id} not found",
                })
                return False
            
            self._db_meeting_id = str(self._meeting_data["_id"])
            
            # Update meeting status to live
            await self.meetings_dao.update_meeting(self._db_meeting_id, {
                "status": "live",
                "started_at": datetime.utcnow(),
            })
            
            # Load context for insights
            context = await self._load_meeting_context()
            
            # Initialize insights engine
            self._insights_engine = InsightsEngine(context)
            
            # Initialize transcription service with sync wrappers
            use_mock = not getattr(loaded_config, 'deepgram_api_key', None)
            self._transcription_service = create_transcription_service(
                on_transcript_interim=self._on_transcript_interim_sync,
                on_transcript_final=self._on_transcript_final_sync,
                on_error=self._on_transcription_error_sync,
                use_mock=use_mock,
            )
            
            # Connect to transcription service
            connected = await self._transcription_service.connect()
            if not connected:
                await self._send_json({
                    "type": "error",
                    "message": "Failed to connect to transcription service",
                })
                return False
            
            self._start_time = datetime.utcnow()
            self._is_running = True
            
            # Start keepalive task to prevent Deepgram timeout
            asyncio.create_task(self._deepgram_keepalive())
            
            logger.info(f"Meeting {self.meeting_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing meeting: {e}")
            await self._send_json({
                "type": "error",
                "message": f"Initialization error: {str(e)}",
            })
            return False
    
    async def handle_audio_chunk(self, audio_data: bytes):
        """Handle incoming audio chunk."""
        logger.info(f"🎤 Received audio chunk: {len(audio_data)} bytes")
        
        # Only send audio if transcription service is connected and meeting is running
        if not self._transcription_service:
            logger.warning(f"⚠️ Dropping audio: transcription service is None")
            return
        
        if not self._is_running:
            logger.warning(f"⚠️ Dropping audio: meeting is not running")
            return
        
        if not hasattr(self._transcription_service, 'is_connected'):
            logger.warning(f"⚠️ Dropping audio: transcription service has no is_connected attribute")
            return
        
        if not self._transcription_service.is_connected:
            logger.warning(f"⚠️ Dropping audio: transcription service not connected (is_connected={self._transcription_service.is_connected})")
            return
        
        logger.info(f"✅ Sending audio chunk to Deepgram: {len(audio_data)} bytes")
        success = await self._transcription_service.send_audio(audio_data)
        if not success:
            logger.warning(f"❌ Failed to send audio chunk ({len(audio_data)} bytes) to Deepgram")
        else:
            logger.debug(f"✅ Audio chunk sent successfully")
    
    async def handle_mark_moment(self, timestamp: float, note: Optional[str] = None):
        """Handle mark moment request."""
        logger.info(f"Moment marked at {timestamp}: {note}")
        # Could save marked moments to the meeting record
    
    async def handle_pin_insight(self, insight_id: str):
        """Handle pin insight request."""
        if self._db_meeting_id:
            await self.meetings_dao.update_insight(
                self._db_meeting_id,
                insight_id,
                {"is_pinned": True}
            )
    
    async def handle_add_action_item(self, insight_id: str):
        """Handle add action item request."""
        if self._db_meeting_id:
            await self.meetings_dao.update_insight(
                self._db_meeting_id,
                insight_id,
                {"is_action_item": True}
            )
    
    async def _deepgram_keepalive(self):
        """Send periodic keepalive messages to Deepgram to prevent timeout."""
        # Deepgram requires keepalive messages within 30 seconds or it times out
        # Send keepalive every 10 seconds to be safe (3x margin)
        await asyncio.sleep(2)  # Wait 2 seconds for connection to fully establish
        
        # Send initial keepalive
        if self._transcription_service and self._transcription_service.is_connected:
            try:
                # Use Deepgram's built-in keep_alive method instead of sending audio
                success = self._transcription_service.send_keepalive()
                if success:
                    logger.debug("Sent initial keepalive to Deepgram")
                else:
                    logger.warning("Failed to send initial keepalive to Deepgram")
            except Exception as e:
                logger.warning(f"Failed to send initial keepalive: {e}")
        
        while self._is_running and self._transcription_service:
            try:
                await asyncio.sleep(10)  # Send every 10 seconds
                
                if not self._is_running:
                    break
                    
                if not self._transcription_service or not self._transcription_service.is_connected:
                    logger.warning("Transcription service not connected, stopping keepalive")
                    break
                
                # Use Deepgram's built-in keep_alive method
                # This sends the proper keepalive message that Deepgram expects
                success = self._transcription_service.send_keepalive()
                if not success:
                    logger.warning("Failed to send keepalive to Deepgram")
                    # If keepalive fails, connection might be dead - check and break
                    if not self._transcription_service.is_connected:
                        break
                else:
                    logger.debug("Sent keepalive to Deepgram")
                    
            except asyncio.CancelledError:
                logger.info("Deepgram keepalive task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Deepgram keepalive: {e}")
                # Don't break on error, keep trying but wait a bit
                await asyncio.sleep(5)
    
    async def end_meeting(self) -> Dict[str, Any]:
        """
        End the meeting and generate post-call data.
        
        Returns:
            Post-call summary data
        """
        self._is_running = False
        ended_at = datetime.utcnow()
        
        # Close transcription service
        if self._transcription_service:
            await self._transcription_service.close()
        
        # Generate post-call summary
        summary_data = {}
        if self._insights_engine:
            summary_data = await self._insights_engine.generate_post_call_summary()
        
        # Finalize meeting in database
        if self._db_meeting_id:
            await self.meetings_dao.finalize_meeting(
                self._db_meeting_id,
                ended_at=ended_at,
                summary=summary_data.get("summary", ""),
                key_discussion_points=summary_data.get("key_discussion_points", []),
                action_items=summary_data.get("action_items", []),
                next_steps=summary_data.get("next_steps", []),
                objections_resolutions=summary_data.get("objections_resolutions", []),
                products_discussed=summary_data.get("products_discussed", []),
            )
            
            # Generate AI reflections
            try:
                company_data = None
                if self._meeting_data.get("company_id") and self.companies_dao:
                    company_data = await self.companies_dao.get_company(
                        str(self._meeting_data["company_id"])
                    )
                
                reflections = await self._reflections_generator.generate_reflections(
                    transcript=self._transcript,
                    insights=self._insights,
                    company_data=company_data,
                    products=self._meeting_data.get("product_ids", []),
                )
                
                await self.meetings_dao.set_ai_reflections(
                    self._db_meeting_id,
                    reflections.model_dump()
                )
            except Exception as e:
                logger.error(f"Error generating reflections: {e}")
        
        logger.info(f"Meeting {self.meeting_id} ended")
        
        return summary_data
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        msg_type = message.get("type")
        
        if msg_type == "mark_moment":
            await self.handle_mark_moment(
                message.get("timestamp", 0),
                message.get("note")
            )
        elif msg_type == "pin_insight":
            await self.handle_pin_insight(message.get("insight_id", ""))
        elif msg_type == "add_action_item":
            await self.handle_add_action_item(message.get("insight_id", ""))
        elif msg_type == "end_meeting":
            summary = await self.end_meeting()
            await self._send_json({
                "type": "meeting_ended",
                **summary,
            })
        else:
            logger.warning(f"Unknown message type: {msg_type}")


async def meeting_websocket_endpoint(
    websocket: WebSocket,
    meeting_id: str,
):
    """
    WebSocket endpoint for live meeting sessions.
    
    Protocol:
    - Connect with meeting_id in path
    - Send binary audio chunks
    - Receive JSON messages for transcripts and insights
    - Send JSON messages for actions (pin, mark, end)
    """
    logger.info(f"WebSocket connection attempt for meeting {meeting_id}")
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for meeting {meeting_id}")
    
    # Get DAOs
    meetings_dao = MeetingsDao(loaded_config.connection_manager.mongo_client)
    companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
    contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
    
    # Create handler
    handler = MeetingWebSocketHandler(
        websocket=websocket,
        meeting_id=meeting_id,
        meetings_dao=meetings_dao,
        companies_dao=companies_dao,
        contacts_dao=contacts_dao,
    )
    
    # Initialize
    if not await handler.initialize():
        await websocket.close()
        return
    
    # Send success message to client
    await handler._send_json({
        "type": "status",
        "data": {
            "status": "connected",
            "message": "Meeting session initialized successfully"
        }
    })
    
    try:
        while True:
            # Receive message (binary audio or JSON command)
            message = await websocket.receive()
            
            if message.get("type") == "websocket.disconnect":
                break
            
            if "bytes" in message:
                # Audio chunk
                await handler.handle_audio_chunk(message["bytes"])
            elif "text" in message:
                # JSON command
                try:
                    data = json.loads(message["text"])
                    await handler.handle_message(data)
                    
                    # Check if meeting ended
                    if data.get("type") == "end_meeting":
                        break
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for meeting {meeting_id}")
        # End meeting gracefully
        await handler.end_meeting()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await handler.end_meeting()
    finally:
        # Only close if websocket is still open
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing websocket (may already be closed): {e}")

