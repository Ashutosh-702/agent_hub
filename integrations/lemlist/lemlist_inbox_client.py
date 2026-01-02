"""
Lemlist Inbox API Client
Handles all communication with Lemlist's Inbox API endpoints
"""
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.loaded_config import loaded_config
from config.logging import logger

LEMLIST_BASE_URL = "https://api.lemlist.com/api"


class LemlistInboxClient:
    """Client for Lemlist Inbox API operations"""

    def __init__(self):
        self.api_key = loaded_config.lemlist_api_key
        self.http_session = loaded_config.http_session
        self.timeout = 30
        
        # Lemlist uses Basic auth with API key as password
        auth_string = f":{self.api_key}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def get_inboxes(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch all inbox conversations
        
        GET /api/inbox
        
        Returns:
            {
                "data": [LemlistInbox],
                "pagination": {...}
            }
        """
        url = f"{LEMLIST_BASE_URL}/inbox"
        params = {
            "page": page,
            "limit": limit
        }
        if user_id:
            params["userId"] = user_id

        try:
            logger.info(f"Fetching Lemlist inboxes", page=page, limit=limit)
            
            response = await self.http_session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                logger.info(
                    f"Fetched Lemlist inboxes successfully",
                    count=len(result.get("data", [])),
                    total=result.get("pagination", {}).get("totalItems", 0)
                )
                return result
            elif response.status == 401:
                logger.error("Lemlist API authentication failed")
                raise Exception("Lemlist API authentication failed. Check API key.")
            elif response.status == 429:
                logger.warning("Lemlist API rate limit hit")
                return {"data": [], "pagination": None, "rate_limited": True}
            else:
                error_text = await response.text()
                logger.error(f"Lemlist API error: {response.status} - {error_text}")
                raise Exception(f"Lemlist API error: {response.status}")

        except Exception as e:
            logger.exception(f"Error fetching Lemlist inboxes: {str(e)}")
            raise

    async def get_inbox_messages(
        self,
        inbox_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch messages for a specific inbox conversation
        
        GET /api/inbox/{inboxId}/messages
        
        Returns:
            {
                "data": [LemlistMessage],
                "pagination": {...}
            }
        """
        url = f"{LEMLIST_BASE_URL}/inbox/{inbox_id}/messages"
        params = {
            "page": page,
            "limit": limit
        }

        try:
            logger.info(f"Fetching Lemlist inbox messages", inbox_id=inbox_id)
            
            response = await self.http_session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                logger.info(
                    f"Fetched Lemlist messages successfully",
                    inbox_id=inbox_id,
                    count=len(result.get("data", []))
                )
                return result
            elif response.status == 404:
                logger.warning(f"Lemlist inbox not found: {inbox_id}")
                return {"data": [], "pagination": None}
            elif response.status == 429:
                logger.warning("Lemlist API rate limit hit")
                return {"data": [], "pagination": None, "rate_limited": True}
            else:
                error_text = await response.text()
                logger.error(f"Lemlist API error: {response.status} - {error_text}")
                raise Exception(f"Lemlist API error: {response.status}")

        except Exception as e:
            logger.exception(f"Error fetching Lemlist messages: {str(e)}")
            raise

    async def send_email(
        self,
        inbox_id: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Send an email via Lemlist inbox
        
        POST /api/inbox/{inboxId}/email
        """
        url = f"{LEMLIST_BASE_URL}/inbox/{inbox_id}/email"
        payload = {
            "subject": subject,
            "body": body
        }

        try:
            logger.info(f"Sending email via Lemlist", inbox_id=inbox_id)
            
            response = await self.http_session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status in [200, 201]:
                result = await response.json()
                logger.info(f"Email sent successfully via Lemlist", inbox_id=inbox_id)
                return result
            else:
                error_text = await response.text()
                logger.error(f"Lemlist send email error: {response.status} - {error_text}")
                raise Exception(f"Failed to send email: {response.status}")

        except Exception as e:
            logger.exception(f"Error sending email via Lemlist: {str(e)}")
            raise

    async def send_linkedin_message(
        self,
        inbox_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a LinkedIn message via Lemlist inbox
        
        POST /api/inbox/{inboxId}/linkedin
        """
        url = f"{LEMLIST_BASE_URL}/inbox/{inbox_id}/linkedin"
        payload = {
            "message": message
        }

        try:
            logger.info(f"Sending LinkedIn message via Lemlist", inbox_id=inbox_id)
            
            response = await self.http_session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status in [200, 201]:
                result = await response.json()
                logger.info(f"LinkedIn message sent successfully", inbox_id=inbox_id)
                return result
            else:
                error_text = await response.text()
                logger.error(f"Lemlist send LinkedIn error: {response.status} - {error_text}")
                raise Exception(f"Failed to send LinkedIn message: {response.status}")

        except Exception as e:
            logger.exception(f"Error sending LinkedIn message via Lemlist: {str(e)}")
            raise

    async def send_whatsapp_message(
        self,
        inbox_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Lemlist inbox
        
        POST /api/inbox/{inboxId}/whatsapp
        """
        url = f"{LEMLIST_BASE_URL}/inbox/{inbox_id}/whatsapp"
        payload = {
            "message": message
        }

        try:
            logger.info(f"Sending WhatsApp message via Lemlist", inbox_id=inbox_id)
            
            response = await self.http_session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status in [200, 201]:
                result = await response.json()
                logger.info(f"WhatsApp message sent successfully", inbox_id=inbox_id)
                return result
            else:
                error_text = await response.text()
                logger.error(f"Lemlist send WhatsApp error: {response.status} - {error_text}")
                raise Exception(f"Failed to send WhatsApp message: {response.status}")

        except Exception as e:
            logger.exception(f"Error sending WhatsApp message via Lemlist: {str(e)}")
            raise

    async def register_webhook(
        self,
        target_url: str,
        events: List[str] = None
    ) -> Dict[str, Any]:
        """
        Register a webhook to receive Lemlist events
        
        POST /api/hooks
        
        Events can include:
        - emailsSent
        - emailsOpened
        - emailsClicked
        - emailsReplied
        - emailsBounced
        - linkedinSent
        - linkedinReplied
        etc.
        """
        url = f"{LEMLIST_BASE_URL}/hooks"
        
        if events is None:
            # Default events we care about for inbox
            events = [
                "emailsReplied",
                "emailsSent",
                "linkedinReplied",
                "linkedinSent",
            ]

        payload = {
            "targetUrl": target_url,
            "events": events
        }

        try:
            logger.info(f"Registering Lemlist webhook", target_url=target_url, events=events)
            
            response = await self.http_session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status in [200, 201]:
                result = await response.json()
                logger.info(f"Webhook registered successfully", webhook_id=result.get("_id"))
                return result
            else:
                error_text = await response.text()
                logger.error(f"Lemlist webhook registration error: {response.status} - {error_text}")
                raise Exception(f"Failed to register webhook: {response.status}")

        except Exception as e:
            logger.exception(f"Error registering Lemlist webhook: {str(e)}")
            raise

    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get all registered webhooks
        
        GET /api/hooks
        """
        url = f"{LEMLIST_BASE_URL}/hooks"

        try:
            response = await self.http_session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Lemlist get webhooks error: {response.status} - {error_text}")
                return []

        except Exception as e:
            logger.exception(f"Error getting Lemlist webhooks: {str(e)}")
            return []

    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook
        
        DELETE /api/hooks/{hookId}
        """
        url = f"{LEMLIST_BASE_URL}/hooks/{webhook_id}"

        try:
            response = await self.http_session.delete(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status in [200, 204]:
                logger.info(f"Webhook deleted successfully", webhook_id=webhook_id)
                return True
            else:
                error_text = await response.text()
                logger.error(f"Lemlist delete webhook error: {response.status} - {error_text}")
                return False

        except Exception as e:
            logger.exception(f"Error deleting Lemlist webhook: {str(e)}")
            return False

    async def get_all_inboxes_paginated(self) -> List[Dict[str, Any]]:
        """
        Fetch all inboxes with automatic pagination
        """
        all_inboxes = []
        page = 1
        limit = 50

        while True:
            result = await self.get_inboxes(page=page, limit=limit)
            
            if result.get("rate_limited"):
                logger.warning("Rate limited while fetching all inboxes")
                break
                
            data = result.get("data", [])
            all_inboxes.extend(data)
            
            pagination = result.get("pagination", {})
            if not pagination.get("nextPage"):
                break
                
            page += 1

        return all_inboxes

    async def get_all_messages_for_inbox(self, inbox_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all messages for an inbox with automatic pagination
        """
        all_messages = []
        page = 1
        limit = 50

        while True:
            result = await self.get_inbox_messages(inbox_id, page=page, limit=limit)
            
            if result.get("rate_limited"):
                logger.warning(f"Rate limited while fetching messages for inbox {inbox_id}")
                break
                
            data = result.get("data", [])
            all_messages.extend(data)
            
            pagination = result.get("pagination", {})
            if not pagination.get("nextPage"):
                break
                
            page += 1

        return all_messages

