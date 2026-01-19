#!/usr/bin/env python3
"""Seed mock data for testing the Tasks module using raw SQL.

Creates 2 companies, 2 contacts, and 2 deals.
This bypasses the ORM to avoid migration dependency issues.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add agent_hub to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection_manager import ConnectionManager
from database.postgres.base_dao import generate_objectid
from config.loaded_config import loaded_config
from sqlalchemy import text
import json


async def seed_mock_data():
    """Seed mock data for companies, contacts, and deals using raw SQL."""
    print("🌱 Seeding mock data for Tasks module (raw SQL)...\n")
    
    # Initialize connection manager
    connection_manager = ConnectionManager(
        mongo_uri=loaded_config.mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=loaded_config.postgres_url
    )
    await connection_manager.setup_postgres()
    
    try:
        engine = connection_manager.postgres_engine
        async with engine.get_session() as session:
            # Generate IDs
            company1_id = generate_objectid()
            company2_id = generate_objectid()
            contact1_id = generate_objectid()
            contact2_id = generate_objectid()
            deal1_id = generate_objectid()
            deal2_id = generate_objectid()
            
            # =====================================================================
            # Create 2 Companies
            # =====================================================================
            print("📊 Creating companies...")
            
            import json
            await session.execute(text("""
                INSERT INTO companies (
                    id, name, source, source_id, primary_domain, source_domain, 
                    industry, webhook_sent, created_at, updated_at,
                    identifiers, profile, location, metadata_json, deep_research, red_flags_history
                ) VALUES (
                    :id, :name, :source, :source_id, :primary_domain, :source_domain,
                    :industry, :webhook_sent, :created_at, :updated_at,
                    CAST(:identifiers AS jsonb), CAST(:profile AS jsonb), CAST(:location AS jsonb), 
                    CAST(:metadata_json AS jsonb), CAST(:deep_research AS jsonb), CAST(:red_flags_history AS jsonb)
                )
            """), {
                "id": company1_id,
                "name": "TechCorp Solutions",
                "source": "manual",
                "source_id": "techcorp_001",
                "primary_domain": "techcorp.com",
                "source_domain": "techcorp.com",
                "industry": ["Technology", "Software"],
                "webhook_sent": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "identifiers": json.dumps({"name": "TechCorp Solutions", "source_id": "techcorp_001", "source_domain": "techcorp.com"}),
                "profile": json.dumps({"industry": ["Technology", "Software"], "employee_count": 500, "revenue_min": 50, "revenue_max": 100}),
                "location": json.dumps({"type": "country", "name": ["United States"]}),
                "metadata_json": json.dumps({"created_by": "system", "notes": "Leading software solutions provider"}),
                "deep_research": "{}",
                "red_flags_history": "[]",
            })
            
            await session.execute(text("""
                INSERT INTO companies (
                    id, name, source, source_id, primary_domain, source_domain,
                    industry, webhook_sent, created_at, updated_at,
                    identifiers, profile, location, metadata_json, deep_research, red_flags_history
                ) VALUES (
                    :id, :name, :source, :source_id, :primary_domain, :source_domain,
                    :industry, :webhook_sent, :created_at, :updated_at,
                    CAST(:identifiers AS jsonb), CAST(:profile AS jsonb), CAST(:location AS jsonb),
                    CAST(:metadata_json AS jsonb), CAST(:deep_research AS jsonb), CAST(:red_flags_history AS jsonb)
                )
            """), {
                "id": company2_id,
                "name": "Global Manufacturing Inc",
                "source": "manual",
                "source_id": "globalmfg_002",
                "primary_domain": "globalmfg.com",
                "source_domain": "globalmfg.com",
                "industry": ["Manufacturing", "Industrial"],
                "webhook_sent": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "identifiers": json.dumps({"name": "Global Manufacturing Inc", "source_id": "globalmfg_002", "source_domain": "globalmfg.com"}),
                "profile": json.dumps({"industry": ["Manufacturing", "Industrial"], "employee_count": 1200, "revenue_min": 200, "revenue_max": 500}),
                "location": json.dumps({"type": "country", "name": ["United States", "Canada"]}),
                "metadata_json": json.dumps({"created_by": "system", "notes": "International manufacturing company"}),
                "deep_research": "{}",
                "red_flags_history": "[]",
            })
            
            await session.commit()
            print(f"  ✅ Created company 1: TechCorp Solutions (ID: {company1_id})")
            print(f"  ✅ Created company 2: Global Manufacturing Inc (ID: {company2_id})\n")
            
            # =====================================================================
            # Create 2 Contacts
            # =====================================================================
            print("👤 Creating contacts...")
            
            await session.execute(text("""
                INSERT INTO contacts (
                    id, firstname, lastname, email, jobtitle, source_id, company_id,
                    webhook_sent, enrichment_status, is_relevant, created_at, updated_at,
                    contact_data, linkedin_data, metadata_json
                ) VALUES (
                    :id, :firstname, :lastname, :email, :jobtitle, :source_id, :company_id,
                    :webhook_sent, :enrichment_status, :is_relevant, :created_at, :updated_at,
                    CAST(:contact_data AS jsonb), CAST(:linkedin_data AS jsonb), CAST(:metadata_json AS jsonb)
                )
            """), {
                "id": contact1_id,
                "firstname": "John",
                "lastname": "Smith",
                "email": "john.smith@techcorp.com",
                "jobtitle": "VP of Sales",
                "source_id": "contact_001",
                "company_id": company1_id,
                "webhook_sent": False,
                "enrichment_status": False,
                "is_relevant": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "contact_data": json.dumps({"firstname": "John", "lastname": "Smith", "email": ["john.smith@techcorp.com"], "jobtitle": "VP of Sales", "phone": ["+1-555-0101"]}),
                "linkedin_data": json.dumps({"linkedin_url": "https://linkedin.com/in/johnsmith"}),
                "metadata_json": json.dumps({"source": "manual", "notes": "Primary decision maker"}),
            })
            
            await session.execute(text("""
                INSERT INTO contacts (
                    id, firstname, lastname, email, jobtitle, source_id, company_id,
                    webhook_sent, enrichment_status, is_relevant, created_at, updated_at,
                    contact_data, linkedin_data, metadata_json
                ) VALUES (
                    :id, :firstname, :lastname, :email, :jobtitle, :source_id, :company_id,
                    :webhook_sent, :enrichment_status, :is_relevant, :created_at, :updated_at,
                    CAST(:contact_data AS jsonb), CAST(:linkedin_data AS jsonb), CAST(:metadata_json AS jsonb)
                )
            """), {
                "id": contact2_id,
                "firstname": "Sarah",
                "lastname": "Johnson",
                "email": "sarah.johnson@globalmfg.com",
                "jobtitle": "Director of Operations",
                "source_id": "contact_002",
                "company_id": company2_id,
                "webhook_sent": False,
                "enrichment_status": False,
                "is_relevant": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "contact_data": json.dumps({"firstname": "Sarah", "lastname": "Johnson", "email": ["sarah.johnson@globalmfg.com"], "jobtitle": "Director of Operations", "phone": ["+1-555-0202"]}),
                "linkedin_data": json.dumps({"linkedin_url": "https://linkedin.com/in/sarahjohnson"}),
                "metadata_json": json.dumps({"source": "manual", "notes": "Key stakeholder"}),
            })
            
            await session.commit()
            print(f"  ✅ Created contact 1: John Smith (ID: {contact1_id})")
            print(f"  ✅ Created contact 2: Sarah Johnson (ID: {contact2_id})\n")
            
            # =====================================================================
            # Create 2 Deals (check if table exists first)
            # =====================================================================
            print("💼 Creating deals...")
            
            # Check if deals table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'deals'
                )
            """))
            deals_table_exists = result.scalar()
            
            if deals_table_exists:
                await session.execute(text("""
                    INSERT INTO deals (
                        id, company_id, name, stage, amount, created_at, updated_at, metadata_json
                    ) VALUES (
                        :id, :company_id, :name, :stage, :amount, :created_at, :updated_at, CAST(:metadata_json AS jsonb)
                    )
                """), {
                    "id": deal1_id,
                    "company_id": company1_id,
                    "name": "Enterprise Software License",
                    "stage": "negotiation",
                    "amount": 150000.00,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata_json": json.dumps({"created_by": "system", "notes": "Large enterprise deal", "probability": 75}),
                })
                
                await session.execute(text("""
                    INSERT INTO deals (
                        id, company_id, name, stage, amount, created_at, updated_at, metadata_json
                    ) VALUES (
                        :id, :company_id, :name, :stage, :amount, :created_at, :updated_at, CAST(:metadata_json AS jsonb)
                    )
                """), {
                    "id": deal2_id,
                    "company_id": company2_id,
                    "name": "Manufacturing Equipment Upgrade",
                    "stage": "proposal",
                    "amount": 500000.00,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata_json": json.dumps({"created_by": "system", "notes": "Major equipment purchase", "probability": 60}),
                })
                
                await session.commit()
                print(f"  ✅ Created deal 1: Enterprise Software License (ID: {deal1_id})")
                print(f"  ✅ Created deal 2: Manufacturing Equipment Upgrade (ID: {deal2_id})\n")
            else:
                print("  ⚠️  Deals table does not exist yet (migration not run). Skipping deals.\n")
                deal1_id = None
                deal2_id = None
            
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
            if deal1_id and deal2_id:
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
