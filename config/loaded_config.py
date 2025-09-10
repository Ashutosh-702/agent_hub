import os
from database.connection_manager import ConnectionManager


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE","mongodb://localhost:27017")
    connection_manager: ConnectionManager = None
    debug = os.getenv("DEBUG",False)
    MODE = os.getenv("MODE", "server")
    base_url = os.getenv("BASE_URL","http://0.0.0.0:80")
    # lusha_api_key = os.getenv("LUSHA_API_KEY")
    lusha_api_key = "cc6b0756-527d-4c71-b7e1-fe9119e96cca"

loaded_config = Settings()
