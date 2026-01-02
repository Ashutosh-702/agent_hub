"""
Inbox Service - Business logic for unified inbox
Handles sync with Lemlist, queries, and lead management
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from config.loaded_config import loaded_config
from config.logging import logger
from database.collection_dao.inbox_events import InboxEventsDao, InboxLeadsDao, InboxNotesDao
from integrations.lemlist.lemlist_inbox_client import LemlistInboxClient
from ai_agents.inbox.models import (
    Channel, Temperature, LeadStatus, Direction, StageStatus,
    LeadSummary, LeadDetail, EngagementEvent, Note, LastTouch,
    Company, Contact, Owner, EventMeta, AttentionReason,
    ListLeadsParams, ListLeadsResponse, UpdateLeadRequest
)


class InboxService:
    """Service for managing unified inbox"""

    def __init__(self):
        mongo_client = loaded_config.connection_manager.mongo_client
        self.events_dao = InboxEventsDao(mongo_client)
        self.leads_dao = InboxLeadsDao(mongo_client)
        self.notes_dao = InboxNotesDao(mongo_client)
        self.lemlist_client = LemlistInboxClient()

    async def initialize(self):
        """Initialize indexes"""
        await self.events_dao.create_indexes()
        await self.leads_dao.create_indexes()
        await self.notes_dao.create_indexes()
        logger.info("Inbox service initialized with indexes")

    # ============ Sync from Lemlist ============

    async def sync_from_lemlist(self, full_sync: bool = False) -> Dict[str, int]:
        """
        Sync inbox data from Lemlist API
        
        Args:
            full_sync: If True, fetch all data. If False, only fetch recent.
            
        Returns:
            Stats about synced data
        """
        logger.info(f"Starting Lemlist sync", full_sync=full_sync)
        
        stats = {
            "inboxes_fetched": 0,
            "leads_created": 0,
            "leads_updated": 0,
            "events_created": 0
        }

        try:
            # Fetch all inboxes from Lemlist
            inboxes = await self.lemlist_client.get_all_inboxes_paginated()
            stats["inboxes_fetched"] = len(inboxes)
            
            logger.info(f"Fetched {len(inboxes)} inboxes from Lemlist")

            for inbox in inboxes:
                try:
                    await self._process_lemlist_inbox(inbox, stats)
                except Exception as e:
                    logger.error(f"Error processing inbox {inbox.get('_id')}: {e}")
                    continue

            logger.info(f"Lemlist sync completed", stats=stats)
            return stats

        except Exception as e:
            logger.exception(f"Error during Lemlist sync: {e}")
            raise

    async def _process_lemlist_inbox(
        self,
        inbox: Dict[str, Any],
        stats: Dict[str, int]
    ):
        """Process a single Lemlist inbox and sync to database"""
        inbox_id = inbox.get("_id")
        contact = inbox.get("contact", {})
        channels = inbox.get("channels", [])
        
        # Generate a lead_id (use contact ID if available, else inbox ID)
        contact_id = contact.get("_id") or inbox.get("contactId")
        lead_id = f"lemlist_{contact_id}" if contact_id else f"lemlist_{inbox_id}"
        
        # Check if lead exists
        existing_lead = await self.leads_dao.get_lead(lead_id)
        
        # Build lead document
        lead_doc = {
            "lead_id": lead_id,
            "lemlist_inbox_id": inbox_id,
            "lemlist_contact_id": contact_id,
            "company": {
                "name": self._extract_company_from_email(contact.get("email", "")),
                "domain": self._extract_domain_from_email(contact.get("email", ""))
            },
            "contact": {
                "id": contact_id or inbox_id,
                "name": contact.get("fullName") or contact.get("email", "Unknown"),
                "email": contact.get("email"),
                "title": contact.get("title"),
                "linkedin": contact.get("linkedin"),
                "phone": contact.get("phone")
            },
            "owner": {
                "name": "Team",
                "email": "team@company.com"  # Default, can be updated
            },
            "channels_present": channels,
            "temperature": existing_lead.get("temperature", "cold") if existing_lead else "cold",
            "temperature_drivers": existing_lead.get("temperature_drivers", []) if existing_lead else [],
            "status": self._determine_status(inbox, existing_lead),
            "in_sequence": False,  # TODO: Check campaign enrollment
            "unread_count": self._calculate_unread(inbox),
            "last_synced_at": datetime.utcnow()
        }
        
        # Calculate last touch from inbox data
        if inbox.get("lastActivityAt"):
            last_channel = inbox.get("lastRepliedChannel") or (channels[0] if channels else "email")
            lead_doc["last_touch"] = {
                "channel": last_channel,
                "direction": "inbound" if inbox.get("haveReplies") else "outbound",
                "snippet": "Recent activity",  # Will be updated from messages
                "at": inbox.get("lastActivityAt")
            }
        
        # Upsert lead
        await self.leads_dao.upsert_lead(lead_doc)
        
        if existing_lead:
            stats["leads_updated"] += 1
        else:
            stats["leads_created"] += 1
        
        # Fetch and sync messages for this inbox
        await self._sync_inbox_messages(inbox_id, lead_id, stats)

    async def _sync_inbox_messages(
        self,
        inbox_id: str,
        lead_id: str,
        stats: Dict[str, int]
    ):
        """Sync messages for a Lemlist inbox"""
        try:
            messages = await self.lemlist_client.get_all_messages_for_inbox(inbox_id)
            
            events = []
            for msg in messages:
                event = self._convert_lemlist_message_to_event(msg, lead_id, inbox_id)
                if event:
                    events.append(event)
            
            if events:
                count = await self.events_dao.bulk_upsert_events(events)
                stats["events_created"] += count
                
                # Update last touch with actual message content
                latest_event = max(events, key=lambda e: e["at"])
                await self.leads_dao.update_last_touch(lead_id, {
                    "channel": latest_event["channel"],
                    "direction": latest_event["direction"],
                    "snippet": latest_event["content"][:100] if latest_event["content"] else "",
                    "at": latest_event["at"]
                })
                
        except Exception as e:
            logger.error(f"Error syncing messages for inbox {inbox_id}: {e}")

    def _convert_lemlist_message_to_event(
        self,
        message: Dict[str, Any],
        lead_id: str,
        inbox_id: str
    ) -> Optional[Dict[str, Any]]:
        """Convert Lemlist message to event document"""
        msg_id = message.get("_id")
        if not msg_id:
            return None
            
        channel = message.get("channel", "email")
        direction = message.get("direction", "outbound")
        
        # Determine content
        content = message.get("body") or message.get("text") or message.get("message") or ""
        if isinstance(content, str):
            content = content[:1000]  # Limit content length
        
        # Parse timestamp
        created_at = message.get("createdAt")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.utcnow()
        elif not created_at:
            created_at = datetime.utcnow()
        
        return {
            "lead_id": lead_id,
            "channel": channel,
            "direction": direction,
            "at": created_at,
            "title": self._generate_event_title(channel, direction),
            "content": content,
            "meta": {
                "subject": message.get("subject"),
                "message_status": message.get("status"),
                "lemlist_inbox_id": inbox_id,
                "lemlist_message_id": msg_id
            },
            "lemlist_inbox_id": inbox_id,
            "lemlist_message_id": msg_id,
            "read": direction == "outbound"  # Outbound messages are already "read"
        }

    def _generate_event_title(self, channel: str, direction: str) -> str:
        """Generate a title for an event"""
        action = "Received" if direction == "inbound" else "Sent"
        channel_name = channel.capitalize()
        
        if channel == "email":
            return f"Email {action.lower()}"
        elif channel == "linkedin":
            return f"LinkedIn message {action.lower()}"
        elif channel == "whatsapp":
            return f"WhatsApp message {action.lower()}"
        elif channel == "call":
            return "Call completed"
        
        return f"{channel_name} {action.lower()}"

    def _determine_status(
        self,
        inbox: Dict[str, Any],
        existing_lead: Optional[Dict[str, Any]]
    ) -> str:
        """Determine lead status based on inbox data"""
        if existing_lead and existing_lead.get("status"):
            # Keep existing status if set
            return existing_lead["status"]
        
        if inbox.get("haveReplies"):
            return LeadStatus.IN_CONVERSATION.value
        
        if inbox.get("lastActivityAt"):
            return LeadStatus.CONTACTED.value
        
        return LeadStatus.NEW.value

    def _calculate_unread(self, inbox: Dict[str, Any]) -> int:
        """Calculate unread count from inbox data"""
        users = inbox.get("users", [])
        for user in users:
            if not user.get("read"):
                return 1
        return 0

    def _extract_company_from_email(self, email: str) -> str:
        """Extract company name from email domain"""
        if not email or "@" not in email:
            return "Unknown Company"
        
        domain = email.split("@")[1]
        company = domain.split(".")[0]
        return company.capitalize()

    def _extract_domain_from_email(self, email: str) -> Optional[str]:
        """Extract domain from email"""
        if not email or "@" not in email:
            return None
        return email.split("@")[1]

    # ============ Webhook Processing ============

    async def process_webhook_event(self, event: Dict[str, Any]) -> bool:
        """
        Process incoming Lemlist webhook event
        
        Event types:
        - emailsReplied
        - emailsSent
        - emailsOpened
        - emailsClicked
        - emailsBounced
        - linkedinReplied
        - linkedinSent
        """
        event_type = event.get("type")
        logger.info(f"Processing Lemlist webhook event", event_type=event_type)
        
        try:
            # Map event type to channel and direction
            channel, direction = self._map_webhook_event_type(event_type)
            if not channel:
                logger.info(f"Ignoring unhandled event type: {event_type}")
                return False
            
            # Get or create lead
            contact_id = event.get("contactId")
            lead_id = f"lemlist_{contact_id}" if contact_id else None
            
            if not lead_id:
                logger.warning(f"No contact ID in webhook event")
                return False
            
            # Check if lead exists, if not trigger partial sync
            existing_lead = await self.leads_dao.get_lead(lead_id)
            if not existing_lead:
                # Try to find by lemlist contact ID
                existing_lead = await self.leads_dao.get_lead_by_lemlist_contact(contact_id)
                if existing_lead:
                    lead_id = existing_lead["lead_id"]
            
            # Create event document
            event_doc = {
                "lead_id": lead_id,
                "channel": channel,
                "direction": direction,
                "at": datetime.utcnow(),
                "title": self._generate_event_title(channel, direction),
                "content": event.get("text") or event.get("message") or event.get("subject") or "",
                "meta": {
                    "subject": event.get("subject"),
                    "lemlist_message_id": event.get("messageId")
                },
                "lemlist_message_id": event.get("messageId"),
                "read": direction == "outbound"
            }
            
            # Insert event
            await self.events_dao.upsert_event(event_doc)
            
            # Update lead
            if existing_lead:
                # Update last touch
                await self.leads_dao.update_last_touch(lead_id, {
                    "channel": channel,
                    "direction": direction,
                    "snippet": event_doc["content"][:100] if event_doc["content"] else "",
                    "at": datetime.utcnow()
                })
                
                # Add channel if new
                await self.leads_dao.add_channel(lead_id, channel)
                
                # Increment unread for inbound
                if direction == "inbound":
                    await self.leads_dao.increment_unread_count(lead_id)
                    
                    # Update status if was waiting
                    if existing_lead.get("status") in [LeadStatus.CONTACTED.value, LeadStatus.WAITING_ON_LEAD.value]:
                        await self.leads_dao.update_lead_status(lead_id, LeadStatus.IN_CONVERSATION.value)
            
            logger.info(f"Processed webhook event", lead_id=lead_id, channel=channel)
            return True
            
        except Exception as e:
            logger.exception(f"Error processing webhook event: {e}")
            return False

    def _map_webhook_event_type(self, event_type: str) -> tuple[Optional[str], Optional[str]]:
        """Map Lemlist webhook event type to channel and direction"""
        mapping = {
            "emailsReplied": ("email", "inbound"),
            "emailsSent": ("email", "outbound"),
            "linkedinReplied": ("linkedin", "inbound"),
            "linkedinSent": ("linkedin", "outbound"),
            "whatsappReplied": ("whatsapp", "inbound"),
            "whatsappSent": ("whatsapp", "outbound"),
        }
        return mapping.get(event_type, (None, None))

    # ============ Call/Meeting Events ============

    async def ingest_call_event(
        self,
        lead_id: str,
        duration_sec: int,
        transcript_snippet: str,
        meeting_id: Optional[str] = None,
        call_type: str = "call"
    ) -> str:
        """
        Ingest a call/meeting event from Client Calls module
        """
        event_doc = {
            "lead_id": lead_id,
            "channel": "call",
            "direction": "outbound",
            "at": datetime.utcnow(),
            "title": f"{'Meeting' if meeting_id else 'Call'} completed",
            "content": transcript_snippet[:1000] if transcript_snippet else "",
            "meta": {
                "call_duration_sec": duration_sec,
                "meeting_id": meeting_id
            },
            "read": True
        }
        
        event_id = await self.events_dao.upsert_event(event_doc)
        
        # Update lead
        existing_lead = await self.leads_dao.get_lead(lead_id)
        if existing_lead:
            await self.leads_dao.update_last_touch(lead_id, {
                "channel": "call",
                "direction": "outbound",
                "snippet": transcript_snippet[:100] if transcript_snippet else "Call completed",
                "at": datetime.utcnow()
            })
            await self.leads_dao.add_channel(lead_id, "call")
        
        logger.info(f"Ingested call event", lead_id=lead_id, event_id=event_id)
        return event_id

    # ============ Query Methods ============

    async def list_leads(self, params: ListLeadsParams) -> ListLeadsResponse:
        """List leads with filters and pagination"""
        leads, total = await self.leads_dao.search_leads(
            query=params.query,
            channel=params.channel.value if params.channel else None,
            temperature=params.temperature.value if params.temperature else None,
            status=params.status.value if params.status else None,
            in_sequence=params.in_sequence,
            stage_status=params.stage_status.value if params.stage_status else None,
            owner_email=params.owner_email,
            sort=params.sort,
            tab=params.tab,
            page=params.page,
            page_size=params.page_size
        )
        
        # Convert to LeadSummary models
        summaries = [self._doc_to_lead_summary(doc) for doc in leads]
        
        has_next = (params.page * params.page_size) < total
        
        return ListLeadsResponse(
            leads=summaries,
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=has_next
        )

    async def get_lead_detail(self, lead_id: str) -> Optional[LeadDetail]:
        """Get full lead detail with events and notes"""
        lead_doc = await self.leads_dao.get_lead(lead_id)
        if not lead_doc:
            return None
        
        # Get events
        event_docs = await self.events_dao.get_events_for_lead(lead_id, limit=100)
        events = [self._doc_to_event(doc) for doc in event_docs]
        
        # Get notes
        note_docs = await self.notes_dao.get_notes_for_lead(lead_id)
        notes = [self._doc_to_note(doc) for doc in note_docs]
        
        summary = self._doc_to_lead_summary(lead_doc)
        
        return LeadDetail(
            summary=summary,
            events=events,
            notes=notes
        )

    def _doc_to_lead_summary(self, doc: Dict[str, Any]) -> LeadSummary:
        """Convert MongoDB document to LeadSummary model"""
        company_data = doc.get("company", {})
        contact_data = doc.get("contact", {})
        owner_data = doc.get("owner", {})
        last_touch_data = doc.get("last_touch")
        sequence_data = doc.get("sequence")
        
        return LeadSummary(
            lead_id=doc.get("lead_id"),
            company=Company(
                name=company_data.get("name", "Unknown"),
                domain=company_data.get("domain")
            ),
            contact=Contact(
                id=contact_data.get("id", ""),
                name=contact_data.get("name", "Unknown"),
                title=contact_data.get("title"),
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                linkedin=contact_data.get("linkedin")
            ),
            owner=Owner(
                name=owner_data.get("name", "Unassigned"),
                email=owner_data.get("email", "")
            ),
            channels_present=[Channel(c) for c in doc.get("channels_present", []) if c in [e.value for e in Channel]],
            temperature=Temperature(doc.get("temperature", "cold")),
            temperature_drivers=doc.get("temperature_drivers", []),
            status=LeadStatus(doc.get("status", "new")),
            in_sequence=doc.get("in_sequence", False),
            sequence=None,  # TODO: Parse sequence data
            last_touch=LastTouch(
                channel=Channel(last_touch_data.get("channel", "email")),
                direction=Direction(last_touch_data.get("direction", "outbound")),
                snippet=last_touch_data.get("snippet", ""),
                at=last_touch_data.get("at") if isinstance(last_touch_data.get("at"), datetime) else datetime.utcnow()
            ) if last_touch_data else None,
            next_step_at=doc.get("next_step_at"),
            unread_count=doc.get("unread_count", 0)
        )

    def _doc_to_event(self, doc: Dict[str, Any]) -> EngagementEvent:
        """Convert MongoDB document to EngagementEvent model"""
        meta_data = doc.get("meta", {})
        
        return EngagementEvent(
            id=str(doc.get("_id", "")),
            lead_id=doc.get("lead_id", ""),
            channel=Channel(doc.get("channel", "email")),
            direction=Direction(doc.get("direction", "outbound")),
            at=doc.get("at") if isinstance(doc.get("at"), datetime) else datetime.utcnow(),
            title=doc.get("title"),
            content=doc.get("content", ""),
            meta=EventMeta(
                subject=meta_data.get("subject"),
                message_status=meta_data.get("message_status"),
                call_duration_sec=meta_data.get("call_duration_sec"),
                meeting_id=meta_data.get("meeting_id"),
                sequence=meta_data.get("sequence"),
                external_link=meta_data.get("external_link"),
                lemlist_inbox_id=meta_data.get("lemlist_inbox_id"),
                lemlist_message_id=meta_data.get("lemlist_message_id")
            ) if meta_data else None
        )

    def _doc_to_note(self, doc: Dict[str, Any]) -> Note:
        """Convert MongoDB document to Note model"""
        return Note(
            id=str(doc.get("_id", "")),
            at=doc.get("at") if isinstance(doc.get("at"), datetime) else datetime.utcnow(),
            author=doc.get("author", "Unknown"),
            text=doc.get("text", "")
        )

    # ============ Update Methods ============

    async def update_lead(
        self,
        lead_id: str,
        update: UpdateLeadRequest
    ) -> bool:
        """Update lead temperature and/or status"""
        success = True
        
        if update.temperature:
            result = await self.leads_dao.update_lead_temperature(
                lead_id,
                update.temperature.value,
                update.temperature_drivers
            )
            success = success and result
        
        if update.status:
            result = await self.leads_dao.update_lead_status(
                lead_id,
                update.status.value
            )
            success = success and result
        
        return success

    async def mark_lead_read(self, lead_id: str) -> bool:
        """Mark all events for a lead as read"""
        await self.events_dao.mark_events_read(lead_id)
        return await self.leads_dao.reset_unread_count(lead_id)

    async def add_note(self, lead_id: str, author: str, text: str) -> str:
        """Add a note to a lead"""
        return await self.notes_dao.add_note(lead_id, author, text)

    # ============ Attention Logic ============

    def compute_needs_attention(self, lead: LeadSummary) -> List[AttentionReason]:
        """Compute reasons why a lead needs attention"""
        reasons = []
        
        # Unread replies
        if lead.unread_count > 0:
            reasons.append(AttentionReason(
                type="unread_reply",
                message=f"{lead.unread_count} unread message{'s' if lead.unread_count > 1 else ''}"
            ))
        
        # Waiting on us
        if lead.status == LeadStatus.WAITING_ON_US:
            reasons.append(AttentionReason(
                type="waiting_on_us",
                message="Lead is waiting for your response"
            ))
        
        # Overdue sequence step
        if lead.in_sequence and lead.next_step_at:
            if lead.next_step_at < datetime.utcnow():
                reasons.append(AttentionReason(
                    type="overdue_step",
                    message="Sequence step is overdue"
                ))
        
        # Hot lead gone stale
        if lead.temperature == Temperature.HOT and lead.last_touch:
            days_since_touch = (datetime.utcnow() - lead.last_touch.at).days
            if days_since_touch > 3:
                reasons.append(AttentionReason(
                    type="hot_stale",
                    message=f"Hot lead with no activity for {days_since_touch} days"
                ))
        
        return reasons


# Singleton instance
_inbox_service: Optional[InboxService] = None


def get_inbox_service() -> InboxService:
    """Get or create inbox service instance"""
    global _inbox_service
    if _inbox_service is None:
        _inbox_service = InboxService()
    return _inbox_service

