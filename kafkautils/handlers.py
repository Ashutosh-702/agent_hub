"""Message handlers for leadgen Kafka consumers."""
from time import sleep
from typing import Any
import json
from ai_agents.core_sdr.src.cli.main import process_company_search
from database.connection_manager import ConnectionManager
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from bson import ObjectId
from ai_agents.core_sdr.src.api.lusha_api import lusha_search_api
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from datetime import datetime, timezone
import time
from global_utils.chronos_utils import (
    generate_default_eta_expression,
    schedule_lusha_company_collection
)

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
        print("🔄 Initializing database connection for consumer...")
        loaded_config.connection_manager = ConnectionManager(
            mongo_uri=loaded_config.mongo_uri, 
            db_name="linkedin_sdr"
        )
        print("✅ Database connection initialized for consumer")

async def leadgen_batch_processing_handler(message: Any):
    """
    Default handler for leadgen batch processing messages.
    This gets replaced by EventBridge consumer with custom handler.
    """
    try:
        # Try different ways to extract the payload
        payload = None
        if hasattr(message, 'value'):
            payload = message.value
        elif hasattr(message, 'data'):
            payload = message.data
        elif isinstance(message, dict) and 'payload' in message:
            payload = message['payload']
        elif isinstance(message, dict):
            payload = message
        else:
            payload = message
        print(f"📨 Received leadgen message: {payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'}")

        if not isinstance(payload, dict) or not payload:
            print("❌ Invalid message payload")
            return
        
        request_id = payload.get("request_id")
        action = payload.get("action")
        campaign_id = payload.get("campaign_id")  # Now we get campaign_id instead of form_data
        
        if not request_id or not campaign_id:
            print("❌ Missing request_id or campaign_id in message")
            return
        
        if action != "process_company_search":
            print(f"❌ Unknown action: {action}")
            return
        
        print(f"🔄 Processing company search: {request_id}")
        
        # Process the company search using campaign_id
        await process_leadgen_message(request_id, campaign_id)
        
    except Exception as e:
        print(f"❌ Error handling leadgen message: {e}")
        import traceback
        traceback.print_exc()
        raise

async def process_leadgen_message(request_id: str, campaign_id: str):
    """Process a single leadgen company search request using campaign_id."""
    try:
        print(f"🔍 Processing request: {request_id}")
        print(f"📋 Campaign ID: {campaign_id}")
        
        # Initialize database connection if needed
        await initialize_consumer_connections()
        
        # Fetch campaign data from database using campaign_id
        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        campaign_data = await campaigns_dao.get_campaign(ObjectId(campaign_id))
        
        if not campaign_data:
            print(f"❌ Campaign not found: {campaign_id}")
            return
        
        print(f"🔍 DEBUG: Campaign data structure: {campaign_data}")
        print(f"📊 Industry: {campaign_data.get('segmentation', {}).get('industry', 'Unknown')}")
        print(f"📍 Location: {campaign_data.get('target', {}).get('location', {}).get('names', 'Unknown')}")
        
        # Call the company search process with campaign data
        result = await process_company_search(campaign_data)
        
        print(f"✅ Completed processing: {request_id}")
        # print(f"📝 Result: {result}")
        
    except Exception as e:
        print(f"❌ Error processing request {request_id}: {e}")
        raise 

async def lusha_company_collection_handler(message: Any):
    """Handler for lusha company collection messages."""
    try:
        print(f"📨 Received lusha company collection message: {message}")
        payload = None
        if hasattr(message, 'value'):
            payload = message.value
        elif hasattr(message, 'data'):
            payload = message.data
        elif isinstance(message, dict):
            payload = message
        else:
            payload = message
        
        print(f"📨 Received leadgen message: {payload.get('request_id', 'unknown') if isinstance(payload, dict) else 'unknown'}")
        
        if not isinstance(payload, dict) or not payload:
            print("❌ Invalid message payload")
            return

        # Handle nested payload structure from Chronos
        print(f"🔍 Debug - Full payload structure: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")
        inner_payload = payload.get("payload", payload)  # Try to get nested payload, fallback to original
        print(f"🔍 Debug - Inner payload structure: {list(inner_payload.keys()) if isinstance(inner_payload, dict) else type(inner_payload)}")
        inner_payload = inner_payload.get("payload", inner_payload)
        action = inner_payload.get("action")   
        if action != "process_lusha_company_collection":
            print(f"❌ Unknown action: {action}")
            return
        campaign_details = inner_payload.get("campaign_details") 
        await process_lusha_company_collection(campaign_details)
    except Exception as e:
        print(f"❌ Error handling lusha company collection message: {e}")
        raise

