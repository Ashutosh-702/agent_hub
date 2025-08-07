import asyncio
import requests
from dotenv import load_dotenv

from config import loaded_config
from database.collection_dao.campaigns import CampaignsDao
BASE_URL = "http://localhost:8000/api/v1/orchestrated/run"
load_dotenv()
from ai_agents.core_sdr.src.cli.main import process_company_search
from ai_agents.leadgen.workflow.prompt_reader import prompt_fetcher, set_status_true
from ai_agents.core_sdr.src.api.coresignal_api import collect_companies_from_search
from ai_agents.core_sdr.src.parsers.lusha_helper import get_companies_from_lusha, sheets_to_lusha_config
from config.loaded_config import loaded_config
from database.connection_manager import ConnectionManager
import json
async def run_batch():
    loaded_config.connection_manager = ConnectionManager(mongo_uri=loaded_config.mongo_uri, db_name="linkedin_db")
    campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
    # response = await campaign_dao.get_campaigns({"status": "active"})
    prompts = await prompt_fetcher()

    if not prompts:
        print("✅ No new prompts found.")
        return

    print(f"📝 Found {len(prompts)} prompts to run.\n")

    for entry in prompts:
        try:
            web_prompt = entry.get("web_prompt", "")
            persona_prompt = entry.get("persona_prompt", "")
            industry = entry.get("industry", "")
            employee_count = entry.get("employee_count", "")
            revenue_min = entry.get("revenue_min", "")
            revenue_max = entry.get("revenue_max", "")
            location_type = entry.get("location_type","")
            location = entry.get("location", "")
            keywords = entry.get("keywords", "")
            categories = entry.get("categories", "")
            currency = entry.get("currency", "USD")
            hubspot_email = entry.get("hubspot_email", "")
            product_name = entry.get("product_name", "")
            business_team = entry.get("business_team", "")
            user_email = entry.get("user_email","")
            status = entry.get("status","")
            print(f"\n🔍 Processing entry for: {industry} industry in {location}")
            print("📊 Fetching companies")
            
            data = {
                "web_prompt": web_prompt,
                "persona_prompt": persona_prompt,
                "industry": industry,
                "employee_count": employee_count,
                "revenue_min": revenue_min,
                "revenue_max": revenue_max,
                "location_type": location_type,
                "location": location,
                "keywords": keywords,
                "categories": categories,
                "currency": currency,
                "hubspot_email": hubspot_email,
                "product_name": product_name,
                "business_team": business_team,
                "user_email":user_email,
                "status":status
            }

            print(json.dumps(data,indent=2))
        except Exception as e:
            print(f"❌ Error processing entry: {str(e)}")
            continue

    loaded_config.connection_manager.mongo_client.close()
    print("\n🏁 Batch processing completed!")

if __name__ == "__main__":
    asyncio.run(run_batch())