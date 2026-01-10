#!/usr/bin/env python
"""Test AI Agents Service with PostgreSQL support.

This script tests the CampaignService, CompanyService, and ContactService
to verify they work correctly with both MongoDB and PostgreSQL backends.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable for PostgreSQL
os.environ.setdefault("POSTGRES_URL", "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub")

from config.loaded_config import loaded_config, Settings


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"      {details}")


async def setup_connections():
    """Setup database connections."""
    from database.connection_manager import ConnectionManager
    
    # Initialize connection manager
    mongo_uri = os.getenv("MONGO_LINKEDIN_SDR_READ_WRITE", "mongodb://localhost:27017")
    postgres_url = os.getenv("POSTGRES_URL", "postgresql+asyncpg://agent_hub:agent_hub@localhost:5433/agent_hub")
    
    connection_manager = ConnectionManager(
        mongo_uri=mongo_uri,
        db_name="linkedin_sdr",
        postgres_url=postgres_url
    )
    
    # Always setup PostgreSQL for testing (since we'll test both backends)
    await connection_manager.setup_postgres(echo=False)
    
    # Set in loaded_config
    loaded_config.connection_manager = connection_manager
    
    return connection_manager


async def test_campaign_service_mongodb():
    """Test CampaignService with MongoDB backend."""
    print("\n" + "=" * 60)
    print("📋 Testing CampaignService (MongoDB)")
    print("=" * 60)
    
    # Ensure MongoDB backend
    original_backend = Settings.db_backend_campaigns
    Settings.db_backend_campaigns = "mongo"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import CampaignService
        from ai_agents.leadgen.schemas.ai_agents import Campaigns
        
        service = CampaignService()
        
        # Test get_campaigns
        query_params = Campaigns(page=1, limit=5)
        result = await service.get_campaigns(query_params)
        
        log_result(
            "get_campaigns (MongoDB)",
            isinstance(result, dict) and "campaigns" in result,
            f"Found {len(result.get('campaigns', []))} campaigns"
        )
        
        # Test get_campaign_details (if any campaigns exist)
        if result.get("campaigns"):
            campaign_id = result["campaigns"][0].get("_id")
            if campaign_id:
                try:
                    details = await service.get_campaign_details(campaign_id)
                    log_result(
                        "get_campaign_details (MongoDB)",
                        details.get("campaign") is not None,
                        f"Campaign name: {details.get('campaign', {}).get('name', 'N/A')}"
                    )
                except Exception as e:
                    log_result("get_campaign_details (MongoDB)", False, str(e))
        
        return True
    except Exception as e:
        log_result("CampaignService (MongoDB)", False, str(e))
        return False
    finally:
        Settings.db_backend_campaigns = original_backend


async def test_campaign_service_postgres():
    """Test CampaignService with PostgreSQL backend."""
    print("\n" + "=" * 60)
    print("📋 Testing CampaignService (PostgreSQL)")
    print("=" * 60)
    
    # Ensure PostgreSQL backend
    original_backend = Settings.db_backend_campaigns
    Settings.db_backend_campaigns = "postgres"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import CampaignService
        from ai_agents.leadgen.schemas.ai_agents import Campaigns
        
        service = CampaignService()
        
        # Test get_campaigns
        query_params = Campaigns(page=1, limit=5)
        result = await service.get_campaigns(query_params)
        
        log_result(
            "get_campaigns (PostgreSQL)",
            isinstance(result, dict) and "campaigns" in result,
            f"Found {len(result.get('campaigns', []))} campaigns"
        )
        
        # Test get_prospecting_campaigns
        prospecting_result = await service.get_prospecting_campaigns(page=1, limit=5)
        log_result(
            "get_prospecting_campaigns (PostgreSQL)",
            isinstance(prospecting_result, dict) and "campaigns" in prospecting_result,
            f"Found {len(prospecting_result.get('campaigns', []))} prospecting campaigns"
        )
        
        return True
    except Exception as e:
        log_result("CampaignService (PostgreSQL)", False, str(e))
        return False
    finally:
        Settings.db_backend_campaigns = original_backend


async def test_company_service_mongodb():
    """Test CompanyService with MongoDB backend."""
    print("\n" + "=" * 60)
    print("📋 Testing CompanyService (MongoDB)")
    print("=" * 60)
    
    # Ensure MongoDB backend
    original_companies = Settings.db_backend_companies
    original_ccr = Settings.db_backend_campaign_company_runs
    Settings.db_backend_companies = "mongo"
    Settings.db_backend_campaign_company_runs = "mongo"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import CompanyService
        from ai_agents.leadgen.schemas.ai_agents import Companies
        
        service = CompanyService()
        
        # Test get_companies
        query_params = Companies(page=1, limit=5)
        result = await service.get_companies(query_params)
        
        log_result(
            "get_companies (MongoDB)",
            isinstance(result, dict) and "companies" in result,
            f"Found {len(result.get('companies', []))} companies"
        )
        
        # Test get_company_details (if any companies exist)
        if result.get("companies"):
            company_id = result["companies"][0].get("_id")
            if company_id:
                try:
                    details = await service.get_company_details(company_id)
                    log_result(
                        "get_company_details (MongoDB)",
                        details.get("company") is not None,
                        f"Company name: {details.get('company', {}).get('identifiers', {}).get('name', 'N/A')}"
                    )
                except Exception as e:
                    log_result("get_company_details (MongoDB)", False, str(e))
        
        return True
    except Exception as e:
        log_result("CompanyService (MongoDB)", False, str(e))
        return False
    finally:
        Settings.db_backend_companies = original_companies
        Settings.db_backend_campaign_company_runs = original_ccr


async def test_company_service_postgres():
    """Test CompanyService with PostgreSQL backend."""
    print("\n" + "=" * 60)
    print("📋 Testing CompanyService (PostgreSQL)")
    print("=" * 60)
    
    # Ensure PostgreSQL backend
    original_companies = Settings.db_backend_companies
    original_ccr = Settings.db_backend_campaign_company_runs
    Settings.db_backend_companies = "postgres"
    Settings.db_backend_campaign_company_runs = "postgres"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import CompanyService
        from ai_agents.leadgen.schemas.ai_agents import Companies
        
        service = CompanyService()
        
        # Test get_companies
        query_params = Companies(page=1, limit=5)
        result = await service.get_companies(query_params)
        
        log_result(
            "get_companies (PostgreSQL)",
            isinstance(result, dict) and "companies" in result,
            f"Found {len(result.get('companies', []))} companies"
        )
        
        return True
    except Exception as e:
        log_result("CompanyService (PostgreSQL)", False, str(e))
        return False
    finally:
        Settings.db_backend_companies = original_companies
        Settings.db_backend_campaign_company_runs = original_ccr


async def test_contact_service_mongodb():
    """Test ContactService with MongoDB backend."""
    print("\n" + "=" * 60)
    print("📋 Testing ContactService (MongoDB)")
    print("=" * 60)
    
    # Ensure MongoDB backend
    original_contacts = Settings.db_backend_contacts
    original_ccr = Settings.db_backend_campaign_contact_runs
    Settings.db_backend_contacts = "mongo"
    Settings.db_backend_campaign_contact_runs = "mongo"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import ContactService
        
        service = ContactService()
        
        # Service is initialized successfully
        log_result(
            "ContactService initialization (MongoDB)",
            service.contacts_dao is not None and service.campaign_contact_run_dao is not None,
            "DAOs initialized successfully"
        )
        
        return True
    except Exception as e:
        log_result("ContactService (MongoDB)", False, str(e))
        return False
    finally:
        Settings.db_backend_contacts = original_contacts
        Settings.db_backend_campaign_contact_runs = original_ccr


async def test_contact_service_postgres():
    """Test ContactService with PostgreSQL backend."""
    print("\n" + "=" * 60)
    print("📋 Testing ContactService (PostgreSQL)")
    print("=" * 60)
    
    # Ensure PostgreSQL backend
    original_contacts = Settings.db_backend_contacts
    original_ccr = Settings.db_backend_campaign_contact_runs
    Settings.db_backend_contacts = "postgres"
    Settings.db_backend_campaign_contact_runs = "postgres"
    
    try:
        from ai_agents.leadgen.services.ai_agents_service import ContactService
        
        service = ContactService()
        
        # Service is initialized successfully
        log_result(
            "ContactService initialization (PostgreSQL)",
            service.contacts_dao is not None and service.campaign_contact_run_dao is not None,
            "DAOs initialized successfully"
        )
        
        return True
    except Exception as e:
        log_result("ContactService (PostgreSQL)", False, str(e))
        return False
    finally:
        Settings.db_backend_contacts = original_contacts
        Settings.db_backend_campaign_contact_runs = original_ccr


async def test_factory_switching():
    """Test that factory correctly switches between MongoDB and PostgreSQL."""
    print("\n" + "=" * 60)
    print("📋 Testing DAO Factory Switching")
    print("=" * 60)
    
    try:
        from database.factory import (
            get_campaigns_dao,
            get_companies_dao,
            get_contacts_dao,
            get_campaign_company_runs_dao,
            get_campaign_contact_runs_dao
        )
        from database.collection_dao.campaigns import CampaignsDao as MongoCampaignsDao
        from database.postgres.collection_dao.campaigns import PostgresCampaignsDao
        
        # Test MongoDB
        Settings.db_backend_campaigns = "mongo"
        mongo_dao = get_campaigns_dao(loaded_config.connection_manager)
        is_mongo = isinstance(mongo_dao, MongoCampaignsDao)
        log_result(
            "Factory returns MongoDB DAO when db_backend=mongo",
            is_mongo,
            f"DAO type: {type(mongo_dao).__name__}"
        )
        
        # Test PostgreSQL
        Settings.db_backend_campaigns = "postgres"
        postgres_dao = get_campaigns_dao(loaded_config.connection_manager)
        is_postgres = isinstance(postgres_dao, PostgresCampaignsDao)
        log_result(
            "Factory returns PostgreSQL DAO when db_backend=postgres",
            is_postgres,
            f"DAO type: {type(postgres_dao).__name__}"
        )
        
        return is_mongo and is_postgres
    except Exception as e:
        log_result("DAO Factory Switching", False, str(e))
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 AI Agents Service PostgreSQL Support Test Suite")
    print("=" * 70)
    
    # Setup connections
    try:
        await setup_connections()
        log_result("Database connections setup", True)
    except Exception as e:
        log_result("Database connections setup", False, str(e))
        return
    
    results = []
    
    # Test factory switching
    results.append(await test_factory_switching())
    
    # Test CampaignService
    results.append(await test_campaign_service_mongodb())
    results.append(await test_campaign_service_postgres())
    
    # Test CompanyService
    results.append(await test_company_service_mongodb())
    results.append(await test_company_service_postgres())
    
    # Test ContactService
    results.append(await test_contact_service_mongodb())
    results.append(await test_contact_service_postgres())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Close connections
    if loaded_config.connection_manager:
        await loaded_config.connection_manager.close_connections()
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

