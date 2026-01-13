import os
import logging
from typing import Optional
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
    """Manages database connections for both MongoDB and PostgreSQL.
    
    This class supports gradual migration from MongoDB to PostgreSQL
    by maintaining connections to both databases simultaneously.
    """
    
    def __init__(self, mongo_uri: str, db_name: str, postgres_url: Optional[str] = None):
        """Initialize the connection manager.
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: MongoDB database name
            postgres_url: PostgreSQL connection URL (optional)
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.postgres_url = postgres_url
        self._mongo_client = self._setup_mongo()
        self._postgres_engine = None
        self.event_emitter = None
        
    def _setup_mongo(self):
        """Initialize MongoDB client."""
        if self.mongo_uri:
            return AsyncIOMotorClient(self.mongo_uri)
        return None
    
    async def setup_postgres(self, echo: bool = False):
        """Initialize PostgreSQL engine if configured.
        
        Args:
            echo: If True, log SQL statements
        """
        if not self.postgres_url:
            return
        
        try:
            from database.postgres.engine import PostgresEngine
            
            self._postgres_engine = PostgresEngine(self.postgres_url)
            await self._postgres_engine.connect(echo=echo)
            print("✅ PostgreSQL engine initialized in ConnectionManager")
        except ImportError as e:
            print(f"⚠️ PostgreSQL dependencies not installed: {e}")
        except Exception as e:
            print(f"❌ PostgreSQL initialization failed: {e}")
            # Don't raise - allow app to continue with MongoDB only
        
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
        """Close all database connections."""
        # Close MongoDB
        if self._mongo_client:
            self._mongo_client.close()
            print("✅ MongoDB connection closed")
        
        # Close PostgreSQL
        if self._postgres_engine:
            await self._postgres_engine.disconnect()
        
        # Close EventBridge
        if self.event_emitter and hasattr(self.event_emitter, 'event_emitter') and hasattr(self.event_emitter.event_emitter, 'kafka_producer'):
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
        """Get the MongoDB client."""
        return self._mongo_client
    
    @property
    def postgres_engine(self):
        """Get the PostgreSQL engine."""
        return self._postgres_engine
    
    @property
    def pg_session(self):
        """Get a new PostgreSQL session.
        
        Note: Caller is responsible for managing the session lifecycle.
        
        Returns:
            AsyncSession or None if PostgreSQL not configured
        """
        if self._postgres_engine:
            return self._postgres_engine.get_session()
        return None
    
    def get_pg_session(self):
        """Get a new PostgreSQL session (alias for pg_session property).
        
        Returns:
            AsyncSession or None if PostgreSQL not configured
        """
        return self.pg_session
    
    def pg_session_context(self):
        """Get PostgreSQL session as async context manager.
        
        Usage:
            async with connection_manager.pg_session_context() as session:
                # Use session
        
        Returns:
            Context manager yielding AsyncSession
        """
        if self._postgres_engine:
            return self._postgres_engine.session()
        raise RuntimeError("PostgreSQL not configured")
    
    
    
    

