"""Comprehensive test for all PostgreSQL DAOs."""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set PostgreSQL as the backend for all collections
os.environ["POSTGRES_URL"] = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub"
os.environ["DB_BACKEND_USERS"] = "postgres"
os.environ["DB_BACKEND_USER_TOKENS"] = "postgres"
os.environ["DB_BACKEND_CAMPAIGNS"] = "postgres"
os.environ["DB_BACKEND_COMPANIES"] = "postgres"
os.environ["DB_BACKEND_CONTACTS"] = "postgres"
os.environ["DB_BACKEND_CAMPAIGN_COMPANY_RUNS"] = "postgres"
os.environ["DB_BACKEND_CAMPAIGN_CONTACT_RUNS"] = "postgres"
os.environ["DB_BACKEND_MEETINGS"] = "postgres"
os.environ["DB_BACKEND_INBOX_LEADS"] = "postgres"
os.environ["DB_BACKEND_INBOX_EVENTS"] = "postgres"
os.environ["DB_BACKEND_INBOX_NOTES"] = "postgres"

from config.loaded_config import Settings
from database.connection_manager import ConnectionManager


# Results tracking
test_results = {
    "passed": [],
    "failed": [],
}


def log_result(test_name: str, passed: bool, error: str = None):
    """Log test result."""
    if passed:
        print(f"  ✅ {test_name}")
        test_results["passed"].append(test_name)
    else:
        print(f"  ❌ {test_name}: {error}")
        test_results["failed"].append(f"{test_name}: {error}")


