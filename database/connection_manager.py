import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

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

    def _setup_mongo(self):
        if self.mongo_uri:
            return AsyncIOMotorClient(self.mongo_uri)
        return None
    async def close_connections(self):
        if self._mongo_client:
            self._mongo_client.close()
    @property
    def mongo_client(self):
        return self._mongo_client