async def process_lusha_company_collection(campaign_details: Any):
    lusha_company_data = []  # Initialize before try block
    try:
        # Initialize database connections for consumer context
        await initialize_consumer_connections()

        if isinstance(campaign_details, str):
            print(f"🔍 Debug - campaign_details is string, parsing JSON...")
            campaign_details = json.loads(campaign_details)
        
        lusha_company_data = await lusha_company_data_collection(campaign_details)
        print(f"lusha_company_data: {lusha_company_data}")

        if not lusha_company_data:
            print("❌ No company data found")
            return
        companies_list = []
        cached_data = []
        companies_dao = CompaniesDao(
            loaded_config.connection_manager.mongo_client
        )
        config = campaign_details["raw_config"]
        # cached_data_db = await companies_dao.get_companies({"location.name":config.get("locations", {}).get("location", {}).get("names", []), "location.type": config.get("target", {}).get("location", {}).get("type", ""), "profile.industry":config.get("segmentation", {}).get("industry", [])})
        cached_data_db = await companies_dao.get_companies({
            "location.name": {"$in": config.get("target", {}).get("location", {}).get("names", [])}, 
            "location.type": config.get("target", {}).get("location", {}).get("type", ""), 
            "profile.industry": {"$in": config.get("segmentation", {}).get("industry", [])}
        })
        for company_data in cached_data_db:
            cached_data.append({'id': company_data['identifiers']['source_id'],'name': company_data['identifiers']['name']})
        cached_ids = [company['_id'] for company in cached_data_db]
        if lusha_company_data:
            source_id_list = [cached_company["id"] for cached_company in cached_data]
            for company_data in lusha_company_data:
                source_id = company_data["id"]
                if source_id not in source_id_list:  
                    company_doc = {
                        "identifiers":{
                            "source_id": company_data["id"],
                            "name": company_data["name"],
                        }, 
                        "profile":{
                            "industry": config.get("segmentation", {}).get("industry", None),  
                            #here revenue_min, revenue_max, employee_count may not present in the config. need to handle this.
                            "revenue_min": config.get("target", {}).get("revenue_min", None),
                            "revenue_max": config.get("target", {}).get("revenue_max", None),
                            "employee_count": config.get("target", {}).get("employee_count", None),
                        },
                        "location":{
                            "type": config.get("target", {}).get("location", {}).get("type", None),
                            "name": config.get("target", {}).get("location", {}).get("names", None),
                        },
                        "source": "lusha",
                        "metadata":{
                            "created_at":datetime.now(timezone.utc),
                            "updated_at":datetime.now(timezone.utc),
                            "api_response": company_data["api_response_metadata"],
                        }
                    }
                    companies_list.append(company_doc)
            if len(companies_list) > 0:
                inserted_ids = await companies_dao.create_companies(companies_list)
            else:
                inserted_ids = []
            print(f"Total new companies added into companies collection: {len(inserted_ids)}")
            id_list = inserted_ids + cached_ids
            campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
            for _id in id_list:
                mapping_doc = {
                "campaign_id": ObjectId(config.get("_id")),
                "company_id": ObjectId(_id),
                "company_status": False,
                "metadata":{
                        "created_at":datetime.now(timezone.utc),
                        "updated_at":datetime.now(timezone.utc),
                    },
                }
                await campaign_company_runs_dao.create_campaign_company_run(mapping_doc)
    except Exception as e:
        print(f"❌ Error occurred during collection: {str(e)}")
    finally:
        print(f"Returning {len(lusha_company_data)} companies")
        return lusha_company_data

