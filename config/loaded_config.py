import os
from database.connection_manager import ConnectionManager
import aiohttp


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE","mongodb://localhost:27017")
    connection_manager: ConnectionManager = None
    debug = os.getenv("DEBUG",False)
    MODE = os.getenv("MODE", "server")
    base_url = os.getenv("BASE_URL","http://0.0.0.0:80")
    lusha_api_key = os.getenv("LUSHA_API_KEY")
    apollo_api_key = os.getenv("APOLLO_API_KEY")
    http_session : aiohttp.ClientSession = None
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "80"))
    workers = int(os.getenv("API_WORKERS", "1"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    serve_static = os.getenv("SERVE_STATIC", "true").lower() == "true"
    static_path = os.getenv("STATIC_PATH", "/Users/ahmedropewala/PycharmProjects/etc1/agent_hub/ai_agents/ui/dist")
    # Lemlist Integration
    lemlist_email = os.getenv("LEMLIST_EMAIL", "shubhamsoni@gofynd.com")
    lemlist_api_key = os.getenv("LEMLIST_API_KEY", "bda032d972797c0301b3ad74fddb55e3")
    lemlist_webhook_secret = os.getenv("LEMLIST_WEBHOOK_SECRET", "")
    
loaded_config = Settings()
