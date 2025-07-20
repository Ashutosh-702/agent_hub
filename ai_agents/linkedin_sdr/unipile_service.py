import os
import re
import requests
from typing import Optional

BASE_URL = os.getenv("UNIPILE_API_URL")
API_KEY = os.getenv("UNIPILE_API_TOKEN")

HEADERS = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async def connect_account(linkedin_email: str, password: str) -> Optional[str]:
    try:
        url = f"{BASE_URL}/api/v1/accounts"
        data = {
            "provider": "LINKEDIN",
            "username": linkedin_email,
            "password": password
        }
        res = await requests.post(url, headers=HEADERS, json=data)

        if res.status_code == 200:
            return res.json().get("account_id")

        raise Exception(f"ERROR: bad response || connect_account: {res.text}")
    except Exception as e:
        print(f"ERROR: failed to connect || connect_account: {str(e)}")
        return None

async def fetch_provider_id(linkedin_url: str, account_id: str) -> Optional[str]:
    try:
        match = re.search(r"linkedin\.com/in/([a-zA-Z0-9\-]+)", linkedin_url)
        if not match:
            raise Exception("ERROR: invalid URL || fetch_provider_id: could not extract identifier")

        identifier = match.group(1)
        url = f"{BASE_URL}/api/v1/users/{identifier}?account_id={account_id}"
        res = await requests.get(url, headers=HEADERS)

        if res.status_code == 200:
            return res.json().get("provider_id")

        raise Exception(f"ERROR: bad response || fetch_provider_id: {res.text}")
    except Exception as e:
        print(f"ERROR: failed to fetch provider_id || fetch_provider_id: {str(e)}")
        return None

async def send_connection_request(provider_id: str, account_id: str, message: str = "I'd like to connect with you on LinkedIn.") -> bool:
    try:
        url = f"{BASE_URL}/api/v1/users/invite"
        data = {
            "provider_id": provider_id,
            "account_id": account_id,
            "message": message
        }
        res = await requests.post(url, headers=HEADERS, json=data)

        if res.status_code == 201:
            return True

        raise Exception(f"ERROR: bad response || send_connection_request: {res.text}")
    except Exception as e:
        print(f"ERROR: failed to send connection || send_connection_request: {str(e)}")
        return False