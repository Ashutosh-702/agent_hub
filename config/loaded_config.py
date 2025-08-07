import os
from database.connection_manager import ConnectionManager


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE","mongodb://host.docker.internal:27017")
    connection_manager: ConnectionManager = None
    debug = os.getenv("DEBUG",False)


loaded_config = Settings()
