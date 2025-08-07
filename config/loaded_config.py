import os
from database.connection_manager import ConnectionManager


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE")
    connection_manager: ConnectionManager = None


loaded_config = Settings()
