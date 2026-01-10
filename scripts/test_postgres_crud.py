"""Test PostgreSQL CRUD operations with UserDAO."""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.loaded_config import Settings
from database.connection_manager import ConnectionManager
from database.factory import get_users_dao, get_user_tokens_dao


async def test_crud_operations():
    """Test Create, Read, Update, Delete operations."""
    print("\n" + "="*60)
    print("PostgreSQL CRUD Operations Test")
    print("="*60 + "\n")
    
    # Set environment to use PostgreSQL
    os.environ["DB_BACKEND_USERS"] = "postgres"
    os.environ["DB_BACKEND_USER_TOKENS"] = "postgres"
    os.environ["POSTGRES_URL"] = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub"
    
    # Reload settings
    Settings.db_backend_users = "postgres"
    Settings.db_backend_user_tokens = "postgres"
    Settings.postgres_url = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub"
    
    # Initialize connection manager
    conn_mgr = ConnectionManager(
        mongo_uri=Settings.mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=Settings.postgres_url
    )
    
    test_user_id = None
    test_token_id = None
    
    try:
        # Setup PostgreSQL
        await conn_mgr.setup_postgres(echo=False)
        
        users_dao = get_users_dao(conn_mgr)
        tokens_dao = get_user_tokens_dao(conn_mgr)
        
        # Generate unique test data
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_name = f"Test User {uuid.uuid4().hex[:8]}"
        
        # Test 1: CREATE
        print("🔄 Test 1: Creating user...")
        user_data = {
            "email": test_email,
            "name": test_name,
            "password_hash": "test_hash_123"
        }
        
        test_user_id = await users_dao.insert_one(user_data)
        print(f"✅ User created with ID: {test_user_id}\n")
        
        # Test 2: READ (find_one)
        print("🔄 Test 2: Reading user by ID...")
        found_user = await users_dao.find_one({"_id": test_user_id})
        assert found_user is not None, "User not found"
        assert found_user["email"] == test_email, "Email mismatch"
        print(f"✅ User found: {found_user['name']}\n")
        
        # Test 3: UPDATE
        print("🔄 Test 3: Updating user...")
        update_data = {
            "name": "Updated Name"
        }
        await users_dao.update_one(
            {"_id": test_user_id},
            {"$set": update_data}
        )
        
        updated_user = await users_dao.find_one({"_id": test_user_id})
        assert updated_user["name"] == "Updated Name", "Update failed"
        print(f"✅ User updated successfully\n")
        
        # Test 4: CREATE token
        print("🔄 Test 4: Creating user token...")
        token_data = {
            "user_id": test_user_id,
            "token": f"token_{uuid.uuid4().hex}",
            "expires_at": datetime.utcnow() + timedelta(days=15)
        }
        
        test_token_id = await tokens_dao.insert_one(token_data)
        print(f"✅ Token created with ID: {test_token_id}\n")
        
        # Test 5: FIND (list with filter)
        print("🔄 Test 5: Finding tokens by user_id...")
        tokens = await tokens_dao.find({"user_id": test_user_id})
        assert len(tokens) == 1, "Token count mismatch"
        print(f"✅ Found {len(tokens)} token(s)\n")
        
        # Test 6: DELETE token
        print("🔄 Test 6: Deleting token...")
        delete_result = await tokens_dao.delete_one({"_id": test_token_id})
        assert delete_result["deleted_count"] == 1, "Token deletion failed"
        print(f"✅ Token deleted\n")
        
        # Test 7: DELETE user
        print("🔄 Test 7: Deleting user...")
        delete_result = await users_dao.delete_one({"_id": test_user_id})
        assert delete_result["deleted_count"] == 1, "User deletion failed"
        print(f"✅ User deleted\n")
        
        # Verify deletion
        print("🔄 Test 8: Verifying deletion...")
        found_user = await users_dao.find_one({"_id": test_user_id})
        assert found_user is None, "User still exists after deletion"
        print(f"✅ Deletion verified\n")
        
        print("="*60)
        print("✅ All CRUD tests passed!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on failure
        if test_user_id:
            try:
                await users_dao.delete_one({"_id": test_user_id})
            except:
                pass
        if test_token_id:
            try:
                await tokens_dao.delete_one({"_id": test_token_id})
            except:
                pass
        
        return False
    finally:
        await conn_mgr.close_connections()


if __name__ == "__main__":
    success = asyncio.run(test_crud_operations())
    sys.exit(0 if success else 1)

