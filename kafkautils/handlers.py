"""Message handlers for leadgen Kafka consumers."""
from time import sleep
from typing import Any
import json
from database.connection_manager import ConnectionManager
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from integrations.integration_orchestrator import IntegrationOrchestrator
from global_utils.chronos_utils import (
    generate_default_eta_expression,
    schedule_lusha_company_collection
)
from integrations.lusha.company_saver import CompanySaver
from config.logging import logger
from integrations.apollo.apollo_helper import ApolloHelper
from integrations.apollo.schema import ApolloResponseSchema
from webhooks.contact_hubspot_webhook import ContactHubspotWebhook

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
        
        if not request_id or not company_ids:
            logger.error("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_contacts_enrichment":
            logger.error(f"❌ Unknown action: {action}")
            return
        
        logger.info(f"🔄 Processing company search: {request_id}")

        await process_contacts_enrichment(request_id, company_ids)

    except Exception as e:
        logger.error(f"❌ Error handling contacts enrichment message: {e}")
        raise

async def process_contacts_enrichment(request_id: str, company_ids: list):
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
        
        person_seniorities = [ "vp", "director"]
        number_of_contacts_per_company = 2
        for company in company_data:
            company_name = company.get("identifiers", {}).get("name", "")
            company_domain = company.get("identifiers", {}).get("source_domain", "")

            company_id = company.get("_id", "")
            logger.info(f"company_data: {company_data}")
            logger.info(f"📊 Company Name: {company_name}")
            logger.info(f"📍 Company ID: {company_id}")
            apollo_helper = ApolloHelper()
            
            # Create ApolloResponseSchema object
            query_params = ApolloResponseSchema(
                company_name=company_name,
                company_domain=company_domain,
                company_id=str(company_id),
                person_seniorities=person_seniorities,
                page=1,
                per_page=number_of_contacts_per_company,
                enrich_contacts=True
            )
            
            response = await apollo_helper.get_company_contacts(query_params)
            #send  webhook to the users with the contacts
            webhook_sender = ContactHubspotWebhook()
            await webhook_sender.send_webhook_for_company(str(company_id))
            logger.info(f"webhook sent to the users with the contacts")

        return
    except Exception as e:
        logger.error(f"❌ Error processing contacts enrichment: {e}")
        raise