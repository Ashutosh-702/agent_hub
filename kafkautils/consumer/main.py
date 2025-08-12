"""Main entry point for leadgen Kafka consumer."""
import asyncio
import os
from kafkautils.consumer.consumer import start_eventbridge_consumer
from kafkautils.consumer.kafka_config import get_available_consumer_types

async def main():
    """Main entry point for leadgen consumer."""
    consumer_type = os.getenv("CONSUMER_TYPE", "leadgen_batch_consumer")
    
    print(f"🚀 Starting Leadgen Kafka Consumer...")
    print(f"   📡 Consumer type: {consumer_type}")
    print(f"   📨 Listening for company search requests...")
    print(f"   🌉 Using EventBridge abstraction")
    
    # Validate consumer type
    available_types = get_available_consumer_types()
    if consumer_type not in available_types:
        print(f"❌ Unknown consumer type: {consumer_type}")
        print(f"   Available consumer types: {available_types}")
        print("   Set CONSUMER_TYPE environment variable")
        print("   Examples:")
        for consumer in available_types:
            print(f"     CONSUMER_TYPE={consumer}")
        return
    
    try:
        await start_eventbridge_consumer(consumer_type)
    except KeyboardInterrupt:
        print("\n🔒 Consumer stopped by user")
    except Exception as e:
        print(f"❌ Consumer error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 