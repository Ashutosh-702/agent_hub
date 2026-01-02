"""Message handlers for leadgen Kafka consumers."""
from time import sleep
from typing import Any, Optional
import json
from datetime import datetime
from database.connection_manager import ConnectionManager
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from integrations.integration_orchestrator import IntegrationOrchestrator
from integrations.apollo.apollo_api import ApolloAPIClient
from global_utils.chronos_utils import (
    generate_default_eta_expression,
    schedule_lusha_company_collection
)
from integrations.lusha.company_saver import CompanySaver
from config.logging import logger
from integrations.apollo.apollo_helper import ApolloHelper
from integrations.apollo.schema import ApolloResponseSchema
from webhooks.contact_hubspot_webhook import ContactHubspotWebhook
from database.collection_dao.contacts import ContactsDao
def convert_objectid_to_string(payload: dict) -> dict:
    """Convert ObjectId values to strings for JSON serialization."""
    converted_payload = payload.copy()

    for key, value in converted_payload.items():

        if hasattr(value, 'str'):  # Check if it's an ObjectId
            converted_payload[key] = str(value)

    return converted_payload


async def initialize_consumer_connections():
    """Initialize database connections for consumer context."""
    
    if not loaded_config.connection_manager:
        logger.info("🔄 Initializing database connection for consumer...")
        loaded_config.connection_manager = ConnectionManager(
            mongo_uri=loaded_config.mongo_uri, 
            db_name="linkedin_sdr"
        )
        logger.info("✅ Database connection initialized for consumer")


async def leadgen_batch_processing_handler(message: Any):
    """
    Default handler for leadgen batch processing messages.
    This gets replaced by EventBridge consumer with custom handler.
    """
    try:
        # Try different ways to extract the payload
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']

        else:
            logger.error(f"🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")  # Now we get campaign_id instead of form_data
        
        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_company_search":
            logger.error(f"❌ Unknown action: {action}")
            return
        
        logger.info(f"🔄 Processing company search: {request_id}")
        
        # Process the company search using campaign_id
        await process_leadgen_message(request_id, campaign_id)
        
    except Exception as e:
        logger.error(f"❌ Error handling leadgen message: {e}")
        import traceback
        traceback.print_exc()
        raise

async def leadgen_prospecting_job_processing_handler(message: Any):
    try:
        # Try different ways to extract the payload
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']

        else:
            logger.error(f"🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")  # Now we get campaign_id instead of form_data
        
        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_prospecting_job":
            logger.error(f"❌ Unknown action: {action}")
            return
        
        logger.info(f"🔄 Processing prospecting job: {request_id}")
        await process_prospecting_job(request_id, campaign_id)
        
    except Exception as e:
        logger.error(f"❌ Error handling leadgen message: {e}")
        import traceback
        traceback.print_exc()
        raise


