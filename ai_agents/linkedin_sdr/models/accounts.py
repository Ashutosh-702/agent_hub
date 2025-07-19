import os
import requests
from ..database import accounts_collection
from typing import Optional

async def get_account_id(email: str, password: str) -> Optional[str]:
    """
    Fetch account by email and password. Returns the account if found or None if not found.
    """
    try:
        account = await accounts_collection.find_one({
            "linkedin_email": email,
            "linkedin_password": password
        })
        if account:
            return account["account_id"]
        return None
    except Exception as e:
        print(f"ERROR: get_account_id: {e}")
        return None

async def validate_credentials(email: str, password: str) -> tuple[bool, str]:
    """
    Returns True if credentials are valid, else False.
    """
    try:
        account = await accounts_collection.find_one({"linkedin_email": email})
        if not account:
            return False, "account not found"
        
        if account["linkedin_password"] != password:
            return False, "invalid email-password combination"
        
        return True, "Valid credentials"
    except Exception as e:
        print(f"ERROR: validate_credentials: {e}")
        return False, "Error message"

async def create_new_account(email: str, password: str) -> Optional[str]:
    """
    Creates a new account with the given email and password. Returns accId
    """
    try:
        api_token = os.getenv("UNIPILE_API_TOKEN")
        base_url = os.getenv("UNIPILE_API_URL")
        
        url = f"{base_url}/api/v1/accounts"
        payload = {
            "provider": "LINKEDIN",
            "username": email,
            "password": password
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-KEY": api_token
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        # Debug logging, delete later
        print(f"DEBUG: Unipile API URL: {url}")
        print(f"DEBUG: Response Status: {response.status_code}")
        print(f"DEBUG: Response Text: {response.text}")
        
        if response.status_code != 201:
            print(f"APIERROR: Unipile account creation failed: {response.status_code}, {response.text}")
            return None
        
        data = response.json()
        account_id = data.get("account_id")
        
        if not account_id:
            print("ERROR: No account_id returned from Unipile API")
            return None
        
        await accounts_collection.insert_one({
            "linkedin_email": email,
            "linkedin_password": password,
            "account_id": account_id
        })
        
        return account_id
        
    except Exception as e:
        print(f"ERROR: create_new_account: {e}")
        return None


