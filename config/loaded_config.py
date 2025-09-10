import os
from database.connection_manager import ConnectionManager


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE","mongodb://localhost:27017")
    connection_manager: ConnectionManager = None
    debug = os.getenv("DEBUG",False)
    MODE = os.getenv("MODE", "server")
    base_url = os.getenv("BASE_URL","http://0.0.0.0:80")
    # lusha_api_key = os.getenv("LUSHA_API_KEY")
    lusha_api_key = "19181599-49af-402c-adb0-71cd402aec81"

loaded_config = Settings()
