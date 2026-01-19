"""
Lemlist Inbox Webhook Handler
Receives and processes webhook events from Lemlist
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import ORJSONResponse

from ai_agents.inbox.service import get_inbox_service
from ai_agents.tasks.service import get_task_service
from ai_agents.tasks.schemas import LemlistEventRequest
from config.loaded_config import loaded_config
from config.logging import logger


router = APIRouter(prefix="/webhook/lemlist", tags=["Webhooks"])


@router.post("/inbox")
async def receive_lemlist_webhook(
    request: Request,
    x_lemlist_signature: str = Header(None, alias="X-Lemlist-Signature")
):
    """
    Receive webhook events from Lemlist.
    
    Events we handle:
    - emailsOpened: First email open -> create call task
    - emailsReplied: Email reply received
    - emailsSent: Email sent
    - linkedinReplied: LinkedIn reply received
    - linkedinSent: LinkedIn message sent
    - whatsappReplied: WhatsApp reply received
    - whatsappSent: WhatsApp message sent
    """
    try:
        # Get raw body for signature verification
        body = await request.json()
        
        event_type = body.get("type")
        logger.info(f"Received Lemlist webhook", event_type=event_type)
        
        # Verify signature if configured
        webhook_secret = loaded_config.lemlist_webhook_secret
        if webhook_secret and x_lemlist_signature:
            # TODO: Implement signature verification
            # Lemlist uses HMAC-SHA256 for webhook signatures
            pass
        
        # Handle email open events - create call task
        if event_type == "emailsOpened":
            try:
                task_service = get_task_service()
                event_request = LemlistEventRequest(
                    type=event_type,
                    contactId=body.get("contactId"),
                    campaignId=body.get("campaignId"),
                    leadId=body.get("leadId"),
                    messageId=body.get("messageId"),
                    email=body.get("email"),
                )
                task = await task_service.create_task_from_lemlist_event(event_request)
                
                if task:
                    logger.info(f"Created call task from email open", task_id=task["_id"])
            except Exception as task_error:
                logger.warning(f"Failed to create call task from email open: {task_error}")
                # Don't fail the webhook - continue processing
        
        # Process the event for inbox
        service = get_inbox_service()
        success = await service.process_webhook_event(body)
        
        if success:
            return ORJSONResponse({
                "success": True,
                "message": "Event processed"
            })
        else:
            return ORJSONResponse({
                "success": False,
                "message": "Event not processed"
            }, status_code=200)  # Return 200 to avoid Lemlist retrying
        
    except Exception as e:
        logger.exception(f"Error processing Lemlist webhook: {e}")
        # Return 200 to avoid Lemlist retrying on our errors
        return ORJSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=200)


@router.get("/health")
async def webhook_health():
    """
    Health check endpoint for webhook.
    Lemlist may ping this to verify webhook is active.
    """
    return ORJSONResponse({
        "status": "healthy",
        "service": "lemlist-inbox-webhook"
    })


# ============ Webhook Registration Helper ============

async def register_lemlist_webhooks(base_url: str):
    """
    Register webhooks with Lemlist.
    Call this on application startup.
    
    Args:
        base_url: The base URL of your application (e.g., https://yourdomain.com)
    """
    try:
        from integrations.lemlist.lemlist_inbox_client import LemlistInboxClient
        
        client = LemlistInboxClient()
        
        # Check existing webhooks
        existing = await client.get_webhooks()
        target_url = f"{base_url}/webhook/lemlist/inbox"
        
        # Check if already registered
        for hook in existing:
            if hook.get("targetUrl") == target_url:
                logger.info(f"Lemlist webhook already registered", webhook_id=hook.get("_id"))
                return hook
        
        # Register new webhook
        events = [
            "emailsOpened",   # For task creation on first open
            "emailsReplied",
            "emailsSent",
            "linkedinReplied",
            "linkedinSent",
            "whatsappReplied",
            "whatsappSent"
        ]
        
        result = await client.register_webhook(target_url, events)
        logger.info(f"Registered Lemlist webhook", webhook_id=result.get("_id"))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to register Lemlist webhook: {e}")
        raise