async def lusha_company_data_collection(campaign_details: Any):
    all_companies = []
    fetch_company_status = False
    try:
        print(f" lusha company data collection campaign_details: {campaign_details}")
        per_page = campaign_details["pages"]["page"]
        page_size = campaign_details["pages"]["size"]
        total_results = campaign_details.get("total_results", 0)
        print(f" lusha company data collection total_results: {total_results}")

        
        # Calculate total_pages regardless of whether we need to fetch results
        total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 1
        print(f" lusha company data collection calculated total_pages: {total_pages}")

        if total_results == 0:
            print("fetching response")
            api_payload = convert_objectid_to_string(campaign_details)
            first_response = await lusha_search_api(api_payload)

            if first_response['status_code'] == 429:
                #need  to loop for try 3 times with sleep
                for i in range(3):
                    time.sleep(10)
                    first_response = await lusha_search_api(api_payload)
                    if first_response['status_code'] == 201:
                        fetch_company_status = True
                        break
                if first_response['status_code'] == 429:
                    print(f"❌ rate limit exhausted")
                    eta = generate_default_eta_expression(
                        daily_left=first_response['daily_left'], 
                        hourly_left=first_response['hourly_left'], 
                        minute_left=first_response['minute_left']
                    )
                    api_payload["total_results"] = total_results
                    api_payload["raw_config"] = campaign_details["raw_config"]
                    scheduler = await schedule_lusha_company_collection(campaign_details=api_payload, eta=eta)
                    print(f"Scheduler response from handler: {scheduler}")
                    return []
            elif first_response['status_code'] == 201 and "data" not in first_response['results'] or first_response['status_code'] != 201:
                print("No data in first response. Returning empty results.")
                return []

            total_results = first_response["results"]["totalResults"]
            campaign_details["total_results"] = total_results
            print("got response")
            print(first_response)
            # Recalculate total_pages with the new total_results
            total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 1

            # total_pages = (total_results + page_size - 1) // page_size

            for company in first_response["results"]["data"]:
                all_companies.append({
                    "id": company["id"], 
                    "name": company["name"],
                    "api_response_metadata": company
                })
        #temp current page
        # per_page = 1
        # total_pages = 2
        print(f" lusha company data collection pages: {per_page} page_size: {page_size} totalpages: {total_pages}")

        for page_num in range(per_page, total_pages):
            print(f" lusha company data collection page_num: {page_num}")
            page_payload = campaign_details.copy()
            page_payload["pages"] = {"page": page_num, "size": page_size}
            page_response = await lusha_search_api(page_payload, all_companies)

            if page_response['status_code'] == 429:
                #need  to loop for try 3 times with sleep
                for i in range(1):
                    page_response = await lusha_search_api(page_payload, all_companies)
                    if page_response['status_code'] == 429:
                        time.sleep(10)
                    else:
                        break

                if page_response['status_code'] == 429:
                    print(f"❌ rate limit exhausted")
                    eta = generate_default_eta_expression(
                        daily_left=page_response['daily_left'], 
                        hourly_left=page_response['hourly_left'], 
                        minute_left=page_response['minute_left']
                    )
                    page_payload["total_results"] = total_results
                    page_payload["raw_config"] = campaign_details["raw_config"]
                    scheduler = await schedule_lusha_company_collection(campaign_details=page_payload, eta=eta)
                    print(f" lusha company data collection scheduler: {scheduler}")
                    break
                else:
                    break
            elif page_response['status_code'] == 201 and "data" in page_response['results']:
                fetch_company_status = True
                for company in page_response["results"]["data"]:
                    all_companies.append({
                        "id": company["id"], 
                        "name": company["name"],
                        "api_response_metadata": company
                    })
            else:
                print(f"Failed to fetch page {page_num}")
                break
        # if fetch_company_status:
        #     campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        #     update_campaign_status = await campaigns_dao.update_campaign_status(ObjectId(campaign_details["campaign_id"]), "pending")
        #     print(f"Updated status of {campaign_details['_id']} to 'processed'")
        # return all_companies
        
    except Exception as e:
        print(f"❌ Error occurred during data collection: {str(e)}")
    finally:
        if fetch_company_status:
            campaigns_dao = CampaignsDao(
                loaded_config.connection_manager.mongo_client
            )
            update_campaign_status = await campaigns_dao.update_campaign_status(ObjectId(campaign_details["campaign_id"]), "pending")
            print(f"Updated status of {campaign_details['campaign_id']} to 'pending'")
        return all_companies