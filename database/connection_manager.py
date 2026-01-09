import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from eventbridge.emitter import AsyncEventEmitter
from kafkautils.producer.producer import AsyncEventEmitterWrapper
from kafkautils.producer.kafka_config import get_producer_config

load_dotenv()

# Configuration

# Global variables
client = None
database = None

class ConnectionManager:
    def __init__(self, mongo_uri: str, db_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self._mongo_client = self._setup_mongo()
        self.event_emitter = None
        
    def _setup_mongo(self):
        if self.mongo_uri:
            return AsyncIOMotorClient(self.mongo_uri)
        return None
        
    async def setup_eventbridge_producer(self):
        """Initialize EventBridge producer following pigeon pattern."""
        try:
            producer_config = get_producer_config()
            event_emitter_instance = AsyncEventEmitter(producer_config)
            self.event_emitter = AsyncEventEmitterWrapper(event_emitter_instance)
            print("✅ EventBridge Producer initialized in ConnectionManager")
        except Exception as e:
            print(f"❌ EventBridge Producer initialization failed: {e}")
            raise
            
    async def close_connections(self):
        if self._mongo_client:
            self._mongo_client.close()
        
        # Close EventBridge producer if it exists and is properly initialized
        if self.event_emitter:
            try:
                if hasattr(self.event_emitter, 'event_emitter') and self.event_emitter.event_emitter:
                    if hasattr(self.event_emitter.event_emitter, 'kafka_producer') and self.event_emitter.event_emitter.kafka_producer:
                        await self.event_emitter.event_emitter.kafka_producer.stop_producer()
                        print("✅ EventBridge Producer closed")
                    else:
                        print("⚠️ EventBridge Producer kafka_producer not initialized, skipping close")
                else:
                    print("⚠️ EventBridge Producer event_emitter not initialized, skipping close")
            except AttributeError as e:
                print(f"⚠️ EventBridge Producer structure unexpected: {e}")
            except Exception as e:
                print(f"❌ Error closing EventBridge Producer: {e}")
                
    @property
    def mongo_client(self):
        return self._mongo_client
    
    
    
    

