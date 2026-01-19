#!/usr/bin/env python3
"""Seed mock data for testing the Tasks module.

Creates 2 companies, 2 contacts, and 2 deals.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add agent_hub to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection_manager import ConnectionManager
from database.factory import get_companies_dao, get_contacts_dao, get_deals_dao
from database.postgres.base_dao import generate_objectid
from config.loaded_config import loaded_config


async def seed_mock_data():
    """Seed mock data for companies, contacts, and deals."""
    print("🌱 Seeding mock data for Tasks module...\n")
    
    # Initialize connection manager
    connection_manager = ConnectionManager(
        mongo_uri=loaded_config.mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=loaded_config.postgres_url
    )
    await connection_manager.setup_postgres()
    
    try:
        # Get DAOs
        companies_dao = get_companies_dao(connection_manager)
        contacts_dao = get_contacts_dao(connection_manager)
        deals_dao = get_deals_dao(connection_manager)
        
        # =====================================================================
        # Create 2 Companies
        # =====================================================================
        print("📊 Creating companies...")
        
        company1_data = {
            "_id": generate_objectid(),
            "name": "TechCorp Solutions",
            "source": "manual",
            "source_id": "techcorp_001",
            "primary_domain": "techcorp.com",
            "source_domain": "techcorp.com",
            "industry": ["Technology", "Software"],
            "identifiers": {
                "name": "TechCorp Solutions",
                "source_id": "techcorp_001",
                "source_domain": "techcorp.com"
            },
            "profile": {
                "industry": ["Technology", "Software"],
                "employee_count": 500,
                "revenue_min": 50,
                "revenue_max": 100
            },
            "location": {
                "type": "country",
                "name": ["United States"]
            },
            "metadata_json": {
                "created_by": "system",
                "notes": "Leading software solutions provider"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        company2_data = {
            "_id": generate_objectid(),
            "name": "Global Manufacturing Inc",
            "source": "manual",
            "source_id": "globalmfg_002",
            "primary_domain": "globalmfg.com",
            "source_domain": "globalmfg.com",
            "industry": ["Manufacturing", "Industrial"],
            "identifiers": {
                "name": "Global Manufacturing Inc",
                "source_id": "globalmfg_002",
                "source_domain": "globalmfg.com"
            },
            "profile": {
                "industry": ["Manufacturing", "Industrial"],
                "employee_count": 1200,
                "revenue_min": 200,
                "revenue_max": 500
            },
            "location": {
                "type": "country",
                "name": ["United States", "Canada"]
            },
            "metadata_json": {
                "created_by": "system",
                "notes": "International manufacturing company"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        company1_id = await companies_dao.insert_one(company1_data)
        company2_id = await companies_dao.insert_one(company2_data)
        
        print(f"  ✅ Created company 1: TechCorp Solutions (ID: {company1_id})")
        print(f"  ✅ Created company 2: Global Manufacturing Inc (ID: {company2_id})\n")
        
        # =====================================================================
        # Create 2 Contacts
        # =====================================================================
        print("👤 Creating contacts...")
        
        contact1_data = {
            "_id": generate_objectid(),
            "firstname": "John",
            "lastname": "Smith",
            "email": "john.smith@techcorp.com",
            "jobtitle": "VP of Sales",
            "source_id": "contact_001",
            "company_id": company1_id,
            "contact_data": {
                "firstname": "John",
                "lastname": "Smith",
                "email": ["john.smith@techcorp.com"],
                "jobtitle": "VP of Sales",
                "phone": ["+1-555-0101"]
            },
            "linkedin_data": {
                "linkedin_url": "https://linkedin.com/in/johnsmith"
            },
            "metadata_json": {
                "source": "manual",
                "notes": "Primary decision maker"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        contact2_data = {
            "_id": generate_objectid(),
            "firstname": "Sarah",
            "lastname": "Johnson",
            "email": "sarah.johnson@globalmfg.com",
            "jobtitle": "Director of Operations",
            "source_id": "contact_002",
            "company_id": company2_id,
            "contact_data": {
                "firstname": "Sarah",
                "lastname": "Johnson",
                "email": ["sarah.johnson@globalmfg.com"],
                "jobtitle": "Director of Operations",
                "phone": ["+1-555-0202"]
            },
            "linkedin_data": {
                "linkedin_url": "https://linkedin.com/in/sarahjohnson"
            },
            "metadata_json": {
                "source": "manual",
                "notes": "Key stakeholder"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        contact1_id = await contacts_dao.insert_one(contact1_data)
        contact2_id = await contacts_dao.insert_one(contact2_data)
        
        print(f"  ✅ Created contact 1: John Smith (ID: {contact1_id})")
        print(f"  ✅ Created contact 2: Sarah Johnson (ID: {contact2_id})\n")
        
        # =====================================================================
        # Create 2 Deals
        # =====================================================================
        print("💼 Creating deals...")
        
        deal1_data = {
            "_id": generate_objectid(),
            "company_id": company1_id,
            "name": "Enterprise Software License",
            "stage": "negotiation",
            "amount": 150000.00,
            "metadata_json": {
                "created_by": "system",
                "notes": "Large enterprise deal",
                "probability": 75
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        deal2_data = {
            "_id": generate_objectid(),
            "company_id": company2_id,
            "name": "Manufacturing Equipment Upgrade",
            "stage": "proposal",
            "amount": 500000.00,
            "metadata_json": {
                "created_by": "system",
                "notes": "Major equipment purchase",
                "probability": 60
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        deal1_id = await deals_dao.insert_one(deal1_data)
        deal2_id = await deals_dao.insert_one(deal2_data)
        
        print(f"  ✅ Created deal 1: Enterprise Software License (ID: {deal1_id})")
        print(f"  ✅ Created deal 2: Manufacturing Equipment Upgrade (ID: {deal2_id})\n")
        
        # =====================================================================
        # Summary
        # =====================================================================
        print("=" * 60)
        print("✅ Mock data seeding complete!")
        print("=" * 60)
        print(f"\n📊 Companies:")
        print(f"  1. TechCorp Solutions - {company1_id}")
        print(f"  2. Global Manufacturing Inc - {company2_id}")
        print(f"\n👤 Contacts:")
        print(f"  1. John Smith (TechCorp) - {contact1_id}")
        print(f"  2. Sarah Johnson (Global Manufacturing) - {contact2_id}")
        print(f"\n💼 Deals:")
        print(f"  1. Enterprise Software License (TechCorp) - {deal1_id}")
        print(f"  2. Manufacturing Equipment Upgrade (Global Manufacturing) - {deal2_id}")
        print("\n🎯 You can now create tasks linked to these entities!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error seeding mock data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await connection_manager.close_connections()


if __name__ == "__main__":
    asyncio.run(seed_mock_data())
