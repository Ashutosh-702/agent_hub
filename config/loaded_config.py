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
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "9be8d4f2be2830be27ba2710784c76d8d0a724a7")
    
    # ============================================================
    # PostgreSQL Migration Feature Flags
    # ============================================================
    # Set to "postgres" to use PostgreSQL, "mongo" to use MongoDB
    # This allows gradual migration collection by collection
    # ============================================================
    
    # PostgreSQL connection URL
    postgres_url = os.getenv(
        "POSTGRES_URL",
        os.getenv("DATABASE_URL", "postgresql+asyncpg://agent_hub:agent_hub@localhost:5432/agent_hub")
    )
    
    # Per-collection database backend selection
    # Valid values: "mongo" (default) or "postgres"
    db_backend_users = os.getenv("DB_BACKEND_USERS", "mongo")
    db_backend_user_tokens = os.getenv("DB_BACKEND_USER_TOKENS", "mongo")
    db_backend_campaigns = os.getenv("DB_BACKEND_CAMPAIGNS", "mongo")
    db_backend_companies = os.getenv("DB_BACKEND_COMPANIES", "mongo")
    db_backend_contacts = os.getenv("DB_BACKEND_CONTACTS", "mongo")
    db_backend_campaign_company_runs = os.getenv("DB_BACKEND_CAMPAIGN_COMPANY_RUNS", "mongo")
    db_backend_campaign_contact_runs = os.getenv("DB_BACKEND_CAMPAIGN_CONTACT_RUNS", "mongo")
    db_backend_meetings = os.getenv("DB_BACKEND_MEETINGS", "mongo")
    db_backend_inbox_leads = os.getenv("DB_BACKEND_INBOX_LEADS", "mongo")
    db_backend_inbox_events = os.getenv("DB_BACKEND_INBOX_EVENTS", "mongo")
    db_backend_inbox_notes = os.getenv("DB_BACKEND_INBOX_NOTES", "mongo")
    
    @classmethod
    def use_postgres(cls, collection: str) -> bool:
        """Check if a collection should use PostgreSQL.
        
        Args:
            collection: Collection name (e.g., "users", "campaigns")
            
        Returns:
            True if PostgreSQL should be used, False for MongoDB
        """
        attr_name = f"db_backend_{collection}"
        backend = getattr(cls, attr_name, "mongo")
        return backend.lower() == "postgres"
    
    @classmethod
    def is_any_postgres_enabled(cls) -> bool:
        """Check if any collection is using PostgreSQL.
        
        Returns:
            True if at least one collection uses PostgreSQL
        """
        collections = [
            "users", "user_tokens", "campaigns", "companies", "contacts",
            "campaign_company_runs", "campaign_contact_runs", "meetings",
            "inbox_leads", "inbox_events", "inbox_notes"
        ]
        return any(cls.use_postgres(c) for c in collections)
    
loaded_config = Settings()
