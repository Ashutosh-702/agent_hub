#!/usr/bin/env python3
"""Data Migration Script - MongoDB to PostgreSQL.

This script migrates existing data from MongoDB collections to PostgreSQL tables.
It's designed to run incrementally and can be safely re-run.

Usage:
    python scripts/migrate_data.py [--collection COLLECTION] [--batch-size BATCH_SIZE]
    
Example:
    python scripts/migrate_data.py --collection users --batch-size 1000
    python scripts/migrate_data.py  # Migrate all collections
"""

import asyncio
import argparse
from datetime import datetime
from typing import Any, Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson import ObjectId


# Migration order (respects foreign key dependencies)
MIGRATION_ORDER = [
    "users",
    "user_tokens",
    "companies",
    "contacts",
    "campaigns",
    "campaign_company_runs",
    "campaign_contact_runs",
    "meetings",
    "inbox_leads",
    "inbox_events",
    "inbox_notes",
]


def normalize_objectid(value: Any) -> Any:
    """Convert ObjectId to string."""
    if isinstance(value, ObjectId):
        return str(value)
    return value


def normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively normalize a document for PostgreSQL."""
    if not isinstance(doc, dict):
        return normalize_objectid(doc)
    
    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value) if isinstance(value, ObjectId) else value
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = normalize_document(value)
        elif isinstance(value, list):
            result[key] = [
                normalize_document(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


async def migrate_collection(
    mongo_dao,
    postgres_dao,
    collection_name: str,
    batch_size: int = 500,
    skip_existing: bool = True
) -> Dict[str, int]:
    """Migrate a single collection from MongoDB to PostgreSQL.
    
    Args:
        mongo_dao: MongoDB DAO instance
        postgres_dao: PostgreSQL DAO instance
        collection_name: Name of the collection
        batch_size: Number of documents per batch
        skip_existing: If True, skip documents that already exist
        
    Returns:
        Dict with migration statistics
    """
    stats = {
        "total": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    print(f"\n📦 Migrating {collection_name}...")
    
    # Get all documents from MongoDB
    page = 1
    while True:
        try:
            # Use pagination if available
            if hasattr(mongo_dao, 'get_paginated_response'):
                documents, pagination = await mongo_dao.get_paginated_response(
                    {}, 
                    page_size=batch_size, 
                    page_number=page
                )
            else:
                # Fallback to find_many
                documents = await mongo_dao.find_many({})
                pagination = {"has_next": False}
            
            if not documents:
                break
            
            stats["total"] += len(documents)
            
            for doc in documents:
                try:
                    # Normalize document
                    normalized = normalize_document(doc)
                    doc_id = normalized.get("id") or normalized.get("_id")
                    
                    # Check if already exists
                    if skip_existing and doc_id:
                        existing = await postgres_dao.find_one({"_id": doc_id})
                        if existing:
                            stats["skipped"] += 1
                            continue
                    
                    # Insert into PostgreSQL
                    await postgres_dao.insert_one(normalized)
                    stats["migrated"] += 1
                    
                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ❌ Error migrating document {doc_id}: {e}")
            
            # Progress update
            print(f"  Progress: {stats['migrated'] + stats['skipped']}/{stats['total']} "
                  f"(migrated: {stats['migrated']}, skipped: {stats['skipped']}, errors: {stats['errors']})")
            
            # Check if more pages
            if not pagination.get("has_next", False):
                break
            
            page += 1
            
        except Exception as e:
            print(f"  ❌ Batch error: {e}")
            stats["errors"] += 1
            break
    
    print(f"  ✅ Completed {collection_name}: "
          f"{stats['migrated']} migrated, {stats['skipped']} skipped, {stats['errors']} errors")
    
    return stats


async def run_migration(collections: List[str] = None, batch_size: int = 500):
    """Run migration for specified or all collections."""
    from database.connection_manager import ConnectionManager
    from config.loaded_config import loaded_config
    
    # Initialize connections
    mongo_uri = loaded_config.mongo_uri
    postgres_url = loaded_config.postgres_url
    
    print(f"🔗 Connecting to databases...")
    print(f"   MongoDB: {mongo_uri.split('@')[-1] if '@' in mongo_uri else 'localhost'}")
    print(f"   PostgreSQL: {postgres_url.split('@')[-1] if '@' in postgres_url else 'localhost'}")
    
    connection_manager = ConnectionManager(mongo_uri, "linkedin-sdr", postgres_url)
    await connection_manager.setup_postgres(echo=False)
    
    # Determine collections to migrate
    migrate_collections = collections if collections else MIGRATION_ORDER
    
    total_stats = {
        "total": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    for collection in migrate_collections:
        if collection not in MIGRATION_ORDER:
            print(f"⚠️  Unknown collection: {collection}")
            continue
        
        # Get DAOs based on collection
        mongo_dao = None
        postgres_dao = None
        
        try:
            if collection == "users":
                from database.collection_dao.users import UsersDao
                from database.postgres.collection_dao.users import PostgresUsersDao
                mongo_dao = UsersDao(connection_manager.mongo_client)
                postgres_dao = PostgresUsersDao(connection_manager.get_pg_session())
                
            elif collection == "user_tokens":
                from database.collection_dao.user_tokens import UserTokensDao
                from database.postgres.collection_dao.user_tokens import PostgresUserTokensDao
                mongo_dao = UserTokensDao(connection_manager.mongo_client)
                postgres_dao = PostgresUserTokensDao(connection_manager.get_pg_session())
                
            elif collection == "companies":
                from database.collection_dao.companies import CompaniesDao
                from database.postgres.collection_dao.companies import PostgresCompaniesDao
                mongo_dao = CompaniesDao(connection_manager.mongo_client)
                postgres_dao = PostgresCompaniesDao(connection_manager.get_pg_session())
                
            elif collection == "contacts":
                from database.collection_dao.contacts import ContactsDao
                from database.postgres.collection_dao.contacts import PostgresContactsDao
                mongo_dao = ContactsDao(connection_manager.mongo_client)
                postgres_dao = PostgresContactsDao(connection_manager.get_pg_session())
                
            elif collection == "campaigns":
                from database.collection_dao.campaigns import CampaignsDao
                from database.postgres.collection_dao.campaigns import PostgresCampaignsDao
                mongo_dao = CampaignsDao(connection_manager.mongo_client)
                postgres_dao = PostgresCampaignsDao(connection_manager.get_pg_session())
                
            elif collection == "campaign_company_runs":
                from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
                from database.postgres.collection_dao.campaign_company_runs import PostgresCampaignCompanyRunsDao
                mongo_dao = CampaignCompanyRunsDao(connection_manager.mongo_client)
                postgres_dao = PostgresCampaignCompanyRunsDao(connection_manager.get_pg_session())
                
            elif collection == "campaign_contact_runs":
                from database.collection_dao.campaign_contact_runs import CampaignContactRunsDao
                from database.postgres.collection_dao.campaign_contact_runs import PostgresCampaignContactRunsDao
                mongo_dao = CampaignContactRunsDao(connection_manager.mongo_client)
                postgres_dao = PostgresCampaignContactRunsDao(connection_manager.get_pg_session())
                
            elif collection == "meetings":
                from database.collection_dao.meetings import MeetingsDao
                from database.postgres.collection_dao.meetings import PostgresMeetingsDao
                mongo_dao = MeetingsDao(connection_manager.mongo_client)
                postgres_dao = PostgresMeetingsDao(connection_manager.get_pg_session())
                
            elif collection == "inbox_leads":
                from database.collection_dao.inbox_events import InboxLeadsDao
                from database.postgres.collection_dao.inbox_events import PostgresInboxLeadsDao
                mongo_dao = InboxLeadsDao(connection_manager.mongo_client)
                postgres_dao = PostgresInboxLeadsDao(connection_manager.get_pg_session())
                
            elif collection == "inbox_events":
                from database.collection_dao.inbox_events import InboxEventsDao
                from database.postgres.collection_dao.inbox_events import PostgresInboxEventsDao
                mongo_dao = InboxEventsDao(connection_manager.mongo_client)
                postgres_dao = PostgresInboxEventsDao(connection_manager.get_pg_session())
                
            elif collection == "inbox_notes":
                from database.collection_dao.inbox_events import InboxNotesDao
                from database.postgres.collection_dao.inbox_events import PostgresInboxNotesDao
                mongo_dao = InboxNotesDao(connection_manager.mongo_client)
                postgres_dao = PostgresInboxNotesDao(connection_manager.get_pg_session())
            
            if mongo_dao and postgres_dao:
                stats = await migrate_collection(
                    mongo_dao, postgres_dao, collection, batch_size
                )
                
                for key in total_stats:
                    total_stats[key] += stats[key]
                    
        except ImportError as e:
            print(f"⚠️  Cannot import DAOs for {collection}: {e}")
        except Exception as e:
            print(f"❌ Error migrating {collection}: {e}")
            total_stats["errors"] += 1
    
    # Close connections
    await connection_manager.close_connections()
    
    # Final summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total Documents: {total_stats['total']}")
    print(f"Migrated: {total_stats['migrated']}")
    print(f"Skipped (already exist): {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")
    print("="*60)
    
    return total_stats["errors"] == 0


def main():
    parser = argparse.ArgumentParser(description="Migrate data from MongoDB to PostgreSQL")
    parser.add_argument("--collection", type=str, help="Collection to migrate (default: all)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size (default: 500)")
    args = parser.parse_args()
    
    collections = [args.collection] if args.collection else None
    
    success = asyncio.run(run_migration(collections, args.batch_size))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


