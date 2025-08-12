"""Test script for leadgen EventBridge producer using pigeon pattern."""
import asyncio
import json
import uuid
from database.connection_manager import ConnectionManager
from kafkautils.producer.event_helpers import emit_event_helper, create_company_search_event
from kafkautils.constants import LEADGEN_BATCH_PROCESSING

async def test_pigeon_pattern_producer():
    """Test the pigeon pattern EventBridge producer."""
    print("🧪 Testing Leadgen EventBridge Producer (Pigeon Pattern)...")
    
    # Sample form data
    sample_form_data = {
        "web_prompt": "Find engineering companies",
        "persona_prompt": "Target CTOs and Engineering Managers",
        "industry": "Software Engineering",
        "employee_count": "50-200",
        "revenue_min": "1000000",
        "revenue_max": "10000000",
        "location_type": "country",
        "location": "United States",
        "keywords": "software engineering, technology",
        "categories": "B2B Software",
        "currency": "USD",
        "hubspot_email": "test@example.com",
        "product_name": "AI Agent Platform",
        "business_team": "Sales",
        "user_email": "user@example.com"
    }
    
    connection_manager = None
    try:
        # Initialize connection manager (like in the API)
        connection_manager = ConnectionManager(mongo_uri="mongodb://localhost:27017", db_name="test")
        await connection_manager.setup_eventbridge_producer()
        
        # Create event
        request_id = str(uuid.uuid4())
        event = create_company_search_event(sample_form_data, request_id)
        
        # Test direct emit using pigeon pattern
        await emit_event_helper(
            event_emitter=connection_manager.event_emitter,
            topics=[LEADGEN_BATCH_PROCESSING],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "test": True}
        )
        
        print(f"✅ Pigeon pattern test successful!")
        print(f"📊 Request ID: {request_id}")
        
    except Exception as e:
        print(f"❌ Pigeon pattern test failed: {e}")
        raise
    finally:
        # Cleanup
        if connection_manager:
            await connection_manager.close_connections()

async def main():
    """Main entry point for pigeon pattern testing."""
    await test_pigeon_pattern_producer()
    print("✅ Pigeon pattern test completed")

if __name__ == "__main__":
    asyncio.run(main()) 