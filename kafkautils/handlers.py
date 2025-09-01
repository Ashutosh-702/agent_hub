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
    try:
        # Initialize database connections for consumer context
        await initialize_consumer_connections()
        loaded_config.lusha_api_key = "cf7f4465-da50-4e3c-88b2-2b9f5521a9f3"
        # Parse campaign_details if it's a JSON string
        if isinstance(campaign_details, str):
            print(f"🔍 Debug - campaign_details is string, parsing JSON...")
            campaign_details = json.loads(campaign_details)
        
        # lusha_company_data = await lusha_company_data_collection(campaign_details)
        lusha_company_data = [{'id': '9252341', 'name': 'Swiggy', 'api_response_metadata': {'id': '9252341', 'name': 'Swiggy', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '10143', 'name': 'Taj Hotels', 'api_response_metadata': {'id': '10143', 'name': 'Taj Hotels', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '3716484', 'name': 'OYO', 'api_response_metadata': {'id': '3716484', 'name': 'OYO', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '16271', 'name': 'Britannia Industries Limited', 'api_response_metadata': {'id': '16271', 'name': 'Britannia Industries Limited', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '361348', 'name': 'Myntra', 'api_response_metadata': {'id': '361348', 'name': 'Myntra', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '17302', 'name': 'DS Group', 'api_response_metadata': {'id': '17302', 'name': 'DS Group', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '14468407', 'name': 'The Indian Hotels Company Limited (IHCL)', 'api_response_metadata': {'id': '14468407', 'name': 'The Indian Hotels Company Limited (IHCL)', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '164809', 'name': 'Aditya Birla Fashion and Retail Ltd.', 'api_response_metadata': {'id': '164809', 'name': 'Aditya Birla Fashion and Retail Ltd.', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '31239958', 'name': 'Tata Consumer Products', 'api_response_metadata': {'id': '31239958', 'name': 'Tata Consumer Products', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '27515', 'name': 'ITC Hotels Limited', 'api_response_metadata': {'id': '27515', 'name': 'ITC Hotels Limited', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '566952', 'name': 'Jubilant FoodWorks Ltd.', 'api_response_metadata': {'id': '566952', 'name': 'Jubilant FoodWorks Ltd.', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '12577', 'name': 'Arvind Limited', 'api_response_metadata': {'id': '12577', 'name': 'Arvind Limited', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '18259907', 'name': 'Hindustan Coca-Cola Beverages', 'api_response_metadata': {'id': '18259907', 'name': 'Hindustan Coca-Cola Beverages', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '129585', 'name': 'Shahi Exports Pvt Ltd', 'api_response_metadata': {'id': '129585', 'name': 'Shahi Exports Pvt Ltd', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '148669', 'name': 'The Leela Palaces, Hotels and Resorts', 'api_response_metadata': {'id': '148669', 'name': 'The Leela Palaces, Hotels and Resorts', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '2618177', 'name': 'Reliance Brands Limited', 'api_response_metadata': {'id': '2618177', 'name': 'Reliance Brands Limited', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '571704', 'name': 'Bata India Limited', 'api_response_metadata': {'id': '571704', 'name': 'Bata India Limited', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '369636', 'name': 'Devyani International Limited', 'api_response_metadata': {'id': '369636', 'name': 'Devyani International Limited', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '1127583', 'name': 'Mahindra Holidays & Resorts India Limited', 'api_response_metadata': {'id': '1127583', 'name': 'Mahindra Holidays & Resorts India Limited', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '912501', 'name': 'United Breweries Ltd.', 'api_response_metadata': {'id': '912501', 'name': 'United Breweries Ltd.', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '518933', 'name': 'Bisleri International Pvt Ltd', 'api_response_metadata': {'id': '518933', 'name': 'Bisleri International Pvt Ltd', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '33353', 'name': 'Arvind Fashions Limited', 'api_response_metadata': {'id': '33353', 'name': 'Arvind Fashions Limited', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '457313', 'name': 'The Lalit Suri Hospitality Group', 'api_response_metadata': {'id': '457313', 'name': 'The Lalit Suri Hospitality Group', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '412199', 'name': 'Page Industries Ltd', 'api_response_metadata': {'id': '412199', 'name': 'Page Industries Ltd', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '95569', 'name': 'Lemon Tree Hotels', 'api_response_metadata': {'id': '95569', 'name': 'Lemon Tree Hotels', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '83004373', 'name': 'Hyperpure by Zomato', 'api_response_metadata': {'id': '83004373', 'name': 'Hyperpure by Zomato', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '1842947', 'name': 'Bira 91', 'api_response_metadata': {'id': '1842947', 'name': 'Bira 91', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '17976', 'name': 'Oberoi Hotels & Resorts', 'api_response_metadata': {'id': '17976', 'name': 'Oberoi Hotels & Resorts', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '13195556', 'name': 'Sapphire Foods India Limited', 'api_response_metadata': {'id': '13195556', 'name': 'Sapphire Foods India Limited', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '9471845', 'name': 'Licious', 'api_response_metadata': {'id': '9471845', 'name': 'Licious', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '307094', 'name': 'Haldiram’s snacks food pvt. ltd.', 'api_response_metadata': {'id': '307094', 'name': 'Haldiram’s snacks food pvt. ltd.', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '978380', 'name': 'Barbeque Nation Hospitality Ltd.', 'api_response_metadata': {'id': '978380', 'name': 'Barbeque Nation Hospitality Ltd.', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '13631041', 'name': 'Fortune Park Hotels Ltd', 'api_response_metadata': {'id': '13631041', 'name': 'Fortune Park Hotels Ltd', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '13318625', 'name': 'Stanza Living', 'api_response_metadata': {'id': '13318624', 'name': 'Stanza Living', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '10594819', 'name': 'Lifestyle International Pvt Ltd', 'api_response_metadata': {'id': '10594819', 'name': 'Lifestyle International Pvt Ltd', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '1610594', 'name': 'Compass Group India', 'api_response_metadata': {'id': '1610594', 'name': 'Compass Group India', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '330905', 'name': 'Blackberrys Menswear', 'api_response_metadata': {'id': '330905', 'name': 'Blackberrys Menswear', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '4037279', 'name': 'Havmor Ice Cream', 'api_response_metadata': {'id': '4037279', 'name': 'Havmor Ice Cream', 'hasCompanyRevenue': False, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '17975', 'name': 'The Oberoi Group', 'api_response_metadata': {'id': '17975', 'name': 'The Oberoi Group', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': False, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}},
                             {'id': '14517494', 'name': 'Metro Brands Limited', 'api_response_metadata': {'id': '14517494', 'name': 'Metro Brands Limited', 'hasCompanyRevenue': True, 'hasCompanyMainIndustry': True, 'hasCompanySubIndustry': True, 'hasCompanyFunding': True, 'hasCompanyIntent': False, 'hasCompanyTechnologies': True}}]

        print(f"lusha_company_data: {lusha_company_data}")
        if not lusha_company_data:
            print("❌ No company data found")
            return
        companies_list = []
        cached_data = []
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
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
        return lusha_company_data
    except Exception as e:
            print(f"❌ Error occurred during collection: {str(e)}")
            if 'lusha_company_data' in locals() and len(lusha_company_data) > 0:
                print(f"Error occurred during collection, but returning {len(lusha_company_data)} companies already collected: {str(e)}")
                return lusha_company_data
            return []

async def lusha_company_data_collection(campaign_details: Any):
    try:
        per_page = campaign_details["pages"]["page"]
        page_size = campaign_details["pages"]["size"]
        
        #here total_results is the total number of companies to collect. this key may comes may not comes. need to handle this.
        total_results = campaign_details.get("total_results", 0)
        all_companies = []
        if total_results == 0:
            print("fetching response")
            # Convert ObjectId to string to make it JSON serializable
            api_payload = convert_objectid_to_string(campaign_details)
            first_response = await lusha_search_api(api_payload)
            if first_response is None:
                #need  to loop for try 3 times with sleep
                for i in range(3):
                    first_response = await lusha_search_api(api_payload)
                    if first_response is None:
                        time.sleep(2)
                    if first_response is not None:
                        break
                if first_response is None:
                    print(f"❌ rate limit exhausted")
                    return []
            total_results = first_response["totalResults"]
            campaign_details["total_results"] = total_results
            print("got response")
            print(first_response)
            total_pages = (total_results + page_size - 1) // page_size
            for company in first_response["data"]:
                all_companies.append({
                    "id": company["id"], 
                    "name": company["name"],
                    "api_response_metadata": company
                })
        #temp current page
        per_page = 1
        total_pages = 2
        for page_num in range(per_page, total_pages):
            page_payload = campaign_details.copy()
            page_payload["pages"] = {"page": page_num, "size": page_size}
            page_response = await lusha_search_api(page_payload, all_companies)
            if page_response is None:
                #need  to loop for try 3 times with sleep
                for i in range(1):
                    page_response = await lusha_search_api(page_payload, all_companies)
                    if page_response is None:
                        time.sleep(2)
                    if page_response is not None:
                        break
                if page_response is None:
                    print(f"❌ rate limit exhausted")
                    break
            for company in page_response["data"]:
                all_companies.append({
                    "id": company["id"], 
                    "name": company["name"],
                    "api_response_metadata": company
                })
        return all_companies
    except Exception as e:
        print(f"❌ Error occurred during data collection: {str(e)}")
        if 'lusha_company_data' in locals() and len(all_companies) > 0:
                print(f"Error occurred during collection, but returning {len(all_companies)} companies already collected: {str(e)}")
                return all_companies
        return []