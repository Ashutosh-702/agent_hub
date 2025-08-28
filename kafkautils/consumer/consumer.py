"""EventBridge consumer for leadgen service."""
import asyncio
from eventbridge.consumer import setup_and_start_consumer
from eventbridge.health import _healthz, _readyz
from typing import Any
from kafkautils.consumer.kafka_config import get_consumer_config
from kafkautils.handlers import process_leadgen_message

class LeadgenEventBridgeConsumer:
    """Leadgen batch consumer using EventBridge abstraction."""
    
    def __init__(self, consumer_type: str = "leadgen_batch_consumer"):
        self.consumer_type = consumer_type
        self.consumer_config = get_consumer_config(consumer_type)
        
        print(f"🤖 Leadgen EventBridge Consumer initialized")
        print(f"   📡 Kafka servers: {self.consumer_config['consumer_config']['bootstrap_servers']}")
        print(f"   📂 Topic: {list(self.consumer_config['topics_configurations'].keys())[0]}")  # Show actual topic
        print(f"   👥 Group ID: {self.consumer_config['consumer_config']['group_id']}")
        print(f"   🎯 Consumer type: {consumer_type}")
        print(f"   🔧 Service name: {self.consumer_config['service_name']}")

    async def leadgen_message_handler(self, message: Any):
        """
        EventBridge message handler for leadgen batch processing.
        This function is called by EventBridge for each Kafka message.
        """
        try:
            print(f"📨 Received EventBridge message: partition={getattr(message, 'partition', 'unknown')}, offset={getattr(message, 'offset', 'unknown')}")
            
            # Extract payload from EventBridge message
            raw_message = message.value if hasattr(message, 'value') else message
            
            # EventBridge wraps our message in a 'payload' field
            if isinstance(raw_message, dict) and 'payload' in raw_message:
                payload = raw_message['payload']
            else:
                payload = raw_message
            
            if not isinstance(payload, dict) or not payload:
                print("❌ Invalid message payload")
                return
            
            request_id = payload.get("request_id")
            action = payload.get("action")
            campaign_id = payload.get("campaign_id")  # Updated to look for campaign_id
            
            if not request_id or not campaign_id:  # Updated validation
                print("❌ Missing request_id or campaign_id in message")
                return
            
            if action != "process_company_search":
                print(f"❌ Unknown action: {action}")
                return
            
            print(f"✅ Processing leadgen message: request_id={request_id}, action={action}")
            
            # Call the processing function
            await process_leadgen_message(request_id, campaign_id)
            
        except Exception as e:
            print(f"❌ Error in leadgen message handler: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def start_consuming(self):
        """Start consuming messages using EventBridge."""
        print("🚀 Starting Leadgen EventBridge Consumer...")
        
        try:
            # Set the message handler in the topics configuration
            topics_config = self.consumer_config["topics_configurations"]
            for topic_name, topic_config in topics_config.items():
                # Only set default handler if no handler is already configured
                if "tasks" not in topic_config or not topic_config["tasks"]:
                    topic_config["tasks"] = [self.leadgen_message_handler]
                    print(f"   📂 Set default handler for topic: {topic_name}")
                else:
                    print(f"   📂 Using configured handler for topic: {topic_name}")
                    print(f"      Handler: {topic_config['tasks'][0].__name__ if topic_config['tasks'] else 'None'}")
            
            print("   📡 Connecting to Kafka via EventBridge...")
            print(f"   👂 Listening for leadgen company search messages...")
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

async def start_eventbridge_consumer(consumer_type: str = "leadgen_batch_consumer"):
    """Entry point to start the Leadgen EventBridge Consumer."""
    print("🤖 Starting Leadgen EventBridge Consumer...")
    consumer = LeadgenEventBridgeConsumer(consumer_type=consumer_type)
    await consumer.start_consuming()