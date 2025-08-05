import asyncio
import requests

BASE_URL = "http://localhost:8000/api/v1/orchestrated/run"

from ai_agents.leadgen.workflow.prompt_reader import prompt_fetcher , set_status_true
from ai_agents.leadgen.api.main import enhance_query,EnhanceRequest


async def run_batch():
    prompts = prompt_fetcher()

    if not prompts:
        print("✅ No new prompts found.")
        return

    print(f"📝 Found {len(prompts)} prompts to run.\n")

    for entry in prompts:
        prompt_text = entry["prompt"]
        industry = entry["industry"]
        is_b2b = entry["is_b2b"]
        employee_count = entry["employee_count"]
        hq = entry["hq"]
        final_query = f"{industry} industry and {'should be B2B' if is_b2b == 'true' else 'shouldn\'t be B2B'} and employee count {employee_count} and headquartered in {hq}."
        final_query_enhanced = await enhance_query(EnhanceRequest(query=final_query))
        print(f"\n🔁 Running prompt:(CORE SDR) {final_query_enhanced.get("enhanced")}\n")

        response = requests.post(BASE_URL, json={
            "config": {
                "query": final_query_enhanced.get("enhanced"),
                "search_query": prompt_text,
            }
        })

        if response.get("status") == "success":
            print("✅ Prompt processed:", response.json())
            set_status_true(entry["row_index"])
        else:
            print("❌ Error:", response.status_code, response.text)

if __name__ == "__main__":
    asyncio.run(run_batch())
