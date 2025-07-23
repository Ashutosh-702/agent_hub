import json
import os
from aiokafka import AIOKafkaConsumer
from typing import Dict, Any

from models.batch import get_batch
from routes.batch_processor import process_batch_with_limit

class LinkedInBatchConsumer:
    def __init__(self):
        self.kafka_servers = os.getenv("KAFKA_BROKER_LIST", "localhost:9092")
        self.topic = "linkedin-batch-processing"  # Topic that Chronos sends to
        self.group_id = "linkedin-batch-consumer-group"
        
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_servers,
            group_id=self.group_id,
            value_deserializer=self._deserialize_message,
            auto_offset_reset='latest'
        )
        
        print(f"🤖 LinkedIn Batch Consumer initialized")
        print(f"   📡 Kafka servers: {self.kafka_servers}")
        print(f"   📂 Topic: {self.topic}")
        print(f"   👥 Group ID: {self.group_id}")

    def _deserialize_message(self, message_bytes):
        """Deserialize Kafka message from bytes to dict"""
        try:
            return json.loads(message_bytes.decode('utf-8'))
        except Exception as e:
            print(f"❌ Error deserializing message: {e}")
            return None

    async def process_chronos_message(self, batch_id: str):
        """
        Process a single LinkedIn URL from the batch
        The cron job will automatically trigger again based on the cron expression
        """
        try:
            print(f"🔄 Processing batch: {batch_id}")
            
            # Check if batch is already completed. Implementing as a check, so that if 
            # the batch has been completed manually by the user, then we don't need to schedule it again.
            batch = await get_batch(batch_id)
            if not batch:
                print(f"❌ Batch {batch_id} not found")
                return
                
            if batch.get("is_completed", False):
                print(f"✅ Batch {batch_id} already completed - no more processing needed")
                return  # 🛑 STOP HERE - Batch already done
            
            print(f"📝 Batch {batch_id} is active, processing next LinkedIn URL...")
            
            # Process 1 LinkedIn URL
            result = await process_batch_with_limit(batch_id, limit=1)
            
            print(f"📊 Processing result: {result['processed']} processed, {result['successful']} successful, {result['failed']} failed")
            
            # Check completion status after processing
            if result["batch_completed"]:
                print(f"🎉 Batch {batch_id} just completed!")
                print(f"📝 Note: Cron job will continue triggering but no more URLs to process")
                return  # 🛑 Batch is done (cron job will still trigger but will hit the completed check above)
            else:
                print(f"⏳ Batch {batch_id} still has URLs pending")
                print(f"🔄 Cron job will automatically trigger again based on expression")
                
        except Exception as e:
            print(f"❌ Error processing batch {batch_id}: {e}")

    async def handle_message(self, message):
        """Handle incoming Kafka message from Chronos"""
        try:
            payload = message.value
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
            
            print(f"📨 Received Chronos message: batch_id={batch_id}, action={action}")
            
            # Process the batch
            await self.process_chronos_message(batch_id)
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")

    async def start_consuming(self):
        """Start consuming messages from Kafka"""
        print("🚀 Starting LinkedIn Batch Consumer...")
        print("   📡 Connecting to Kafka...")
        
        await self.consumer.start()
        
        try:
            print("✅ Connected to Kafka successfully!")
            print("   👂 Listening for Chronos batch processing messages...")
            print(f"   📂 Topic: {self.topic}")
            
            async for message in self.consumer:
                print(f"📨 Received message: partition={message.partition}, offset={message.offset}")
                await self.handle_message(message)
                
        except Exception as e:
            print(f"❌ Error in consumer loop: {e}")
        finally:
            print("🛑 Stopping Kafka consumer...")
            await self.consumer.stop()

async def start_batch_consumer():
    """Entry point to start the LinkedIn Batch Consumer"""
    print("🤖 Starting LinkedIn Batch Consumer...")
    consumer = LinkedInBatchConsumer()
    await consumer.start_consuming() 