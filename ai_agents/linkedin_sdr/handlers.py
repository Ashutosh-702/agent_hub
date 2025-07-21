"""LinkedIn SDR Kafka message handlers (Following Vector's Pattern)."""
from typing import Any

from .models.batch import get_batch
from .routes.batch_processor import process_batch_with_limit

async def linkedin_batch_processing_handler(message: Any):
    """
    LinkedIn batch processing handler (Following Vector's handler pattern)
    This function is called by EventBridge for each Kafka message
    
    Similar to Vector's shipment_create_ingestion, user_ingestion, etc.
    """
    try:
        print(f"📨 Received EventBridge message: partition={getattr(message, 'partition', 'unknown')}, offset={getattr(message, 'offset', 'unknown')}")
        
        # Extract payload from EventBridge message
        payload = message.value if hasattr(message, 'value') else message
        
        if not isinstance(payload, dict) or not payload:
            print("❌ Invalid message payload")
            return
        
        batch_id = payload.get("batch_id")
        action = payload.get("action")
        
        if not batch_id:
            print("❌ Missing batch_id in message")
            return
        
        if action != "process_batch":
            print(f"❌ Unknown action: {action}")
            return
        
        print(f"📨 Processing Chronos message: batch_id={batch_id}, action={action}")
        
        # Process the batch using our existing logic
        await _process_linkedin_batch(batch_id)
        
    except Exception as e:
        print(f"❌ Error handling EventBridge message: {e}")
        # Re-raise to let EventBridge handle retry logic
        raise

async def _process_linkedin_batch(batch_id: str):
    """
    Internal helper to process a single LinkedIn URL from the batch
    The cron job will automatically trigger again based on the cron expression
    
    Private helper function (like Vector's internal processing functions)
    """
    try:
        print(f"🔄 Processing batch: {batch_id}")
        
        # Check if batch is already completed
        batch = await get_batch(batch_id)
        if not batch:
            print(f"❌ Batch {batch_id} not found")
            return
            
        if batch.get("is_completed", False):
            print(f"✅ Batch {batch_id} already completed - no more processing needed")
            return
        
        print(f"📝 Batch {batch_id} is active, processing next LinkedIn URL...")
        
        # Process 1 LinkedIn URL
        result = await process_batch_with_limit(batch_id, limit=1)
        
        print(f"📊 Processing result: {result['processed']} processed, {result['successful']} successful, {result['failed']} failed")
        
        # Check completion status after processing
        if result["batch_completed"]:
            print(f"🎉 Batch {batch_id} just completed!")
            print(f"📝 Note: Cron job will continue triggering but no more URLs to process")
        else:
            print(f"⏳ Batch {batch_id} still has URLs pending")
            print(f"🔄 Cron job will automatically trigger again based on expression")
            
    except Exception as e:
        print(f"❌ Error processing batch {batch_id}: {e}")
        # Re-raise to let EventBridge handle retry logic
        raise

# Future handlers ready to uncomment (Vector's "Uncomment to Add" Pattern)
# async def linkedin_shipment_processing_handler(message: Any):
#     """Handler for LinkedIn shipment processing messages"""
#     print(f"📦 Processing LinkedIn shipment message")
#     # Add shipment processing logic here
#     pass
#
# async def linkedin_user_processing_handler(message: Any):
#     """Handler for LinkedIn user processing messages"""
#     print(f"👤 Processing LinkedIn user message")
#     # Add user processing logic here
#     pass 