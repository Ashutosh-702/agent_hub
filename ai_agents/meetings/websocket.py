"""WebSocket endpoint for live meeting transcription and insights."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from config.loaded_config import loaded_config

# Set up file logging for debugging
log_dir = "/Users/ashutoshtripathy/agent_hub/logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "meetings_websocket.log"))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
from database.factory import get_meetings_dao, get_companies_dao, get_contacts_dao
from database.collection_dao.products import ProductsDao
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
from ai_agents.meetings.post_call_analyzer import PostCallAnalyzer
from ai_agents.meetings.red_flag_detector import RedFlagDetector

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


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
        meetings_dao: Any,
        companies_dao: Optional[Any] = None,
        contacts_dao: Optional[Any] = None,
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
        self._post_call_analyzer = PostCallAnalyzer()
        self._red_flag_detector = RedFlagDetector()
        
        # State
        self._transcript: list = []
        self._insights: list = []
        self._insights_task: Optional[asyncio.Task] = None  # Periodic insights generation task
        self._meeting_start_time: float = 0  # Track meeting start time (Unix timestamp) for relative time calculation
        
    async def _send_json(self, data: Dict[str, Any]):
        """Send JSON message to client."""
        if self.websocket.client_state == WebSocketState.CONNECTED:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    def _on_transcript_interim_sync(self, text: str, timestamp: float, speaker: str = "user"):
        """Sync wrapper for interim transcript callback (called from Deepgram thread)."""
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self._on_transcript_interim(text, timestamp, speaker),
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
    
    async def _on_transcript_interim(self, text: str, timestamp: float, speaker: str = "user"):
        """Handle interim transcript from Deepgram."""
        try:
            # Skip empty transcripts
            if not text or not text.strip():
                logger.debug(f"⏭️ Skipping empty interim transcript from {speaker}")
                return
                
            logger.info(f"📝 Received interim transcript: {text[:100]}... (speaker: {speaker})")
            # Determine source: 'user' speaker = mic, 'client' speaker = system_audio
            source = "mic" if speaker == "user" else "system_audio"
            
            # Save to database if text is not empty - fallback for when Deepgram finals are empty
            if self._db_meeting_id and text.strip():
                entry = TranscriptEntry(
                    timestamp=timestamp,
                    speaker=speaker,
                    source=source,
                    text=text,
                    is_final=False,  # Mark as interim
                )
                try:
                    result = await self.meetings_dao.append_transcript(
                        self._db_meeting_id,
                        entry.model_dump()
                    )
                    logger.info(f"📝 Saved INTERIM transcript to DB: meeting={self._db_meeting_id}, result={result}, text={text[:50]}...")
                except Exception as e:
                    logger.error(f"❌ Failed to save interim transcript: {e}", exc_info=True)
        
            await self._send_json({
                    "type": "transcript_interim",
                    "text": text,
                    "timestamp": timestamp,
                    "speaker": speaker,
                    "source": source,
                })
            logger.debug(f"✅ Sent interim transcript to client: '{text[:50]}...'")
        except Exception as e:
            logger.error(f"❌ Error handling interim transcript: {e}", exc_info=True)
    
    async def _on_transcript_final(self, text: str, speaker: str, timestamp: float):
        """Handle final transcript from Deepgram."""
        try:
            logger.info(f"📝 Received final transcript: {text[:100] if text else '(empty)'}... (speaker: {speaker})")
            
            # Skip empty transcripts (silence or no speech detected)
            if not text or not text.strip():
                logger.debug(f"⏭️ Skipping empty transcript from {speaker}")
                return
            
            # Determine source: 'user' speaker = mic, 'client' speaker = system_audio
            source = "mic" if speaker == "user" else "system_audio"
            
            # Create transcript entry
            entry = TranscriptEntry(
                timestamp=timestamp,
                speaker=speaker,
                source=source,
                text=text,
                is_final=True,
            )
            
            # Add to local buffer
            self._transcript.append(entry.model_dump())
            
            # Add to insights engine (don't let this block transcript sending)
            try:
                if self._insights_engine:
                    self._insights_engine.add_transcript_entry(entry)
                    buffer_size = len(self._insights_engine._transcript_buffer)
                    logger.debug(f"📊 Transcript added to insights engine - buffer size: {buffer_size}")
                else:
                    logger.warning("⚠️ Insights engine not initialized - transcript not added to insights buffer")
            except Exception as insights_error:
                logger.error(f"❌ Error adding transcript to insights engine: {insights_error}", exc_info=True)
            
            # Save to database (don't let this block transcript sending)
            try:
                if self._db_meeting_id:
                    await self.meetings_dao.append_transcript(
                        self._db_meeting_id,
                        entry.model_dump()
                    )
            except Exception as db_error:
                logger.error(f"❌ Error saving transcript to database: {db_error}", exc_info=True)
            
            # Send to client - THIS IS CRITICAL, must not fail
            try:
                await self._send_json({
                    "type": "transcript_final",
                    "text": text,
                    "speaker": speaker,
                    "timestamp": timestamp,
                    "source": source,
                })
                logger.info(f"✅ Sent transcript_final message to client: '{text[:50]}...' (speaker: {speaker})")
            except Exception as send_error:
                logger.error(f"❌ CRITICAL: Failed to send transcript to client: {send_error}", exc_info=True)
                raise  # Re-raise this as it's critical
            
            # Check if we should generate insights (non-blocking, fire and forget)
            try:
                if self._insights_engine and self._insights_engine.should_generate_insights(timestamp, text):
                    asyncio.create_task(self._generate_and_send_insights(timestamp))
            except Exception as insights_gen_error:
                logger.error(f"❌ Error triggering insights generation: {insights_gen_error}", exc_info=True)
                # Don't re-raise - insights generation failure shouldn't block transcripts
                
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in _on_transcript_final: {e}", exc_info=True)
            # Try to send error to client
            try:
                await self._send_json({
                    "type": "error",
                    "message": f"Error processing transcript: {str(e)}",
                })
            except:
                pass  # If we can't even send errors, something is very wrong
    
    async def _on_transcription_error(self, message: str):
        """Handle transcription error."""
        await self._send_json({
            "type": "error",
            "message": f"Transcription error: {message}",
        })
    
    async def _generate_and_send_insights(self, current_time: float):
        """Generate insights and send to client."""
        if not self._insights_engine:
            logger.warning("⚠️ Insights engine not initialized, cannot generate insights")
            return
        
        try:
            buffer_size = len(self._insights_engine._transcript_buffer)
            logger.info(f"🔍 GENERATING INSIGHTS - time: {current_time:.1f}s, transcript buffer: {buffer_size} entries")
            
            new_insights = await self._insights_engine.generate_insights(current_time)
            
            logger.info(f"📊 INSIGHT GENERATION RESULT - Generated {len(new_insights)} new insights at {current_time:.1f}s")
            
            if not new_insights:
                logger.warning(f"⚠️ No insights generated at {current_time:.1f}s - may be due to low confidence, duplicates, empty transcript, or API returned empty")
                logger.debug(f"   Buffer size: {buffer_size}, Last insight time: {self._insights_engine._last_insight_time}")
            
            for insight in new_insights:
                try:
                    # Convert to dict with proper serialization (use mode='json' to ensure enum values are strings)
                    insight_dict = insight.model_dump(mode='json')
                    # Ensure type is a string (not enum) - double check
                    if 'type' in insight_dict:
                        if hasattr(insight_dict['type'], 'value'):
                            insight_dict['type'] = insight_dict['type'].value
                        elif isinstance(insight_dict['type'], str):
                            # Already a string, ensure it's lowercase
                            insight_dict['type'] = insight_dict['type'].lower()
                        else:
                            insight_dict['type'] = str(insight_dict['type']).lower()
                    
                    logger.info(f"📤 Sending insight: type={insight_dict.get('type')}, message={insight_dict.get('message', '')[:50]}...")
                    
                    # Save to database
                    if self._db_meeting_id:
                        try:
                            await self.meetings_dao.append_insight(
                                self._db_meeting_id,
                                insight_dict
                            )
                        except Exception as db_error:
                            logger.error(f"❌ Error saving insight to database: {db_error}", exc_info=True)
                    
                    # Add to local buffer
                    self._insights.append(insight_dict)
                    
                    # Send to client
                    await self._send_json({
                        "type": "insight",
                        "insight": insight_dict,
                    })
                    logger.info(f"✅ Successfully sent insight to client: {insight_dict.get('id')} (type: {insight_dict.get('type')})")
                except Exception as insight_error:
                    logger.error(f"❌ Error processing/sending insight: {insight_error}", exc_info=True)
                    continue
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
    
    async def _periodic_insights_generation(self):
        """
        Periodic task that generates insights every 20 seconds.
        
        This ensures insights are generated even if there are no new transcripts,
        as long as there's some transcript content available.
        """
        import time
        
        # Wait a bit for initial transcript to accumulate (skip test insight at 5s)
        await asyncio.sleep(25)  # Wait 25 seconds before first generation
        
        # Track when we last generated insights (for this periodic task)
        last_periodic_generation = 0
        
        while self._is_running:
            try:
                # Check if we have transcript content
                if not self._insights_engine:
                    logger.warning("⚠️ Insights engine not initialized - skipping periodic generation")
                    await asyncio.sleep(20)
                    continue
                
                # Check buffer directly (more reliable than get_recent_transcript)
                buffer_size = len(self._insights_engine._transcript_buffer)
                recent_transcript = self._insights_engine.get_recent_transcript()
                transcript_count = len(recent_transcript)
                
                # Calculate relative time from meeting start (matching transcript timestamps)
                current_relative_time = time.time() - self._meeting_start_time
                
                if buffer_size == 0:
                    logger.debug(f"⏳ No transcript buffer yet - waiting... (meeting time: {current_relative_time:.1f}s)")
                    await asyncio.sleep(20)
                    continue
                
                # For periodic task, always generate if 20+ seconds have passed since last periodic generation
                # This ensures we generate every 20 seconds regardless of other factors
                time_since_last_periodic = current_relative_time - last_periodic_generation
                
                if time_since_last_periodic >= self._insights_engine.time_trigger_seconds:
                    logger.info(f"🔄 PERIODIC INSIGHTS TRIGGERED - buffer: {buffer_size} entries, recent: {transcript_count} entries, meeting: {current_relative_time:.1f}s, last periodic: {last_periodic_generation:.1f}s ago ({time_since_last_periodic:.1f}s gap)")
                    try:
                        await self._generate_and_send_insights(current_relative_time)
                        last_periodic_generation = current_relative_time
                        logger.info(f"✅ Periodic insights generation completed at {current_relative_time:.1f}s")
                    except Exception as gen_error:
                        logger.error(f"❌ Error during periodic insights generation: {gen_error}", exc_info=True)
                        # Don't update last_periodic_generation on error, so we retry sooner
                else:
                    logger.debug(f"⏸️ Too soon - last periodic {time_since_last_periodic:.1f}s ago, need {self._insights_engine.time_trigger_seconds}s (buffer: {buffer_size}, meeting: {current_relative_time:.1f}s)")
                
                # Wait 20 seconds before next check
                await asyncio.sleep(20)
                
            except asyncio.CancelledError:
                logger.info("Periodic insights task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in periodic insights loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _load_product_context(
        self,
        context: InsightGenerationContext,
        product_ids: list,
    ) -> None:
        """
        Load product context from MongoDB with JSON fallback.
        
        Args:
            context: InsightGenerationContext to populate
            product_ids: List of product IDs to load
        """
        if not product_ids:
            return
        
        products_loaded = False
        
        # Try MongoDB first
        try:
            products_dao = ProductsDao(loaded_config.connection_manager.mongo_client)
            db_products = await products_dao.get_products_for_insights(product_ids)
            
            if db_products:
                for pid, p in db_products.items():
                    # Extract feature titles for key_features list
                    key_features = []
                    for f in p.get("key_features", []):
                        if isinstance(f, dict):
                            key_features.append(f.get("title", ""))
                        else:
                            key_features.append(str(f))
                    
                    context.products.append(ProductContext(
                        name=p.get("name", pid),
                        key_features=key_features or p.get("benefits", []),
                        differentiators=p.get("differentiators", []),
                        common_objections=p.get("common_objections", {}),
                        case_studies=[logo for logo in p.get("customer_logos", [])[:5]],
                    ))
                products_loaded = True
                logger.info(f"Loaded {len(db_products)} products from MongoDB")
                
        except Exception as e:
            logger.warning(f"Could not load products from MongoDB: {e}")
        
        # Fallback to JSON file
        if not products_loaded:
            try:
                from ai_agents.meetings.product_knowledge_service import ProductKnowledgeService
                
                service = ProductKnowledgeService()
                json_products = service.get_products_by_ids(product_ids)
                
                for pid, p in json_products.items():
                    context.products.append(ProductContext(
                        name=p.get("name", pid),
                        key_features=p.get("key_features", []),
                        differentiators=p.get("differentiators", []),
                        common_objections=p.get("common_objections", {}),
                        case_studies=p.get("case_studies", []),
                    ))
                
                if json_products:
                    logger.info(f"Loaded {len(json_products)} products from JSON fallback")
                    
            except Exception as e:
                logger.warning(f"Could not load products from JSON fallback: {e}")
                
                # Final fallback to battlecard PRODUCT_INFO
                try:
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
                    logger.info(f"Loaded products from PRODUCT_INFO fallback")
                except Exception as e2:
                    logger.error(f"All product loading methods failed: {e2}")
    
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
        
        # Load product context from MongoDB with JSON fallback
        product_ids = self._meeting_data.get("product_ids", [])
        # Handle both list format and legacy double-nested format {"product_ids": [...]}
        if isinstance(product_ids, dict) and "product_ids" in product_ids:
            product_ids = product_ids.get("product_ids", [])
        await self._load_product_context(context, product_ids)
        
        # Load contact context
        contact_ids = self._meeting_data.get("contact_ids", [])
        # Handle both list format and legacy double-nested format {"contact_ids": [...]}
        if isinstance(contact_ids, dict) and "contact_ids" in contact_ids:
            contact_ids = contact_ids.get("contact_ids", [])
        if contact_ids and isinstance(contact_ids, list) and len(contact_ids) > 0 and self.contacts_dao:
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
            logger.info(f"✅ InsightsEngine initialized - OpenAI client: {'✅ Present' if self._insights_engine._openai_client else '❌ Missing (API key not configured)'}")
            logger.info(f"   Context loaded - Company: {bool(context.company_research)}, Products: {len(context.products)}, Contact: {bool(context.contact)}")
            
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
            import time
            self._meeting_start_time = time.time()  # Store Unix timestamp for relative calculations
            self._is_running = True
            
            # Start keepalive task to prevent Deepgram timeout
            asyncio.create_task(self._deepgram_keepalive())
            
            # Start periodic insights generation task
            self._insights_task = asyncio.create_task(self._periodic_insights_generation())
            logger.info(f"✅ Started periodic insights generation task (will start after 25s, then every 20s)")
            
            # Send a test insight after 5 seconds to verify frontend can receive insights
            asyncio.create_task(self._send_test_insight())
            logger.info(f"✅ Started test insight task (will send after 5s)")
            
            logger.info(f"Meeting {self.meeting_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing meeting: {e}", exc_info=True)
            await self._send_json({
                "type": "error",
                "message": f"Initialization error: {str(e)}",
            })
            return False
    
    async def _send_test_insight(self):
        """Send a test insight to verify frontend connectivity."""
        await asyncio.sleep(5)  # Wait 5 seconds after initialization
        
        if not self._is_running:
            return
        
        test_insight = {
            "id": "test-insight-1",
            "type": "discovery_question",
            "message": "Test: Ask about their current order cancellation rate",
            "suggested_response": "You mentioned inventory issues - what's the impact on your order cancellation rate?",
            "timestamp": 5.0,
            "confidence": 0.9,
            "evidence": "Test insight to verify connectivity",
        }
        
        logger.info("🧪 Sending test insight to verify frontend connectivity")
        await self._send_json({
            "type": "insight",
            "insight": test_insight,
        })
        
        # Note: We don't update _last_insight_time for test insight to avoid interfering
        # with the periodic task's timing
    
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
        
        # Cancel periodic insights generation task
        if self._insights_task and not self._insights_task.done():
            self._insights_task.cancel()
            try:
                await self._insights_task
            except asyncio.CancelledError:
                pass
        
        # Close transcription service
        if self._transcription_service:
            await self._transcription_service.close()
        
        # Generate comprehensive post-call analysis using PostCallAnalyzer
        summary_data = {}
        if self._transcript:
            # Get company and contact data for analysis
            company_data = None
            contact_data = None
            if self._meeting_data.get("company_id") and self.companies_dao:
                company_data = await self.companies_dao.get_company(str(self._meeting_data["company_id"]))
            if self._meeting_data.get("contact_ids") and self.contacts_dao:
                contact_id = str(self._meeting_data["contact_ids"][0])
                contact_data = await self.contacts_dao.get_contact(contact_id)
            
            # Get previous meetings
            previous_meetings = []
            if self._meeting_data.get("company_id"):
                previous = await self.meetings_dao.get_previous_meetings(
                    company_id=str(self._meeting_data["company_id"]),
                    exclude_meeting_id=self._db_meeting_id,
                )
                previous_meetings = previous[:3]
            
            company_name = company_data.get("name", "") if company_data else ""
            
            # Analyze meeting
            analysis = await self._post_call_analyzer.analyze_meeting(
                transcript=self._transcript,
                company_data=company_data,
                contact_data=contact_data,
                products=self._meeting_data.get("product_ids", []),
                previous_meetings=previous_meetings,
                company_name=company_name,
            )
            summary_data = analysis
            
            # Detect and save red flags
            if self._transcript:
                red_flags_raw = await self._red_flag_detector.detect_red_flags(self._transcript)
                if red_flags_raw and self._meeting_data.get("company_id"):
                    # Save red flags to company
                    await self.companies_dao.add_red_flags(
                        company_id=str(self._meeting_data["company_id"]),
                        meeting_id=self._db_meeting_id,
                        flags=red_flags_raw,
                        transcript_excerpts={rf.get("flag_name"): rf.get("evidence") for rf in red_flags_raw},
                    )
        
        # Fallback to insights engine if no transcript
        if not summary_data and self._insights_engine:
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
    meetings_dao = get_meetings_dao(loaded_config.connection_manager)
    companies_dao = get_companies_dao(loaded_config.connection_manager)
    contacts_dao = get_contacts_dao(loaded_config.connection_manager)
    
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