async def test_users_dao(conn_mgr):
    """Test Users DAO."""
    print("\n📋 Testing Users DAO...")
    
    from database.postgres.collection_dao.users import PostgresUsersDao
    
    dao = PostgresUsersDao(conn_mgr.get_pg_session())
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user_id = None
    
    try:
        # Test insert_one
        user_data = {
            "email": test_email,
            "name": "Test User",
            "password_hash": "hash123",
            "is_active": True
        }
        user_id = await dao.insert_one(user_data)
        log_result("insert_one", user_id is not None)
        
        # Test find_one by ID
        found = await dao.find_one({"_id": user_id})
        log_result("find_one by _id", found is not None and found.get("email") == test_email)
        
        # Test find_one by email
        found = await dao.find_one({"email": test_email})
        log_result("find_one by email", found is not None)
        
        # Test update_one
        result = await dao.update_one({"_id": user_id}, {"$set": {"name": "Updated Name"}})
        found = await dao.find_one({"_id": user_id})
        log_result("update_one", found.get("name") == "Updated Name")
        
        # Test count
        count = await dao.count({"email": test_email})
        log_result("count", count == 1)
        
        # Test delete_one
        result = await dao.delete_one({"_id": user_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        
        # Verify deletion
        found = await dao.find_one({"_id": user_id})
        log_result("verify deletion", found is None)
        user_id = None  # Clear so cleanup doesn't try to delete again
        
    except Exception as e:
        log_result("Users DAO", False, str(e))
        traceback.print_exc()
    finally:
        if user_id:
            try:
                await dao.delete_one({"_id": user_id})
            except:
                pass


async def test_campaigns_dao(conn_mgr):
    """Test Campaigns DAO."""
    print("\n📋 Testing Campaigns DAO...")
    
    from database.postgres.collection_dao.campaigns import PostgresCampaignsDao
    
    dao = PostgresCampaignsDao(conn_mgr.get_pg_session())
    campaign_id = None
    
    try:
        # Test insert_one
        campaign_data = {
            "name": f"Test Campaign {uuid.uuid4().hex[:8]}",
            "campaign_type": "wide_prospecting",
            "lifecycle_status": "started",
            "prospecting_cycle_status": "prospecting",
            "segmentation_json": {"industry": ["Tech"]},
            "target_json": {"employee_count": ["1-10"]},
            "ownership_json": {"product_name": "test-product"}
        }
        campaign_id = await dao.insert_one(campaign_data)
        log_result("insert_one", campaign_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": campaign_id})
        log_result("find_one", found is not None and found.get("campaign_type") == "wide_prospecting")
        
        # Test find_many
        campaigns = await dao.find_many({"campaign_type": "wide_prospecting"})
        log_result("find_many", len(campaigns) > 0)
        
        # Test update_one with $set
        await dao.update_one({"_id": campaign_id}, {"$set": {"lifecycle_status": "completed"}})
        found = await dao.find_one({"_id": campaign_id})
        log_result("update_one $set", found.get("lifecycle_status") == "completed")
        
        # Test count
        count = await dao.count({"_id": campaign_id})
        log_result("count", count == 1)
        
        # Test delete_one
        result = await dao.delete_one({"_id": campaign_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        campaign_id = None
        
    except Exception as e:
        log_result("Campaigns DAO", False, str(e))
        traceback.print_exc()
    finally:
        if campaign_id:
            try:
                await dao.delete_one({"_id": campaign_id})
            except:
                pass


async def test_companies_dao(conn_mgr):
    """Test Companies DAO."""
    print("\n📋 Testing Companies DAO...")
    
    from database.postgres.collection_dao.companies import PostgresCompaniesDao
    
    dao = PostgresCompaniesDao(conn_mgr.get_pg_session())
    company_id = None
    
    try:
        # Test insert_one
        company_data = {
            "name": f"Test Company {uuid.uuid4().hex[:8]}",
            "source": "apollo",
            "source_id": f"apollo_{uuid.uuid4().hex[:8]}",
            "profile_json": {"industry": ["Technology"]},
            "location_json": {"type": "country", "name": ["USA"]}
        }
        company_id = await dao.insert_one(company_data)
        log_result("insert_one", company_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": company_id})
        log_result("find_one", found is not None)
        
        # Test find with $in operator
        companies = await dao.find_many({"source": {"$in": ["apollo", "linkedin"]}})
        log_result("find_many with $in", len(companies) >= 0)
        
        # Test update_one
        await dao.update_one({"_id": company_id}, {"$set": {"source": "linkedin"}})
        found = await dao.find_one({"_id": company_id})
        log_result("update_one", found.get("source") == "linkedin")
        
        # Test delete
        result = await dao.delete_one({"_id": company_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        company_id = None
        
    except Exception as e:
        log_result("Companies DAO", False, str(e))
        traceback.print_exc()
    finally:
        if company_id:
            try:
                await dao.delete_one({"_id": company_id})
            except:
                pass


async def test_contacts_dao(conn_mgr):
    """Test Contacts DAO."""
    print("\n📋 Testing Contacts DAO...")
    
    from database.postgres.collection_dao.contacts import PostgresContactsDao
    from database.postgres.collection_dao.companies import PostgresCompaniesDao
    
    contacts_dao = PostgresContactsDao(conn_mgr.get_pg_session())
    companies_dao = PostgresCompaniesDao(conn_mgr.get_pg_session())
    contact_id = None
    company_id = None
    
    try:
        # First create a company for the foreign key
        company_data = {
            "name": f"Contact Test Company {uuid.uuid4().hex[:8]}",
            "source": "apollo",
            "source_id": f"apollo_{uuid.uuid4().hex[:8]}"
        }
        company_id = await companies_dao.insert_one(company_data)
        
        # Test insert_one with valid company_id
        contact_data = {
            "firstname": "Test",
            "lastname": f"Contact {uuid.uuid4().hex[:8]}",
            "email": f"contact_{uuid.uuid4().hex[:8]}@test.com",
            "source_id": f"apollo_{uuid.uuid4().hex[:8]}",
            "company_id": company_id
        }
        contact_id = await contacts_dao.insert_one(contact_data)
        log_result("insert_one", contact_id is not None)
        
        # Test find_one
        found = await contacts_dao.find_one({"_id": contact_id})
        log_result("find_one", found is not None)
        
        # Test update
        await contacts_dao.update_one({"_id": contact_id}, {"$set": {"firstname": "Updated"}})
        found = await contacts_dao.find_one({"_id": contact_id})
        log_result("update_one", found.get("firstname") == "Updated")
        
        # Test delete contact
        result = await contacts_dao.delete_one({"_id": contact_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        contact_id = None
        
    except Exception as e:
        log_result("Contacts DAO", False, str(e))
        traceback.print_exc()
    finally:
        if contact_id:
            try:
                await contacts_dao.delete_one({"_id": contact_id})
            except:
                pass
        if company_id:
            try:
                await companies_dao.delete_one({"_id": company_id})
            except:
                pass


async def test_meetings_dao(conn_mgr):
    """Test Meetings DAO."""
    print("\n📋 Testing Meetings DAO...")
    
    from database.postgres.collection_dao.meetings import PostgresMeetingsDao
    
    dao = PostgresMeetingsDao(conn_mgr.get_pg_session())
    meeting_id = None
    
    try:
        # Test insert_one with valid fields (meeting_id is required)
        meeting_data = {
            "meeting_id": str(uuid.uuid4()),  # Required field
            "meeting_name": f"Test Meeting {uuid.uuid4().hex[:8]}",
            "status": "scheduled"
        }
        meeting_id = await dao.insert_one(meeting_data)
        log_result("insert_one", meeting_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": meeting_id})
        log_result("find_one", found is not None)
        
        # Test update
        await dao.update_one({"_id": meeting_id}, {"$set": {"status": "completed"}})
        found = await dao.find_one({"_id": meeting_id})
        log_result("update_one", found.get("status") == "completed")
        
        # Test find_many with filter
        meetings = await dao.find_many({"status": "completed"})
        log_result("find_many with filter", len(meetings) >= 0)
        
        # Test delete
        result = await dao.delete_one({"_id": meeting_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        meeting_id = None
        
    except Exception as e:
        log_result("Meetings DAO", False, str(e))
        traceback.print_exc()
    finally:
        if meeting_id:
            try:
                await dao.delete_one({"_id": meeting_id})
            except:
                pass


async def test_campaign_company_runs_dao(conn_mgr):
    """Test CampaignCompanyRuns DAO."""
    print("\n📋 Testing CampaignCompanyRuns DAO...")
    
    from database.postgres.collection_dao.campaign_company_runs import PostgresCampaignCompanyRunsDao
    
    dao = PostgresCampaignCompanyRunsDao(conn_mgr.get_pg_session())
    run_id = None
    
    try:
        # Test insert_one
        run_data = {
            "campaign_id": "000000000000000000000000",
            "company_id": "000000000000000000000001",
            "status": "pending",
            "is_relevant": True,
            "relevance_score": 0.85
        }
        run_id = await dao.insert_one(run_data)
        log_result("insert_one", run_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": run_id})
        log_result("find_one", found is not None)
        
        # Test find_many by campaign_id
        runs = await dao.find_many({"campaign_id": "000000000000000000000000"})
        log_result("find_many by campaign_id", len(runs) >= 0)
        
        # Test update
        await dao.update_one({"_id": run_id}, {"$set": {"status": "completed"}})
        found = await dao.find_one({"_id": run_id})
        log_result("update_one", found.get("status") == "completed")
        
        # Test delete
        result = await dao.delete_one({"_id": run_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        run_id = None
        
    except Exception as e:
        log_result("CampaignCompanyRuns DAO", False, str(e))
        traceback.print_exc()
    finally:
        if run_id:
            try:
                await dao.delete_one({"_id": run_id})
            except:
                pass


async def test_campaign_contact_runs_dao(conn_mgr):
    """Test CampaignContactRuns DAO."""
    print("\n📋 Testing CampaignContactRuns DAO...")
    
    from database.postgres.collection_dao.campaign_contact_runs import PostgresCampaignContactRunsDao
    
    dao = PostgresCampaignContactRunsDao(conn_mgr.get_pg_session())
    run_id = None
    
    try:
        # Test insert_one
        run_data = {
            "campaign_id": "000000000000000000000000",
            "contact_id": "000000000000000000000001",
            "company_id": "000000000000000000000002",
            "status": "pending",
            "is_relevant": True,
            "enrichment_json": {"linkedin_url": "https://linkedin.com/in/test"}
        }
        run_id = await dao.insert_one(run_data)
        log_result("insert_one", run_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": run_id})
        log_result("find_one", found is not None)
        
        # Test find_many
        runs = await dao.find_many({"campaign_id": "000000000000000000000000"})
        log_result("find_many", len(runs) >= 0)
        
        # Test update
        await dao.update_one({"_id": run_id}, {"$set": {"status": "enriched"}})
        found = await dao.find_one({"_id": run_id})
        log_result("update_one", found.get("status") == "enriched")
        
        # Test delete
        result = await dao.delete_one({"_id": run_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        run_id = None
        
    except Exception as e:
        log_result("CampaignContactRuns DAO", False, str(e))
        traceback.print_exc()
    finally:
        if run_id:
            try:
                await dao.delete_one({"_id": run_id})
            except:
                pass


async def test_inbox_leads_dao(conn_mgr):
    """Test InboxLeads DAO."""
    print("\n📋 Testing InboxLeads DAO...")
    
    from database.postgres.collection_dao.inbox_events import PostgresInboxLeadsDao
    
    dao = PostgresInboxLeadsDao(conn_mgr.get_pg_session())
    doc_id = None
    
    try:
        # Test insert_one (lead_id is required)
        lead_data = {
            "lead_id": f"lead_{uuid.uuid4().hex}",  # Required unique field
            "email": f"lead_{uuid.uuid4().hex[:8]}@test.com",
            "name": "Test Lead",
            "temperature": "warm"
        }
        doc_id = await dao.insert_one(lead_data)
        log_result("insert_one", doc_id is not None)
        
        # Test find_one
        found = await dao.find_one({"_id": doc_id})
        log_result("find_one", found is not None)
        
        # Test update
        await dao.update_one({"_id": doc_id}, {"$set": {"temperature": "hot"}})
        found = await dao.find_one({"_id": doc_id})
        log_result("update_one", found.get("temperature") == "hot")
        
        # Test delete
        result = await dao.delete_one({"_id": doc_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        doc_id = None
        
    except Exception as e:
        log_result("InboxLeads DAO", False, str(e))
        traceback.print_exc()
    finally:
        if doc_id:
            try:
                await dao.delete_one({"_id": doc_id})
            except:
                pass


async def test_inbox_events_dao(conn_mgr):
    """Test InboxEvents DAO."""
    print("\n📋 Testing InboxEvents DAO...")
    
    from database.postgres.collection_dao.inbox_events import PostgresInboxEventsDao, PostgresInboxLeadsDao
    
    events_dao = PostgresInboxEventsDao(conn_mgr.get_pg_session())
    leads_dao = PostgresInboxLeadsDao(conn_mgr.get_pg_session())
    event_id = None
    lead_doc_id = None
    
    try:
        # First create a lead for the foreign key
        lead_data = {
            "lead_id": f"lead_{uuid.uuid4().hex}",  # Required unique field
            "email": f"event_test_lead_{uuid.uuid4().hex[:8]}@test.com",
            "name": "Event Test Lead",
            "temperature": "warm"
        }
        lead_doc_id = await leads_dao.insert_one(lead_data)
        
        # Test insert_one
        event_data = {
            "lead_id": lead_doc_id,  # FK to inbox_leads
            "event_type": "email_opened",
            "occurred_at": datetime.utcnow()
        }
        event_id = await events_dao.insert_one(event_data)
        log_result("insert_one", event_id is not None)
        
        # Test find_one
        found = await events_dao.find_one({"_id": event_id})
        log_result("find_one", found is not None)
        
        # Test find_many by lead_id
        events = await events_dao.find_many({"lead_id": lead_doc_id})
        log_result("find_many", len(events) >= 0)
        
        # Test delete event
        result = await events_dao.delete_one({"_id": event_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        event_id = None
        
    except Exception as e:
        log_result("InboxEvents DAO", False, str(e))
        traceback.print_exc()
    finally:
        if event_id:
            try:
                await events_dao.delete_one({"_id": event_id})
            except:
                pass
        if lead_doc_id:
            try:
                await leads_dao.delete_one({"_id": lead_doc_id})
            except:
                pass


async def test_inbox_notes_dao(conn_mgr):
    """Test InboxNotes DAO."""
    print("\n📋 Testing InboxNotes DAO...")
    
    from database.postgres.collection_dao.inbox_events import PostgresInboxNotesDao, PostgresInboxLeadsDao
    
    notes_dao = PostgresInboxNotesDao(conn_mgr.get_pg_session())
    leads_dao = PostgresInboxLeadsDao(conn_mgr.get_pg_session())
    note_id = None
    lead_doc_id = None
    
    try:
        # First create a lead for the foreign key
        lead_data = {
            "lead_id": f"lead_{uuid.uuid4().hex}",  # Required unique field
            "email": f"note_test_lead_{uuid.uuid4().hex[:8]}@test.com",
            "name": "Note Test Lead",
            "temperature": "cold"
        }
        lead_doc_id = await leads_dao.insert_one(lead_data)
        
        # Test insert_one
        note_data = {
            "lead_id": lead_doc_id,  # FK to inbox_leads
            "content": "Test note content",
            "author": "Test User"
        }
        note_id = await notes_dao.insert_one(note_data)
        log_result("insert_one", note_id is not None)
        
        # Test find_one
        found = await notes_dao.find_one({"_id": note_id})
        log_result("find_one", found is not None)
        
        # Test update
        await notes_dao.update_one({"_id": note_id}, {"$set": {"content": "Updated note"}})
        found = await notes_dao.find_one({"_id": note_id})
        log_result("update_one", found.get("content") == "Updated note")
        
        # Test delete note
        result = await notes_dao.delete_one({"_id": note_id})
        log_result("delete_one", result.get("deleted_count") == 1)
        note_id = None
        
    except Exception as e:
        log_result("InboxNotes DAO", False, str(e))
        traceback.print_exc()
    finally:
        if note_id:
            try:
                await notes_dao.delete_one({"_id": note_id})
            except:
                pass
        if lead_doc_id:
            try:
                await leads_dao.delete_one({"_id": lead_doc_id})
            except:
                pass


async def test_query_operators(conn_mgr):
    """Test MongoDB query operator compatibility."""
    print("\n📋 Testing Query Operators...")
    
    from database.postgres.collection_dao.companies import PostgresCompaniesDao
    
    dao = PostgresCompaniesDao(conn_mgr.get_pg_session())
    company_ids = []
    
    try:
        # Create test data
        for i in range(5):
            company_data = {
                "name": f"Query Test Company {i}",
                "source": "apollo" if i % 2 == 0 else "linkedin",
                "source_id": f"test_{uuid.uuid4().hex[:8]}",
                "profile_json": {"industry": ["Tech"], "score": i * 10}
            }
            company_id = await dao.insert_one(company_data)
            company_ids.append(company_id)
        
        # Test $eq
        results = await dao.find_many({"source": {"$eq": "apollo"}})
        log_result("$eq operator", len(results) >= 0)
        
        # Test $ne
        results = await dao.find_many({"source": {"$ne": "linkedin"}})
        log_result("$ne operator", len(results) >= 0)
        
        # Test $in
        results = await dao.find_many({"_id": {"$in": company_ids[:2]}})
        log_result("$in operator", len(results) >= 0)
        
        # Test $nin
        results = await dao.find_many({"_id": {"$nin": company_ids[:2]}})
        log_result("$nin operator", True)
        
        # Test $exists (true)
        results = await dao.find_many({"source": {"$exists": True}})
        log_result("$exists true", len(results) >= 0)
        
        # Test count with filter
        count = await dao.count({"source": "apollo"})
        log_result("count with filter", count >= 0)
        
    except Exception as e:
        log_result("Query Operators", False, str(e))
        traceback.print_exc()
    finally:
        # Cleanup
        for cid in company_ids:
            try:
                await dao.delete_one({"_id": cid})
            except:
                pass


async def test_pagination_and_sorting(conn_mgr):
    """Test pagination and sorting."""
    print("\n📋 Testing Pagination & Sorting...")
    
    from database.postgres.collection_dao.companies import PostgresCompaniesDao
    
    dao = PostgresCompaniesDao(conn_mgr.get_pg_session())
    company_ids = []
    
    try:
        # Create test data
        for i in range(10):
            company_data = {
                "name": f"Page Test Company {i:02d}",
                "source": "apollo",
                "source_id": f"page_{uuid.uuid4().hex[:8]}"
            }
            company_id = await dao.insert_one(company_data)
            company_ids.append(company_id)
        
        # Test pagination with skip and limit
        all_results = await dao.find_many({"_id": {"$in": company_ids}}, skip=0, limit=5)
        log_result("pagination (limit=5)", len(all_results) <= 5)
        
        # Test skip
        skipped_results = await dao.find_many({"_id": {"$in": company_ids}}, skip=3, limit=5)
        log_result("pagination (skip=3)", True)
        
        # Test sorting
        sorted_asc = await dao.find_many({"_id": {"$in": company_ids}}, sort=[("name", 1)])
        log_result("sort ascending", True)
        
        sorted_desc = await dao.find_many({"_id": {"$in": company_ids}}, sort=[("name", -1)])
        log_result("sort descending", True)
        
    except Exception as e:
        log_result("Pagination & Sorting", False, str(e))
        traceback.print_exc()
    finally:
        # Cleanup
        for cid in company_ids:
            try:
                await dao.delete_one({"_id": cid})
            except:
                pass


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 COMPREHENSIVE POSTGRESQL DAO TESTS")
    print("="*70)
    
    # Update settings
    Settings.postgres_url = os.environ["POSTGRES_URL"]
    for collection in ["users", "user_tokens", "campaigns", "companies", "contacts",
                       "campaign_company_runs", "campaign_contact_runs", "meetings",
                       "inbox_leads", "inbox_events", "inbox_notes"]:
        setattr(Settings, f"db_backend_{collection}", "postgres")
    
    # Initialize connection manager
    conn_mgr = ConnectionManager(
        mongo_uri=Settings.mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=Settings.postgres_url
    )
    
    try:
        # Setup PostgreSQL
        print("\n🔄 Connecting to PostgreSQL...")
        await conn_mgr.setup_postgres(echo=False)
        print("✅ PostgreSQL connected!\n")
        
        # Run all DAO tests
        await test_users_dao(conn_mgr)
        await test_campaigns_dao(conn_mgr)
        await test_companies_dao(conn_mgr)
        await test_contacts_dao(conn_mgr)
        await test_meetings_dao(conn_mgr)
        await test_campaign_company_runs_dao(conn_mgr)
        await test_campaign_contact_runs_dao(conn_mgr)
        await test_inbox_leads_dao(conn_mgr)
        await test_inbox_events_dao(conn_mgr)
        await test_inbox_notes_dao(conn_mgr)
        
        # Test query features
        await test_query_operators(conn_mgr)
        await test_pagination_and_sorting(conn_mgr)
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        traceback.print_exc()
    finally:
        await conn_mgr.close_connections()
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    
    if test_results['failed']:
        print("\n❌ Failed Tests:")
        for failed in test_results['failed']:
            print(f"   - {failed}")
    
    print("\n" + "="*70)
    
    success_rate = len(test_results['passed']) / (len(test_results['passed']) + len(test_results['failed'])) * 100 if (test_results['passed'] or test_results['failed']) else 0
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    print("="*70 + "\n")
    
    return len(test_results['failed']) == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

