import os
from pathlib import Path
from dotenv import load_dotenv
from database.connection_manager import ConnectionManager
import aiohttp

# Load .env file before reading environment variables
# Find the .env file relative to this file's location
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # Fallback: try loading from current directory
    import logging
    logging.warning(f".env file not found at {env_path}, trying current directory")
    load_dotenv(override=True)


class Settings:
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE","mongodb://localhost:27017")
    connection_manager: ConnectionManager = None
    # Enable debug/hot reload by default for local development
    debug = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    MODE = os.getenv("MODE", "server")
    base_url = os.getenv("BASE_URL","http://0.0.0.0:80")
    lusha_api_key = os.getenv("LUSHA_API_KEY")
    apollo_api_key = os.getenv("APOLLO_API_KEY")
    http_session : aiohttp.ClientSession = None
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip('"').strip("'")  # Strip quotes if present
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
    
    # Client Calls / Meetings - Deepgram for transcription
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "")
    
loaded_config = Settings()
