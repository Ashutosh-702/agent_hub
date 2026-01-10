"""Test PostgreSQL setup and basic DAO operations."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.loaded_config import Settings
from database.connection_manager import ConnectionManager
from database.factory import get_users_dao


async def test_postgres_setup():
    """Test basic PostgreSQL connection and operations."""
    print("\n" + "="*60)
    print("PostgreSQL Setup Test")
    print("="*60 + "\n")
    
    # Set environment to use PostgreSQL for users
    os.environ["DB_BACKEND_USERS"] = "postgres"
    os.environ["POSTGRES_URL"] = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub"
    
    # Reload settings
    Settings.db_backend_users = "postgres"
    Settings.postgres_url = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub"
    
    print(f"📊 Testing with POSTGRES_URL: {Settings.postgres_url}")
    print(f"🔧 Using backend for users: {Settings.db_backend_users}\n")
    
    # Initialize connection manager
    conn_mgr = ConnectionManager(
        mongo_uri=Settings.mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=Settings.postgres_url
    )
    
    try:
        # Setup PostgreSQL
        print("🔄 Connecting to PostgreSQL...")
        await conn_mgr.setup_postgres(echo=True)
        
        if not conn_mgr.postgres_engine:
            print("❌ PostgreSQL engine not initialized")
            return False
        
        print("✅ PostgreSQL connection successful!\n")
        
        # Test DAO factory
        print("🔄 Testing DAO factory...")
        users_dao = get_users_dao(conn_mgr)
        print(f"✅ Got DAO: {type(users_dao).__name__}\n")
        
        # Test session creation
        print("🔄 Testing session creation...")
        async with conn_mgr.pg_session_context() as session:
            print(f"✅ Session created: {type(session).__name__}\n")
            
            # Try a simple query to verify tables exist
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✅ Users table query successful. Count: {count}\n")
        
        print("="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn_mgr.close_connections()
        print("🔄 Connections closed\n")


if __name__ == "__main__":
    success = asyncio.run(test_postgres_setup())
    sys.exit(0 if success else 1)

