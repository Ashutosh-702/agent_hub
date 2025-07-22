from typing import Optional
from agent_hub.ai_agents.linkedin_sdr.database import leads_collection, batches_collection, batch_values_collection
from agent_hub.ai_agents.linkedin_sdr.models.accounts import get_account_id
from agent_hub.ai_agents.linkedin_sdr.unipile_service import fetch_provider_id
async def add_lead(linkedin_url: str, account_id: str, provider_id: str) -> None:
    """
    Adds a new lead document with the given linkedin_url, account_id, and provider_id.
    """
    try:
        await leads_collection.insert_one({
            "linkedin_url": linkedin_url,
            "account_id": account_id,
            "provider_id": provider_id
        })
    except Exception as e:
        print(f"ERROR: add_lead: {e}")

async def get_provider_id(linkedin_url: str, account_id: str) -> Optional[str]:
    """
    Fetches from db or unipileAPI the provider_id for the given linkedin_url.
    """
    try:
        lead = await leads_collection.find_one({"linkedin_url": linkedin_url})
        if lead and "provider_id" in lead:
            return lead["provider_id"]

        provider_id = await fetch_provider_id(linkedin_url, account_id)

        await leads_collection.insert_one({
            "linkedin_url": linkedin_url,
            "provider_id": provider_id,
            "account_id": account_id
        })

        return provider_id

    except Exception as e:
        print(f"ERROR: get_provider_id: {e}")
        return None
async def get_lead(linkedin_url: str) -> Optional[dict]:
    """
    Fetches the lead document using linkedin_url. Returns the lead if found, else None.
    """
    try:
        return await leads_collection.find_one({"linkedin_url": linkedin_url})
    except Exception as e:
        print(f"ERROR: get_lead: {e}")
        return None