async def leadgen_single_company_processing_handler(message: Any):
    """Handler for single company URL campaigns - searches Apollo by domain."""
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        else:
            logger.error("🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received single company message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return

        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")

        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return

        if action != "process_single_company":
            logger.error(f"❌ Unknown action: {action}")
            return

        logger.info(f"🔄 Processing single company for campaign: {campaign_id}")
        await process_single_company(request_id, campaign_id)

    except Exception as e:
        logger.error(f"❌ Error handling single company message: {e}")
        import traceback
        traceback.print_exc()
        raise


async def leadgen_csv_import_processing_handler(message: Any):
    """Handler for CSV import campaigns - batch searches Apollo by domain."""
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        else:
            logger.error("🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received CSV import message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return

        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")

        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return

        if action != "process_csv_import":
            logger.error(f"❌ Unknown action: {action}")
            return

        logger.info(f"🔄 Processing CSV import for campaign: {campaign_id}")
        await process_csv_import(request_id, campaign_id)

    except Exception as e:
        logger.error(f"❌ Error handling CSV import message: {e}")
        import traceback
        traceback.print_exc()
        raise


async def process_csv_import(request_id: str, campaign_id: str):
    """
    Process CSV import campaign - optimized for large datasets (10,000+ domains).
    
    Strategy:
    1. Read domains from campaign.csv_import.domains
    2. Check for existing companies in batches
    3. Bulk insert new companies and mappings
    4. Process Apollo enrichment with rate limiting
    5. Update progress periodically
    """
    import asyncio
    
    BATCH_SIZE = 100  # Process domains in batches of 100
    APOLLO_DELAY = 0.5  # 500ms delay between Apollo calls to respect rate limits
    PROGRESS_UPDATE_INTERVAL = 10  # Update progress every N domains
    
    campaigns_dao = None
    companies_dao = None
    campaign_company_runs_dao = None
    
    try:
        logger.info(f"🔍 Processing CSV import: {request_id}")
        logger.info(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        apollo_client = ApolloAPIClient()
        
        # 1. Fetch campaign to get domains list
        campaign_data = await campaigns_dao.get_campaign(campaign_id)
        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return
        
        domains = campaign_data.get("csv_import", {}).get("domains", [])
        if not domains:
            logger.warning(f"⚠️ No domains found in campaign {campaign_id}")
            await campaigns_dao.update_campaign(campaign_id, {
                "csv_import.status": "completed",
                "prospecting_cycle.status": "company_qualification",
                "lifecycle.status": "company_qualification",
                "metadata.updated_at": datetime.utcnow()
            })
            return
        
        total_count = len(domains)
        processed_count = 0
        existing_count = 0
        already_enriched_count = 0  # Existing companies that already had Apollo data (skipped Apollo)
        new_count = 0
        success_count = 0
        failed_count = 0
        
        logger.info(f"📋 Processing {total_count} domains for campaign {campaign_id}")
        
        # Update campaign status to processing
        await campaigns_dao.update_campaign(campaign_id, {
            "csv_import.status": "processing",
            "csv_import.total_count": total_count,
            "csv_import.processed_count": 0,
            "metadata.updated_at": datetime.utcnow()
        })
        
        # 2. Process domains in batches
        for batch_start in range(0, total_count, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_count)
            batch_domains = domains[batch_start:batch_end]
            
            logger.info(f"📦 Processing batch {batch_start + 1}-{batch_end} of {total_count}")
            
            for domain in batch_domains:
                try:
                    # Check if company already exists
                    existing_company = await companies_dao.get_company_by_source_domain(domain)
                    
                    if existing_company:
                        company_id = str(existing_company.get("_id"))
                        
                        # Check if already enriched via Apollo (has source_id)
                        source_id = existing_company.get("identifiers", {}).get("source_id", "")
                        already_enriched = bool(source_id and source_id.strip())
                        
                        if already_enriched:
                            # Company already has Apollo data - just create mapping, skip Apollo search
                            enrichment_source = "existing_enriched_company"
                            already_enriched_count += 1
                            logger.info(f"✅ Company already enriched for domain {domain}, skipping Apollo search")
                        else:
                            # Company exists but not enriched - search Apollo
                            enrichment_source = "apollo_domain_search"
                            logger.info(f"🔍 Company exists but not enriched for domain {domain}, searching Apollo")
                            
                            try:
                                search_result = await apollo_client.apollo_company_search_by_domain_api(domain)
                                
                                if search_result.get('status_code') == 200:
                                    organizations = search_result.get('results', {}).get('organizations', [])
                                    
                                    if organizations:
                                        org = organizations[0]
                                        # Update company with Apollo data
                                        company_update = {
                                            "identifiers.name": org.get("name", ""),
                                            "identifiers.source_id": org.get("id", ""),
                                            "identifiers.website_url": org.get("website_url", f"https://{domain}"),
                                            "source": "apollo",
                                            "metadata.api_response": org,
                                            "metadata.updated_at": datetime.utcnow(),
                                            "location.name": org.get("country", ""),
                                            "location.type": "country",
                                            "profile.industry": org.get("industry", ""),
                                            "profile.employee_count": org.get("organization_headcount", "")
                                        }
                                        await companies_dao.update_company(company_id, company_update)
                                        logger.info(f"✅ Enriched existing company for domain {domain}")
                                
                                # Rate limiting for Apollo API
                                await asyncio.sleep(APOLLO_DELAY)
                                
                            except Exception as apollo_error:
                                logger.warning(f"⚠️ Apollo search failed for {domain}: {apollo_error}")
                                enrichment_source = "apollo_search_failed"
                        
                        # Create campaign_company_run mapping
                        campaign_company_run = {
                            "campaign_id": str(campaign_id),
                            "company_id": company_id,
                            "company_status": False,
                            "linkedin_contact_status": False,
                            "is_relevant": True,
                            "metadata": {
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                                "source": "csv_import",
                                "enrichment_source": enrichment_source,
                                "domain": domain
                            }
                        }
                        await campaign_company_runs_dao.create_campaign_company_run(campaign_company_run)
                        existing_count += 1
                        success_count += 1
                    else:
                        # Company doesn't exist - create placeholder, search Apollo, update
                        company_data = {
                            "identifiers": {
                                "name": "",
                                "source_domain": domain,
                                "source_id": "",
                                "website_url": f"https://{domain}"
                            },
                            "source": "csv_import",
                            "webhook_sent": False,
                            "metadata": {
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                                "api_response": {}
                            },
                            "location": {"name": "", "type": ""},
                            "profile": {
                                "employee_count": [],
                                "industry": [],
                                "revenue_max": "",
                                "revenue_min": ""
                            }
                        }
                        company_id = await companies_dao.create_company(company_data)
                        new_count += 1
                        
                        enrichment_source = "apollo_domain_search"
                        
                        # Search Apollo by domain (with rate limiting)
                        try:
                            search_result = await apollo_client.apollo_company_search_by_domain_api(domain)
                            
                            if search_result.get('status_code') == 200:
                                organizations = search_result.get('results', {}).get('organizations', [])
                                
                                if organizations:
                                    org = organizations[0]
                                    # Update company with Apollo data
                                    company_update = {
                                        "identifiers.name": org.get("name", ""),
                                        "identifiers.source_id": org.get("id", ""),
                                        "identifiers.website_url": org.get("website_url", f"https://{domain}"),
                                        "source": "apollo",
                                        "metadata.api_response": org,
                                        "metadata.updated_at": datetime.utcnow(),
                                        "location.name": org.get("country", ""),
                                        "location.type": "country",
                                        "profile.industry": org.get("industry", ""),
                                        "profile.employee_count": org.get("organization_headcount", "")
                                    }
                                    await companies_dao.update_company(company_id, company_update)
                                else:
                                    enrichment_source = "apollo_not_found"
                            else:
                                enrichment_source = "apollo_api_failed"
                            
                            # Rate limiting for Apollo API
                            await asyncio.sleep(APOLLO_DELAY)
                            
                        except Exception as apollo_error:
                            logger.warning(f"⚠️ Apollo search failed for {domain}: {apollo_error}")
                            enrichment_source = "apollo_search_failed"
                        
                        # Create campaign_company_run (always mark as relevant so user sees it)
                        campaign_company_run = {
                            "campaign_id": str(campaign_id),
                            "company_id": str(company_id),
                            "company_status": False,
                            "linkedin_contact_status": False,
                            "is_relevant": True,
                            "metadata": {
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                                "source": "csv_import",
                                "enrichment_source": enrichment_source,
                                "domain": domain
                            }
                        }
                        await campaign_company_runs_dao.create_campaign_company_run(campaign_company_run)
                        success_count += 1
                    
                except Exception as domain_error:
                    logger.error(f"❌ Error processing domain {domain}: {domain_error}")
                    failed_count += 1
                
                processed_count += 1
                
                # Update progress periodically
                if processed_count % PROGRESS_UPDATE_INTERVAL == 0 or processed_count == total_count:
                    await campaigns_dao.update_campaign(campaign_id, {
                        "csv_import.processed_count": processed_count,
                        "csv_import.existing_count": existing_count,
                        "csv_import.already_enriched_count": already_enriched_count,
                        "csv_import.new_count": new_count,
                        "metadata.updated_at": datetime.utcnow()
                    })
                    logger.info(f"📊 Progress: {processed_count}/{total_count} ({already_enriched_count} cached, {existing_count - already_enriched_count} enriched existing, {new_count} new)")
        
        # 3. All done - update campaign status
        await campaigns_dao.update_campaign(campaign_id, {
            "csv_import.status": "completed",
            "csv_import.processed_count": processed_count,
            "csv_import.existing_count": existing_count,
            "csv_import.already_enriched_count": already_enriched_count,
            "csv_import.new_count": new_count,
            "csv_import.success_count": success_count,
            "csv_import.failed_count": failed_count,
            "prospecting_cycle.status": "company_qualification",
            "lifecycle.status": "company_qualification",
            "metadata.updated_at": datetime.utcnow()
        })
        
        apollo_calls_made = new_count + (existing_count - already_enriched_count)
        logger.info(f"✅ CSV import completed for campaign {campaign_id}: {success_count} success, {failed_count} failed, {already_enriched_count} skipped (cached), {apollo_calls_made} Apollo calls made")
        
    except Exception as e:
        logger.error(f"❌ Error processing CSV import for campaign {campaign_id}: {e}")
        import traceback
        traceback.print_exc()
        
        if campaigns_dao:
            await campaigns_dao.update_campaign(campaign_id, {
                "csv_import.status": "failed",
                "csv_import.error": str(e),
                "metadata.updated_at": datetime.utcnow()
            })
        raise


async def leadgen_company_qualification_ai_processing_handler(message: Any):
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        else:
            logger.error("🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return

        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")

        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return

        if action != "process_company_qualification_ai":
            logger.error(f"❌ Unknown action: {action}")
            return

        logger.info(f"🔄 Processing AI company qualification: {request_id}")
        await process_company_qualification_ai(request_id, campaign_id)
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        await campaigns_dao.update_campaign( campaign_id, {"prospecting_cycle.status":"contact_qualification"})
        
    except Exception as e:
        logger.error(f"❌ Error handling leadgen message: {e}")
        import traceback
        traceback.print_exc()
        raise


async def leadgen_apollo_contact_list_processing_handler(message: Any):
    """
    Handler for get_apollo_contact_list events.
    Expands campaign_id -> relevant company_ids and then reuses contacts enrichment logic (Apollo fetch).
    """
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        else:
            logger.error("🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return

        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")
        slack_metadata = payload.get("slack_metadata", {})

        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in message")
            return

        if action != "get_apollo_contact_list" and action != "enrich_apollo_contact_list":
            logger.error(f"❌ Unknown action: {action}")
            return

        logger.info(f"🔄 Processing Apollo contact list for campaign: {campaign_id}")
        await process_apollo_contact_list(request_id, campaign_id, slack_metadata, action)

    except Exception as e:
        logger.error(f"❌ Error handling apollo contact list message: {e}")
        import traceback
        traceback.print_exc()
        raise


async def process_apollo_contact_list(request_id: str, campaign_id: str, slack_metadata: dict, action: str):
    """
    Fetch Apollo contacts for all relevant companies in a campaign.
    This reuses `process_contacts_enrichment` (which calls ApolloHelper.get_company_contacts).
    """
    try:
        await initialize_consumer_connections()
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(campaign_id)
        
        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return
        orchestrator = IntegrationOrchestrator(campaign_data)
        if action == "get_apollo_contact_list":
            await orchestrator.fetch_apollo_contact_list()
        elif action == "enrich_apollo_contact_list":
            await orchestrator.enrich_apollo_contact_list()

    except Exception as e:
        logger.error(f"❌ Error processing apollo contact list {request_id}: {e}")
        raise

async def process_company_qualification_ai(request_id: str, campaign_id: str):
    """Re-run AI company qualification (relevance check) using updated campaign prompts."""
    try:
        logger.info(f"🔍 Processing request: {request_id}")
        logger.info(f"📋 Campaign ID: {campaign_id}")

        await initialize_consumer_connections()

        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(campaign_id)

        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return

        orchestrator = IntegrationOrchestrator(campaign_data)
        # Uses the campaign config (including updated prompts.web) to re-run relevance check.
        await orchestrator.relevance_check.company_relevance_check(campaign_id, request_id=request_id)
        update_campaign_status = await campaigns_dao.update_campaign(campaign_id, {"prospecting_cycle.status": "company_qualification"})
        if update_campaign_status:
            logger.info(f"✅ Updated campaign status to company_qualification: {campaign_id}")
        else:
            logger.error(f"❌ Failed to update campaign status to company_qualification: {campaign_id}")
        logger.info(f"✅ Completed AI company qualification: {request_id}")

    except Exception as e:
        logger.error(f"❌ Error processing AI company qualification {request_id}: {e}")
        raise

async def process_prospecting_job(request_id: str, campaign_id: str):
    """Process a single prospecting job request using campaign_id."""
    try:
        logger.info(f"🔍 Processing request: {request_id}")
        logger.info(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        # Fetch campaign data from database using campaign_id
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(campaign_id)
        
        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return
        
        logger.info(f"🔍 DEBUG: Campaign data structure: {campaign_data}")
        logger.info(f"📊 Industry: {campaign_data.get('segmentation', {}).get('industry', 'Unknown')}")
        logger.info(f"📍 Location: {campaign_data.get('target', {}).get('location', {}).get('names', 'Unknown')}")
        
        # Run the prospecting job pipeline for this campaign
        orchestrator = IntegrationOrchestrator(campaign_data)
        await orchestrator.process_prospecting_job()
        
        logger.info(f"✅ Completed processing: {request_id}")
        # print(f"📝 Result: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error processing request {request_id}: {e}")
        raise 


async def process_single_company(request_id: str, campaign_id: str):
    """
    Process a single company URL campaign.
    1. Fetch campaign to get domain from single_company.domain
    2. Fetch campaign_company_runs to get company_id
    3. Search Apollo by domain
    4. Update company with Apollo data
    5. Set is_relevant=true in campaign_company_run
    """
    campaigns_dao = None
    companies_dao = None
    campaign_company_runs_dao = None
    company_domain = None
    
    try:
        logger.info(f"🔍 Processing single company request: {request_id}")
        logger.info(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        
        # 1. Fetch campaign to get domain
        campaign_data = await campaigns_dao.get_campaign(campaign_id)
        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return
        
        company_domain = campaign_data.get("single_company", {}).get("domain")
        if not company_domain:
            logger.error(f"❌ No domain found in campaign: {campaign_id}")
            await campaigns_dao.update_campaign(campaign_id, {
                "single_company.status": "failed",
                "single_company.error": "No domain found in campaign",
                "metadata.updated_at": datetime.utcnow()
            })
            return
        
        logger.info(f"📋 Found domain: {company_domain}")
        
        # Update campaign single_company status to processing
        await campaigns_dao.update_campaign(campaign_id, {
            "single_company.status": "processing",
            "metadata.updated_at": datetime.utcnow()
        })
        
        # 2. Fetch campaign_company_runs to get company_id
        campaign_company_runs = await campaign_company_runs_dao.get_campaign_company_runs({
            "campaign_id": campaign_id
        })
        
        if not campaign_company_runs:
            logger.error(f"❌ No campaign_company_runs found for campaign: {campaign_id}")
            await campaigns_dao.update_campaign(campaign_id, {
                "single_company.status": "failed",
                "single_company.error": "No company mapping found",
                "metadata.updated_at": datetime.utcnow()
            })
            return
        
        # Get the first (and should be only) company run
        campaign_company_run = campaign_company_runs[0]
        company_id = campaign_company_run.get("company_id")
        campaign_company_run_id = campaign_company_run.get("_id")
        
        logger.info(f"📋 Found company_id: {company_id}")
        
        # 3. Search Apollo by domain
        apollo_client = ApolloAPIClient()
        search_result = await apollo_client.apollo_company_search_by_domain_api(company_domain)
        
        if search_result.get('status_code') != 200:
            logger.error(f"❌ Apollo search failed for domain {company_domain}")
            await campaigns_dao.update_campaign(campaign_id, {
                "single_company.status": "failed",
                "single_company.error": search_result.get('error', 'Apollo search failed'),
                "metadata.updated_at": datetime.utcnow()
            })
            return
        
        # Get first organization from results
        organizations = search_result.get('results', {}).get('organizations', [])
        if not organizations:
            organization = search_result.get('organization')  # Fallback to direct organization
        else:
            organization = organizations[0]  # Take first result
        
        if not organization:
            logger.warning(f"⚠️ No company found for domain {company_domain}")
            await campaigns_dao.update_campaign(campaign_id, {
                "single_company.status": "not_found",
                "single_company.error": f"No company found for domain: {company_domain}",
                "metadata.updated_at": datetime.utcnow()
            })
            return
        
        logger.info(f"✨ Found company in Apollo: {organization.get('name')}")
        
        # Helper to get employee count range from number
        def get_employee_count_range(num):
            if not num:
                return []
            if num <= 10:
                return ["1-10"]
            elif num <= 50:
                return ["11-50"]
            elif num <= 200:
                return ["51-200"]
            elif num <= 500:
                return ["201-500"]
            elif num <= 1000:
                return ["501-1000"]
            elif num <= 5000:
                return ["1001-5000"]
            elif num <= 10000:
                return ["5001-10000"]
            else:
                return ["10001+"]
        
        # Helper to get revenue range
        def get_revenue_range(revenue):
            if not revenue:
                return ("", "")
            if revenue < 1000000:
                return ("0", "1")
            elif revenue < 10000000:
                return ("1", "10")
            elif revenue < 50000000:
                return ("10", "50")
            elif revenue < 100000000:
                return ("50", "100")
            elif revenue < 500000000:
                return ("100", "500")
            else:
                return ("500", "1000+")
        
        revenue_min, revenue_max = get_revenue_range(organization.get("organization_revenue"))
        
        # 4. Update company with Apollo data in correct format
        company_update_data = {
            "identifiers.name": organization.get("name") or "",
            "identifiers.source_domain": organization.get("primary_domain") or company_domain,
            "identifiers.source_id": organization.get("id") or "",
            "identifiers.website_url": organization.get("website_url") or "",
            "source": "apollo",
            "webhook_sent": False,
            "metadata.updated_at": datetime.utcnow(),
            "metadata.api_response": organization,  # Store full Apollo response
            "location.name": organization.get("country") or "",
            "location.type": "country" if organization.get("country") else "",
            "profile.employee_count": get_employee_count_range(organization.get("estimated_num_employees")),
            "profile.industry": organization.get("industries") or ([organization.get("industry")] if organization.get("industry") else []),
            "profile.revenue_min": revenue_min,
            "profile.revenue_max": revenue_max
        }
        
        await companies_dao.update_company(company_id, company_update_data)
        logger.info(f"📝 Updated company with Apollo data: {company_id}")
        
        # 5. Update campaign_company_run with is_relevant=true
        await campaign_company_runs_dao.update_campaign_company_run(
            {"_id": campaign_company_run_id},
            {"$set": {
                "is_relevant": True,
                "metadata.updated_at": datetime.utcnow(),
                "metadata.enrichment_source": "apollo_domain_search"
            }}
        )
        logger.info(f"✅ Set is_relevant=true for campaign_company_run: {campaign_company_run_id}")
        
        # Update campaign with success status - set to company_qualification 
        # (company is qualified, ready for contact fetching via get_apollo_contact_list)
        await campaigns_dao.update_campaign(campaign_id, {
            "single_company.status": "completed",
            "single_company.company_id": company_id,
            "single_company.company_name": organization.get("name"),
            "prospecting_cycle.status": "company_qualification",
            "lifecycle.status": "company_qualification",
            "metadata.updated_at": datetime.utcnow()
        })
        
        logger.info(f"✅ Single company processing completed for campaign: {campaign_id}")
        
    except Exception as e:
        logger.error(f"❌ Error processing single company (domain: {company_domain}): {e}")
        # Update campaign with failure status
        try:
            if campaigns_dao:
                await campaigns_dao.update_campaign(campaign_id, {
                    "single_company.status": "failed",
                    "single_company.error": str(e),
                    "metadata.updated_at": datetime.utcnow()
                })
        except:
            pass
        raise 


async def process_leadgen_message(request_id: str, campaign_id: str):
    """Process a single leadgen company search request using campaign_id."""
    try:
        logger.info(f"🔍 Processing request: {request_id}")
        logger.info(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        # Fetch campaign data from database using campaign_id
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(campaign_id)
        
        if not campaign_data:
            logger.error(f"❌ Campaign not found: {campaign_id}")
            return
        
        logger.info(f"🔍 DEBUG: Campaign data structure: {campaign_data}")
        logger.info(f"📊 Industry: {campaign_data.get('segmentation', {}).get('industry', 'Unknown')}")
        logger.info(f"📍 Location: {campaign_data.get('target', {}).get('location', {}).get('names', 'Unknown')}")
        
        # Call the company search process with campaign data
        orchestrator = IntegrationOrchestrator(campaign_data)
        await orchestrator.process_company_search()
        
        logger.info(f"✅ Completed processing: {request_id}")
        # print(f"📝 Result: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error processing request {request_id}: {e}")
        raise 


async def lusha_company_collection_handler(message: Any):
    """Handler for lusha company collection messages."""
    try:
        logger.info(f"📨 Received lusha company collection message: {message}")
        payload = message

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")
        
        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return

        # Handle nested payload structure from Chronos
        logger.info(
            f"Debug - Full payload structure: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")

        inner_payload = payload.get("payload", payload)  # Try to get nested payload, fallback to original
        keys_or_type = list(inner_payload.keys()) if isinstance(inner_payload, dict) else type(inner_payload)
        logger.info(f"🔍 Debug - Inner payload structure: {keys_or_type}")
        inner_payload = inner_payload.get("payload", inner_payload)
        action = inner_payload.get("action")   
        
        if action != "process_lusha_company_collection":
            logger.error(f"❌ Unknown action: {action}")
            return

        campaign_details = inner_payload.get("campaign_details") 
        await process_lusha_company_collection(campaign_details)

    except Exception as e:
        logger.error(f"❌ Error handling lusha company collection message: {e}")
        raise


async def process_lusha_company_collection(campaign_details: Any):
    lusha_company_data = {
        'company_ids': [],
        'inserted_ids': []
    }

    try:
        # Initialize database connections for consumer context
        await initialize_consumer_connections()

        if isinstance(campaign_details, str):
            logger.info(f"🔍 Debug - campaign_details is string, parsing JSON...")
            campaign_details = json.loads(campaign_details)
        
        lusha_company_data = await lusha_company_data_collection(campaign_details)
        logger.info(f"lusha_company_data: {lusha_company_data}")

        if not lusha_company_data:
            logger.error("❌ No company data found")
            return

    except Exception as e:
        logger.error(f"❌ Error occurred during collection: {str(e)}")

    finally:
        logger.info(f"Returning {len(lusha_company_data)} companies")

        return lusha_company_data


async def lusha_company_data_collection(campaign_details: Any):
    fetch_company_status = False
    
    try:
        logger.info(f" lusha company data collection campaign_details: {campaign_details}")
        per_page = campaign_details["pages"]["page"]
        page_size = campaign_details["pages"]["size"]
        total_results = campaign_details.get("total_results", 0)
        logger.info(f" lusha company data collection total_results: {total_results}")
        # Calculate total_pages regardless of whether we need to fetch results
        total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 1
        logger.info(f" lusha company data collection calculated total_pages: {total_pages}")

        if total_results == 0:
            api_payload = convert_objectid_to_string(campaign_details)
            lusha_api_client = LushaAPIClient(payload_values=api_payload)
            first_response = await lusha_api_client.lusha_search_api()

            if first_response['status_code'] == 429:

                #need  to loop for try 3 times with sleep
                for i in range(3):
                    first_response = await lusha_api_client.lusha_search_api()

                    if first_response['status_code'] == 201:
                        fetch_company_status = True
                        break

                if first_response['status_code'] == 429:

                    logger.warning(f"❌ rate limit exhausted")
                    eta = generate_default_eta_expression(
                        daily_left=first_response['daily_left'], 
                        hourly_left=first_response['hourly_left'], 
                        minute_left=first_response['minute_left']
                    )

                    api_payload["total_results"] = total_results
                    api_payload["raw_config"] = campaign_details["raw_config"]

                    scheduler = await schedule_lusha_company_collection(campaign_details=api_payload, eta=eta)

                    logger.info(f"Scheduler response from handler: {scheduler}")

                    return []

            elif (first_response['status_code'] == 201 and 
                  "data" not in first_response['results']) or \
                  first_response['status_code'] != 201:
                logger.info("No data in first response. Returning empty results.")

                return {
                    'company_ids': [],
                    'inserted_ids': []
                }

            total_results = first_response["results"]["totalResults"]
            campaign_details["total_results"] = total_results
            logger.info(first_response)
            # Recalculate total_pages with the new total_results
            total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 1
            page_companies = []

            companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
            campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
            company_saver = CompanySaver(companies_dao, campaign_company_runs_dao)
            raw_config =campaign_details["raw_config"]
            
            for company in first_response["results"]["data"]:
                page_companies.append({
                    "id": company["id"], 
                    "name": company["name"],
                    "api_response_metadata": company
                })

            # ✅ IMMEDIATE DATABASE INSERTION
            inserted_count = await company_saver.insert_companies_batch_to_db(
                page_companies, raw_config,
                "lusha")

            # Step 2: Create campaign mappings
            mappings_created = await company_saver.create_campaign_company_mappings_batch(
                inserted_count['company_ids'], raw_config.get("_id")
            )

        logger.info(f"lusha company data collection pages:{per_page} page_size: {page_size} totalpages: {total_pages}")

        for page_num in range(per_page, total_pages):
            logger.info(f" lusha company data collection page_num: {page_num}")
            page_payload = campaign_details.copy()
            page_payload["pages"] = {"page": page_num, "size": page_size}
            page_response = await lusha_api_client.lusha_search_api(page_payload)

            if page_response['status_code'] == 429:

                logger.warning(f"❌ rate limit exhausted")
                eta = generate_default_eta_expression(
                    daily_left=page_response['daily_left'], 
                    hourly_left=page_response['hourly_left'], 
                    minute_left=page_response['minute_left']
                )
                page_payload["total_results"] = total_results
                page_payload["raw_config"] = campaign_details["raw_config"]
                scheduler = await schedule_lusha_company_collection(campaign_details=page_payload, eta=eta)
                logger.info(f" lusha company data collection scheduler: {scheduler}")
                break

            elif page_response['status_code'] == 201 and "data" in page_response['results']:
                fetch_company_status = True
                page_companies = []
                
                for company in page_response["results"]["data"]:
                    page_companies.append({
                        "id": company["id"], 
                        "name": company["name"],
                        "api_response_metadata": company
                    })

                # ✅ IMMEDIATE DATABASE INSERTION
                inserted_count = await company_saver.insert_companies_batch_to_db(page_companies, raw_config, "lusha")

                # Step 2: Create campaign mappings
                mappings_created = await company_saver.create_campaign_company_mappings_batch(
                    inserted_count['company_ids'], raw_config.get("_id")
                )
                
            else:
                logger.info(f"Failed to fetch page {page_num}")
                break

    except Exception as e:
        logger.error(f"❌ Error occurred during data collection: {str(e)}")

    finally:
        if fetch_company_status:
            campaigns_dao = CampaignsDao(
                loaded_config.connection_manager.mongo_client
            )
            update_campaign_status = await campaigns_dao.update_campaign_status(
                campaign_details["campaign_id"], "pending")
            logger.info(f"Updated status of {campaign_details['campaign_id']} to 'pending'")
            
        return inserted_count

async def contacts_enrichment_handler(message: Any):
    """Handler for contacts enrichment messages."""
      # Try different ways to extract the payload
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']

        else:
            logger.error(f"🔍 payload missing")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received leadgen message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        company_ids = payload.get("company_ids")  # Now we get campaign_id instead of form_data
        slack_metadata = payload.get("slack_metadata", {})
        if not request_id or not company_ids:
            logger.error("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_contacts_enrichment":
            logger.error(f"❌ Unknown action: {action}")
            return
        
        logger.info(f"🔄 Processing company search: {request_id}")

        await process_contacts_enrichment(request_id, company_ids, slack_metadata)

    except Exception as e:
        logger.error(f"❌ Error handling contacts enrichment message: {e}")
        raise

async def process_contacts_enrichment(request_id: str, company_ids: list, slack_metadata: dict):
    """Process a single contacts enrichment request using campaign_id."""
    try:
        logger.info(f"🔍 Processing request: {request_id}")
        logger.info(f"📋 Campaign ID: {company_ids}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        # Fetch campaign data from database using campaign_id
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        company_data = await companies_dao.get_companies({"_id": {"$in": company_ids}})
        if not company_data:
            logger.error(f"❌ Company not found: {company_ids}")
            return

        logger.info(f"company_ids: {company_ids}")
        
        person_seniorities = [ "vp", "director", "founder", "manager", "head", "partner", "c_suite", "owner"]
        contact_email_status = ["verified", "unverified", "likely to engage"]
        number_of_contacts_per_company = 25
        for company in company_data:
            company_name = company.get("identifiers", {}).get("name", "")
            company_domain = company.get("identifiers", {}).get("source_domain", "")

            company_id = company.get("_id", "")
            logger.info(f"company_data: {company_data}")
            logger.info(f"📊 Company Name: {company_name}")
            logger.info(f"📍 Company ID: {company_id}")
            apollo_helper = ApolloHelper()

            # if company as  multple unsent contacts, then don't do apollo search
            contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
            contacts = await contacts_dao.get_contacts({
                "company_id": company_id,
                # "webhook_sent": False,
                "contact_data.email": {"$ne": []} #only get contacts with email. it should not be empty here email is an array field.
            })
            
            # Create ApolloResponseSchema object
            if len(contacts) == 0:

                query_params = ApolloResponseSchema(
                    company_name=company_name,
                    company_domain=company_domain,
                    company_id=str(company_id),
                    person_seniorities=person_seniorities,
                    page=1,
                    per_page=number_of_contacts_per_company,
                    enrich_contacts=True,
                    contact_email_status=contact_email_status
                )

                response = await apollo_helper.get_company_contacts(query_params)
            #send  webhook to the users with the contacts
            webhook_sender = ContactHubspotWebhook()
            await webhook_sender.send_company_level_webhook(str(company_id), slack_metadata)
            # await webhook_sender.send_webhook_for_company(str(company_id), slack_metadata)
            logger.info(f"webhook sent to the users with the contacts")

        return
    except Exception as e:
        logger.error(f"❌ Error processing contacts enrichment: {e}")
        raise


async def leadgen_hubspot_sync_processing_handler(message: Any):
    """
    Handler for HubSpot sync processing messages.
    Receives campaign_id and syncs relevant contacts to HubSpot.
    """
    try:
        payload = None

        if isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        else:
            logger.error(f"🔍 payload missing in HubSpot sync message")
            return

        request_id = payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'
        logger.info(f"📨 Received HubSpot sync message: {request_id}")

        if not isinstance(payload, dict) or not payload:
            logger.error("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")
        
        if not request_id or not campaign_id:
            logger.error("❌ Missing request_id or campaign_id in HubSpot sync message")
            return
        
        if action != "sync_to_hubspot":
            logger.error(f"❌ Unknown action for HubSpot sync: {action}")
            return
        
        logger.info(f"🔄 Processing HubSpot sync for campaign: {campaign_id}")

        await sync_to_hubspot(request_id, campaign_id)

    except Exception as e:
        logger.error(f"❌ Error handling HubSpot sync message: {e}")
        raise


async def sync_to_hubspot(request_id: str, campaign_id: str):
    """
    Sync campaign contacts to HubSpot.
    This function will contain the actual sync logic.
    
    Args:
        request_id: Unique request identifier for tracking
        campaign_id: Campaign ID to sync contacts from
    """
    try:
        logger.info(f"🔍 Starting HubSpot sync for request: {request_id}, campaign: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        hubspot_webhook = ContactHubspotWebhook(custom_webhook_url="https://asia-south1.api.boltic.io/service/webhook/temporal/v1.0/b156f5b3-c90d-449a-b104-2735e1259e5c/workflows/execute/2821387b-9e86-4c9a-ac83-b5ffeb7ba959", campaign_id=campaign_id)
        await hubspot_webhook.sync_to_hubspot(campaign_id)
        
        
        logger.info(f"✅ HubSpot sync completed for campaign: {campaign_id}")
        
        return
    except Exception as e:
        logger.error(f"❌ Error syncing to HubSpot: {e}")
        raise