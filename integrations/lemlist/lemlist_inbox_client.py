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
        self.email = loaded_config.lemlist_email
        self.http_session = loaded_config.http_session
        self.timeout = 30
        
        # Lemlist uses Basic auth with email:apikey
        auth_string = f"{self.email}:{self.api_key}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def get_team(self) -> Dict[str, Any]:
        """
        Fetch team information including user IDs
        
        GET /api/team
        
        Returns:
            {
                "_id": "team_id",
                "userIds": ["user_id1", "user_id2"],
                "name": "Team Name",
                ...
            }
        """
        url = f"{LEMLIST_BASE_URL}/team"
        
        try:
            logger.info("Fetching Lemlist team info")
            
            response = await self.http_session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                logger.info(
                    f"Fetched Lemlist team successfully",
                    team_name=result.get("name"),
                    user_count=len(result.get("userIds", []))
                )
                return result
            elif response.status == 401:
                logger.error("Lemlist API authentication failed")
                raise Exception("Lemlist API authentication failed. Check API key.")
            else:
                error_text = await response.text()
                logger.error(f"Lemlist API error: {response.status} - {error_text}")
                raise Exception(f"Lemlist API error: {response.status}")

        except Exception as e:
            logger.exception(f"Error fetching Lemlist team: {str(e)}")
            raise

    async def get_inboxes(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch all inbox conversations for a user
        
        GET /api/inbox?userId=xxx
        
        Note: userId is REQUIRED by Lemlist API
        
        Returns:
            {
                "data": [LemlistInbox],
                "pagination": {...}
            }
        """
        url = f"{LEMLIST_BASE_URL}/inbox"
        params = {
            "userId": user_id,
            "page": page,
            "limit": limit
        }

        try:
            logger.info(f"Fetching Lemlist inboxes", user_id=user_id, page=page, limit=limit)
            
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
        Fetch all inboxes with automatic pagination for all team users
        """
        all_inboxes = []
        seen_inbox_ids = set()
        
        # First get team info to get user IDs
        try:
            team = await self.get_team()
            user_ids = team.get("userIds", [])
            
            if not user_ids:
                logger.warning("No users found in team")
                return []
            
            logger.info(f"Fetching inboxes for {len(user_ids)} team users")
            
            # Fetch inboxes for each user
            for user_id in user_ids:
                page = 1
                limit = 50
                
                while True:
                    result = await self.get_inboxes(user_id=user_id, page=page, limit=limit)
                    
                    if result.get("rate_limited"):
                        logger.warning(f"Rate limited while fetching inboxes for user {user_id}")
                        break
                    
                    data = result.get("data", [])
                    
                    # Deduplicate by inbox ID
                    for inbox in data:
                        inbox_id = inbox.get("_id")
                        if inbox_id and inbox_id not in seen_inbox_ids:
                            seen_inbox_ids.add(inbox_id)
                            all_inboxes.append(inbox)
                    
                    pagination = result.get("pagination", {})
                    if not pagination.get("nextPage"):
                        break
                    
                    page += 1
            
            logger.info(f"Fetched {len(all_inboxes)} unique inboxes from all users")
            return all_inboxes
            
        except Exception as e:
            logger.exception(f"Error fetching all inboxes: {str(e)}")
            raise

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

    # ==================== Campaign Lead Enrollment APIs ====================
    
    async def get_campaigns(self) -> List[Dict[str, Any]]:
        """
        Fetch all campaigns from Lemlist
        
        GET /api/campaigns
        
        Returns a list of campaigns:
        [
            {
                "_id": "cam_abc123",
                "name": "Enterprise Outreach Q1",
                "labels": ["outreach", "enterprise"],
                ...
            }
        ]
        """
        url = f"{LEMLIST_BASE_URL}/campaigns"
        
        try:
            logger.info("Fetching Lemlist campaigns")
            
            response = await self.http_session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                logger.info(
                    f"Fetched Lemlist campaigns successfully",
                    count=len(result) if isinstance(result, list) else 0
                )
                return result if isinstance(result, list) else []
            elif response.status == 401:
                logger.error("Lemlist API authentication failed")
                raise Exception("Lemlist API authentication failed. Check API key.")
            elif response.status == 429:
                logger.warning("Lemlist API rate limit hit")
                return []
            else:
                error_text = await response.text()
                logger.error(f"Lemlist API error: {response.status} - {error_text}")
                raise Exception(f"Lemlist API error: {response.status}")

        except Exception as e:
            logger.exception(f"Error fetching Lemlist campaigns: {str(e)}")
            raise

    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Fetch a single campaign from Lemlist
        
        GET /api/campaigns/{campaignId}
        """
        url = f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}"
        
        try:
            logger.info(f"Fetching Lemlist campaign", campaign_id=campaign_id)
            
            response = await self.http_session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status == 200:
                result = await response.json()
                logger.info(f"Fetched Lemlist campaign successfully", campaign_id=campaign_id)
                return result
            elif response.status == 404:
                logger.warning(f"Lemlist campaign not found: {campaign_id}")
                return {}
            elif response.status == 401:
                logger.error("Lemlist API authentication failed")
                raise Exception("Lemlist API authentication failed. Check API key.")
            else:
                error_text = await response.text()
                logger.error(f"Lemlist API error: {response.status} - {error_text}")
                raise Exception(f"Lemlist API error: {response.status}")

        except Exception as e:
            logger.exception(f"Error fetching Lemlist campaign: {str(e)}")
            raise

    async def add_lead_to_campaign(
        self,
        campaign_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
        personalised_deck_link: Optional[str] = None,
        personalised_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a lead to a Lemlist campaign
        
        POST /api/campaigns/{campaignId}/leads/?version=v2
        
        Args:
            campaign_id: The Lemlist campaign ID
            email: Lead's email address
            first_name: Lead's first name
            last_name: Lead's last name
            company_name: Lead's company name
            personalised_deck_link: URL of the personalized deck PDF
            personalised_message: Content of the personalized message
            
        Returns:
            Lemlist API response with created lead info
        """
        url = f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}/leads/?version=v2"
        
        # Build payload - exact format as per Lemlist API v2
        payload: Dict[str, Any] = {
            "email": email
        }
        
        if first_name:
            payload["firstName"] = first_name
        if last_name:
            payload["lastName"] = last_name
        if company_name:
            payload["companyName"] = company_name
        if personalised_deck_link:
            payload["personalised_deck_link"] = personalised_deck_link
        if personalised_message:
            payload["personalised_message"] = personalised_message
        
        try:
            logger.info(
                f"Adding lead to Lemlist campaign",
                campaign_id=campaign_id,
                email=email
            )
            
            response = await self.http_session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status in [200, 201]:
                result = await response.json()
                logger.info(
                    f"Lead added to Lemlist campaign successfully",
                    campaign_id=campaign_id,
                    email=email,
                    lead_id=result.get("_id")
                )
                return {"success": True, "data": result}
            elif response.status == 409:
                # Lead already exists in campaign
                logger.warning(
                    f"Lead already exists in Lemlist campaign",
                    campaign_id=campaign_id,
                    email=email
                )
                return {"success": True, "data": {"alreadyExists": True, "email": email}}
            elif response.status == 401:
                logger.error("Lemlist API authentication failed")
                return {"success": False, "error": "Authentication failed"}
            elif response.status == 429:
                logger.warning("Lemlist API rate limit hit")
                return {"success": False, "error": "Rate limit exceeded", "retry": True}
            else:
                error_text = await response.text()
                logger.error(
                    f"Lemlist add lead error: {response.status} - {error_text}",
                    campaign_id=campaign_id,
                    email=email
                )
                return {"success": False, "error": f"API error: {response.status}"}

        except Exception as e:
            logger.exception(f"Error adding lead to Lemlist campaign: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_leads_to_campaign_batch(
        self,
        campaign_id: str,
        leads: List[Dict[str, Any]],
        rate_limit_delay: float = 0.2
    ) -> Dict[str, Any]:
        """
        Add multiple leads to a Lemlist campaign with rate limiting
        
        Args:
            campaign_id: The Lemlist campaign ID
            leads: List of lead data dictionaries, each containing:
                - email (required)
                - first_name, last_name, company_name (optional)
                - personalised_deck_link, personalised_message (optional)
            rate_limit_delay: Delay between API calls in seconds
            
        Returns:
            Summary of enrollment results
        """
        import asyncio
        
        results = {
            "total": len(leads),
            "success": 0,
            "failed": 0,
            "already_exists": 0,
            "rate_limited": 0,
            "errors": [],
            "enrolled_leads": []
        }
        
        for i, lead in enumerate(leads):
            email = lead.get("email")
            if not email:
                results["failed"] += 1
                results["errors"].append({"index": i, "error": "Missing email"})
                continue
            
            response = await self.add_lead_to_campaign(
                campaign_id=campaign_id,
                email=email,
                first_name=lead.get("first_name"),
                last_name=lead.get("last_name"),
                company_name=lead.get("company_name"),
                personalised_deck_link=lead.get("personalised_deck_link"),
                personalised_message=lead.get("personalised_message")
            )
            
            if response.get("success"):
                lead_id = response.get("data", {}).get("_id")
                if response.get("data", {}).get("alreadyExists"):
                    results["already_exists"] += 1
                    # Also add already existing leads to enrolled_leads so we can track them
                    results["enrolled_leads"].append({
                        "email": email,
                        "lead_id": lead_id,
                        "already_existed": True
                    })
                else:
                    results["success"] += 1
                    results["enrolled_leads"].append({
                        "email": email,
                        "lead_id": lead_id
                    })
            else:
                if response.get("retry"):
                    results["rate_limited"] += 1
                    # Could implement exponential backoff here
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "email": email,
                        "error": response.get("error")
                    })
            
            # Rate limiting delay between calls
            if i < len(leads) - 1:
                await asyncio.sleep(rate_limit_delay)
        
        logger.info(
            f"Batch lead enrollment complete",
            campaign_id=campaign_id,
            total=results["total"],
            success=results["success"],
            failed=results["failed"],
            already_exists=results["already_exists"]
        )
        
        return results

