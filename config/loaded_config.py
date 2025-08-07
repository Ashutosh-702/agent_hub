import os
from database.connection_manager import ConnectionManager


class Settings:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    connection_manager: ConnectionManager = None


loaded_config = Settings()
