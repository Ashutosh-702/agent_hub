#!/usr/bin/env python3
"""Database Parity Testing Script.

This script tests that MongoDB and PostgreSQL DAOs produce identical results
for the same operations, ensuring migration correctness.

Usage:
    python scripts/db_parity_test.py [--collection COLLECTION]
    
Example:
    python scripts/db_parity_test.py --collection users
    python scripts/db_parity_test.py  # Test all collections
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson import ObjectId


class ParityTest:
    """Base class for parity testing between MongoDB and PostgreSQL."""
    
    def __init__(self, mongo_dao, postgres_dao, collection_name: str):
        self.mongo_dao = mongo_dao
        self.postgres_dao = postgres_dao
        self.collection_name = collection_name
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []
    
    def _normalize_doc(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Normalize document for comparison."""
        if doc is None:
            return None
        
        result = {}
        for key, value in doc.items():
            # Convert ObjectId to string
            if isinstance(value, ObjectId):
                result[key] = str(value)
            # Normalize datetime
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            # Handle nested dicts
            elif isinstance(value, dict):
                result[key] = self._normalize_doc(value)
            # Handle lists
            elif isinstance(value, list):
                result[key] = [
                    self._normalize_doc(item) if isinstance(item, dict) 
                    else str(item) if isinstance(item, ObjectId)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    def _compare_results(self, mongo_result: Any, postgres_result: Any, 
                        operation: str, ignore_fields: List[str] = None) -> bool:
        """Compare results from MongoDB and PostgreSQL."""
        if ignore_fields is None:
            ignore_fields = ["_id", "id", "created_at", "updated_at"]
        
        # Normalize both results
        if isinstance(mongo_result, dict):
            mongo_normalized = self._normalize_doc(mongo_result)
            postgres_normalized = self._normalize_doc(postgres_result)
            
            # Remove ignored fields
            for field in ignore_fields:
                mongo_normalized.pop(field, None)
                postgres_normalized.pop(field, None) if postgres_normalized else None
        elif isinstance(mongo_result, list):
            mongo_normalized = [self._normalize_doc(doc) for doc in mongo_result]
            postgres_normalized = [self._normalize_doc(doc) for doc in postgres_result]
        else:
            mongo_normalized = mongo_result
            postgres_normalized = postgres_result
        
        if mongo_normalized == postgres_normalized:
            self.passed += 1
            print(f"  ✅ {operation}")
            return True
        else:
            self.failed += 1
            error = f"{operation}: Results differ\n  MongoDB: {mongo_normalized}\n  PostgreSQL: {postgres_normalized}"
            self.errors.append(error)
            print(f"  ❌ {operation}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print(f"Results for {self.collection_name}:")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}\n")


class UsersParityTest(ParityTest):
    """Parity tests for users collection."""
    
    async def run(self):
        """Run all user parity tests."""
        print(f"\n🧪 Testing {self.collection_name}...")
        
        # Test create user
        test_user = {
            "email": f"test_{datetime.utcnow().timestamp()}@example.com",
            "password_hash": "hashed_password_123",
            "name": "Test User",
            "is_active": True
        }
        
        mongo_id = await self.mongo_dao.create_user(test_user.copy())
        postgres_id = await self.postgres_dao.create_user(test_user.copy())
        
        self._compare_results(
            bool(mongo_id), bool(postgres_id), 
            "create_user returns ID"
        )
        
        # Test get user by email
        mongo_user = await self.mongo_dao.get_user_by_email(test_user["email"])
        postgres_user = await self.postgres_dao.get_user_by_email(test_user["email"])
        
        self._compare_results(
            mongo_user is not None, postgres_user is not None,
            "get_user_by_email finds user"
        )
        
        # Test email_exists
        mongo_exists = await self.mongo_dao.email_exists(test_user["email"])
        postgres_exists = await self.postgres_dao.email_exists(test_user["email"])
        
        self._compare_results(mongo_exists, postgres_exists, "email_exists")
        
        # Test update user
        await self.mongo_dao.update_user(mongo_id, {"name": "Updated Name"})
        await self.postgres_dao.update_user(postgres_id, {"name": "Updated Name"})
        
        mongo_updated = await self.mongo_dao.get_user_by_id(mongo_id)
        postgres_updated = await self.postgres_dao.get_user_by_id(postgres_id)
        
        self._compare_results(
            mongo_updated.get("name"), postgres_updated.get("name"),
            "update_user modifies name"
        )
        
        # Cleanup
        await self.mongo_dao.delete_one({"_id": mongo_id})
        await self.postgres_dao.delete_one({"_id": postgres_id})
        
        self.print_summary()


class CampaignsParityTest(ParityTest):
    """Parity tests for campaigns collection."""
    
    async def run(self):
        """Run all campaign parity tests."""
        print(f"\n🧪 Testing {self.collection_name}...")
        
        # Test create campaign
        test_campaign = {
            "name": f"Test Campaign {datetime.utcnow().timestamp()}",
            "campaign_type": "wide_prospecting",
            "lifecycle": {"status": "started"},
            "prospecting_cycle": {"status": "prospecting"},
            "segmentation": {"industry": ["Tech"]},
            "target": {"employee_count": ["11-50"]},
            "ownership": {"user_email": "test@example.com"},
        }
        
        mongo_id = await self.mongo_dao.create_campaign(test_campaign.copy())
        postgres_id = await self.postgres_dao.create_campaign(test_campaign.copy())
        
        self._compare_results(
            bool(mongo_id), bool(postgres_id), 
            "create_campaign returns ID"
        )
        
        # Test get campaign
        mongo_campaign = await self.mongo_dao.get_campaign(mongo_id)
        postgres_campaign = await self.postgres_dao.get_campaign(postgres_id)
        
        self._compare_results(
            mongo_campaign is not None, postgres_campaign is not None,
            "get_campaign finds campaign"
        )
        
        # Test update campaign status
        await self.mongo_dao.update_campaign_status(mongo_id, "completed")
        await self.postgres_dao.update_campaign_status(postgres_id, "completed")
        
        mongo_updated = await self.mongo_dao.get_campaign(mongo_id)
        postgres_updated = await self.postgres_dao.get_campaign(postgres_id)
        
        mongo_status = mongo_updated.get("lifecycle", {}).get("status")
        postgres_status = postgres_updated.get("lifecycle", {}).get("status") or postgres_updated.get("lifecycle_status")
        
        self._compare_results(
            mongo_status, postgres_status,
            "update_campaign_status modifies status"
        )
        
        # Cleanup
        await self.mongo_dao.delete_one({"_id": mongo_id})
        await self.postgres_dao.delete_one({"_id": postgres_id})
        
        self.print_summary()


class CompaniesParityTest(ParityTest):
    """Parity tests for companies collection."""
    
    async def run(self):
        """Run all company parity tests."""
        print(f"\n🧪 Testing {self.collection_name}...")
        
        # Test create company
        test_company = {
            "identifiers": {
                "source_id": f"test_{datetime.utcnow().timestamp()}",
                "name": "Test Company Inc",
                "source_domain": "testcompany.com"
            },
            "profile": {
                "industry": ["Technology"],
                "employee_count": ["51-200"]
            },
            "location": {
                "type": "country",
                "name": ["USA"]
            },
            "source": "apollo"
        }
        
        mongo_id = await self.mongo_dao.create_company(test_company.copy())
        postgres_id = await self.postgres_dao.create_company(test_company.copy())
        
        self._compare_results(
            bool(mongo_id), bool(postgres_id), 
            "create_company returns ID"
        )
        
        # Test get company
        mongo_company = await self.mongo_dao.get_company(mongo_id)
        postgres_company = await self.postgres_dao.get_company(postgres_id)
        
        self._compare_results(
            mongo_company is not None, postgres_company is not None,
            "get_company finds company"
        )
        
        # Test update company
        await self.mongo_dao.update_company(mongo_id, {"source": "manual"})
        await self.postgres_dao.update_company(postgres_id, {"source": "manual"})
        
        mongo_updated = await self.mongo_dao.get_company(mongo_id)
        postgres_updated = await self.postgres_dao.get_company(postgres_id)
        
        self._compare_results(
            mongo_updated.get("source"), postgres_updated.get("source"),
            "update_company modifies source"
        )
        
        # Cleanup
        await self.mongo_dao.delete_one({"_id": mongo_id})
        await self.postgres_dao.delete_one({"_id": postgres_id})
        
        self.print_summary()


async def run_parity_tests(collections: List[str] = None):
    """Run parity tests for specified or all collections."""
    from database.connection_manager import ConnectionManager
    from config.loaded_config import loaded_config
    
    # Initialize connections
    mongo_uri = loaded_config.mongo_uri
    postgres_url = loaded_config.postgres_url
    
    connection_manager = ConnectionManager(mongo_uri, "agent_hub_test", postgres_url)
    await connection_manager.setup_postgres(echo=False)
    
    all_collections = ["users", "campaigns", "companies"]
    test_collections = collections if collections else all_collections
    
    total_passed = 0
    total_failed = 0
    
    for collection in test_collections:
        if collection == "users":
            from database.collection_dao.users import UsersDao
            from database.postgres.collection_dao.users import PostgresUsersDao
            
            mongo_dao = UsersDao(connection_manager.mongo_client)
            postgres_dao = PostgresUsersDao(connection_manager.get_pg_session())
            
            test = UsersParityTest(mongo_dao, postgres_dao, "users")
            await test.run()
            total_passed += test.passed
            total_failed += test.failed
            
        elif collection == "campaigns":
            from database.collection_dao.campaigns import CampaignsDao
            from database.postgres.collection_dao.campaigns import PostgresCampaignsDao
            
            mongo_dao = CampaignsDao(connection_manager.mongo_client)
            postgres_dao = PostgresCampaignsDao(connection_manager.get_pg_session())
            
            test = CampaignsParityTest(mongo_dao, postgres_dao, "campaigns")
            await test.run()
            total_passed += test.passed
            total_failed += test.failed
            
        elif collection == "companies":
            from database.collection_dao.companies import CompaniesDao
            from database.postgres.collection_dao.companies import PostgresCompaniesDao
            
            mongo_dao = CompaniesDao(connection_manager.mongo_client)
            postgres_dao = PostgresCompaniesDao(connection_manager.get_pg_session())
            
            test = CompaniesParityTest(mongo_dao, postgres_dao, "companies")
            await test.run()
            total_passed += test.passed
            total_failed += test.failed
    
    # Close connections
    await connection_manager.close_connections()
    
    # Final summary
    print("\n" + "="*60)
    print("OVERALL RESULTS")
    print("="*60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed+total_failed)*100:.1f}%" if (total_passed+total_failed) > 0 else "N/A")
    print("="*60)
    
    return total_failed == 0


def main():
    parser = argparse.ArgumentParser(description="Test MongoDB/PostgreSQL parity")
    parser.add_argument("--collection", type=str, help="Collection to test (default: all)")
    args = parser.parse_args()
    
    collections = [args.collection] if args.collection else None
    
    success = asyncio.run(run_parity_tests(collections))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


