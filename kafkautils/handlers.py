"""Message handlers for leadgen Kafka consumers."""
from typing import Any
from ai_agents.core_sdr.src.cli.main import process_company_search
from database.connection_manager import ConnectionManager
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from bson import ObjectId

async def initialize_consumer_connections():
    """Initialize database connections for consumer context."""
    if not loaded_config.connection_manager:
        print("🔄 Initializing database connection for consumer...")
        loaded_config.connection_manager = ConnectionManager(
            mongo_uri=loaded_config.mongo_uri, 
            db_name="linkedin_sdr"
        )
        print("✅ Database connection initialized for consumer")

async def leadgen_batch_processing_handler(message: Any):
    """
    Default handler for leadgen batch processing messages.
    This gets replaced by EventBridge consumer with custom handler.
    """
    try:
        # Try different ways to extract the payload
        payload = None
        if hasattr(message, 'value'):
            payload = message.value
        elif hasattr(message, 'data'):
            payload = message.data
        elif isinstance(message, dict):
            payload = message
        else:
            payload = message
        
        print(f"📨 Received leadgen message: {payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'}")
        
        if not isinstance(payload, dict) or not payload:
            print("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")  # Now we get campaign_id instead of form_data
        
        if not request_id or not campaign_id:
            print("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_company_search":
            print(f"❌ Unknown action: {action}")
            return
        
        print(f"🔄 Processing company search: {request_id}")
        
        # Process the company search using campaign_id
        await process_leadgen_message(request_id, campaign_id)
        
    except Exception as e:
        print(f"❌ Error handling leadgen message: {e}")
        import traceback
        traceback.print_exc()
        raise

async def process_leadgen_message(request_id: str, campaign_id: str):
    """Process a single leadgen company search request using campaign_id."""
    try:
        print(f"🔍 Processing request: {request_id}")
        print(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        # Fetch campaign data from database using campaign_id
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(ObjectId(campaign_id))
        
        if not campaign_data:
            print(f"❌ Campaign not found: {campaign_id}")
            return
        
        print(f"🔍 DEBUG: Campaign data structure: {campaign_data}")
        print(f"📊 Industry: {campaign_data.get('segmentation', {}).get('industry', 'Unknown')}")
        print(f"📍 Location: {campaign_data.get('target', {}).get('location', {}).get('names', 'Unknown')}")
        
        # Call the company search process with campaign data
        result = await process_company_search(campaign_data)
        
        print(f"✅ Completed processing: {request_id}")
        print(f"📝 Result: {result}")
        
    except Exception as e:
        print(f"❌ Error processing request {request_id}: {e}")
        raise 