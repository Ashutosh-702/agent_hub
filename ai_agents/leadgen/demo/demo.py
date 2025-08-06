import asyncio
import requests
from dotenv import load_dotenv
BASE_URL = "http://localhost:8000/api/v1/orchestrated/run"
load_dotenv()
from ai_agents.leadgen.workflow.prompt_reader import prompt_fetcher, set_status_true
from ai_agents.core_sdr.src.api.coresignal_api import collect_companies_from_search
from ai_agents.core_sdr.src.parsers.lusha_helper import get_companies_from_lusha, sheets_to_lusha_config

async def run_batch():
    prompts = prompt_fetcher()

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
            location = entry.get("location", "")
            keywords = entry.get("keywords", "")
            categories = entry.get("categories", "")
            currency = entry.get("currency", "USD")
            hubspot_email = entry.get("hubspot_email", "")
            product_name = entry.get("product_name", "")
            business_team = entry.get("business_team", "")

            print(f"\n🔍 Processing entry for: {industry} industry in {location}")
            print("📊 Fetching companies from Lusha...")
            
            sheets_data = {
                "web_prompt": web_prompt,
                "persona_prompt": persona_prompt,
                "industry": industry,
                "employee_count": employee_count,
                "revenue_min": revenue_min,
                "revenue_max": revenue_max,
                "location": location,
                "keywords": keywords,
                "categories": categories,
                "currency": currency,
                "hubspot_email": hubspot_email,
                "product_name": product_name,
                "business_team": business_team
            }
            companies = collect_companies_from_search(sheets_data)
            
            # companies = get_companies_from_lusha(sheets_data)
            
            # if not companies:
            #     print("⚠️ No companies found from Lusha, skipping this entry")
            #     continue

            print(f"✅ Retrieved {len(companies)} companies from Lusha")
            print(f"📋 Companies: {companies[:5]}{'...' if len(companies) > 5 else ''}")

            config = {
                "search_query": web_prompt,
                "target_executives": persona_prompt,
                "companies": companies,  # Pass the companies list
                "original_sheets_data": sheets_data  # Include original data for reference
            }

        except Exception as e:
            print(f"❌ Error processing entry: {str(e)}")
            continue

    print("\n🏁 Batch processing completed!")

if __name__ == "__main__":
    asyncio.run(run_batch())