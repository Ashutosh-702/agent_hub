import os
import requests
from ..database import leads_collection

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

async def get_provider_id(linkedin_url: str) -> str:
    """
    Fetches from db or unipileAPI the provider_id for the given linkedin_url.
    """
    try:
        lead = await leads_collection.find_one({"linkedin_url": linkedin_url})
        if lead and "provider_id" in lead:
            return lead["provider_id"]

        identifier = linkedin_url
        account_id = os.getenv("UNIPILE_ACCOUNT_ID")
        api_token = os.getenv("UNIPILE_API_TOKEN")
        base_url = os.getenv("UNIPILE_API_URL")

        url = f"{base_url}/api/v1/users/{identifier}?account_id={account_id}"
        headers = {
            "X-API-KEY": api_token,
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"APIERROR: Unipile API failed: {response.status_code}, {response.text}")
            return None

        data = response.json()
        provider_id = data.get("provider_id")

        await leads_collection.insert_one({
            "linkedin_url": linkedin_url,
            "provider_id": provider_id,
            "account_id": account_id
        })

        return provider_id

    except Exception as e:
        print(f"ERROR: get_provider_id: {e}")
        return None
async def get_lead(linkedin_url: str) -> dict:
    """
    Fetches the lead document using linkedin_url. Returns the lead if found, else None.
    """
    try:
        return await leads_collection.find_one({"linkedin_url": linkedin_url})
    except Exception as e:
        print(f"ERROR: get_lead: {e}")
        return None