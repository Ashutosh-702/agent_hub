import asyncio
from eventbridge.consumer import setup_and_start_consumer
from eventbridge.health import _healthz, _readyz
from typing import Any

from linkedin_sdr.models.batch import get_batch
from linkedin_sdr.routes.batch_processor import process_batch_with_limit
from linkedin_sdr.kafka_config import get_consumer_config

class LinkedInEventBridgeConsumer:
    """LinkedIn batch consumer using EventBridge abstraction"""
    
    def __init__(self, consumer_type: str = "linkedin_batch_consumer"):
        self.consumer_type = consumer_type
        self.consumer_config = get_consumer_config(consumer_type)
        
        print(f"🤖 LinkedIn EventBridge Consumer initialized")
        print(f"   📡 Kafka servers: {self.consumer_config['consumer_config']['bootstrap.servers']}")
        print(f"   📂 Topic: linkedin-batch-processing")
        print(f"   👥 Group ID: {self.consumer_config['consumer_config']['group.id']}")
        print(f"   🎯 Consumer type: {consumer_type}")
        print(f"   🔧 Service name: {self.consumer_config['service_name']}")

    async def linkedin_message_handler(self, message: Any):
        """
        EventBridge message handler for LinkedIn batch processing
        This function is called by EventBridge for each Kafka message
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
            await self.process_chronos_message(batch_id)
            
        except Exception as e:
            print(f"❌ Error handling EventBridge message: {e}")
            # Re-raise to let EventBridge handle retry logic
            raise

    async def process_chronos_message(self, batch_id: str):
        """
        Process a single LinkedIn URL from the batch
        The cron job will automatically trigger again based on the cron expression
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

    async def start_consuming(self):
        """Start consuming messages using EventBridge"""
        print("🚀 Starting LinkedIn EventBridge Consumer...")
        
        try:
            # Set the message handler in the topics configuration (Vector's pattern)
            topics_config = self.consumer_config["topics_configurations"]
            for topic_name, topic_config in topics_config.items():
                topic_config["tasks"] = [self.linkedin_message_handler]
                print(f"   📂 Set handler for topic: {topic_name}")
            
            print("   📡 Connecting to Kafka via EventBridge...")
            print(f"   👂 Listening for Chronos batch processing messages...")
            print(f"   ⚙️  Consumer config: {self.consumer_config['service_name']}")
            
            # Start health check endpoints
            print("   ❤️ Starting health check endpoints...")
            asyncio.create_task(_healthz())
            asyncio.create_task(_readyz())
            
            # Start EventBridge consumer - this will block and handle messages
            await setup_and_start_consumer(self.consumer_config)
            
        except Exception as e:
            print(f"❌ Error starting EventBridge consumer: {e}")
            raise

async def start_eventbridge_consumer(consumer_type: str = "linkedin_batch_consumer"):
    """Entry point to start the LinkedIn EventBridge Consumer"""
    print("🤖 Starting LinkedIn EventBridge Consumer...")
    consumer = LinkedInEventBridgeConsumer(consumer_type=consumer_type)
    await consumer.start_consuming() 