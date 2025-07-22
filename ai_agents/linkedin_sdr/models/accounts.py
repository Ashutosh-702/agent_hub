from ..database import accounts_collection
from ..unipile_service import connect_account
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

async def validate_credentials(email: str, password: str) -> bool:
    """
    Returns True if credentials are valid, else False.
    """
    try:
        account = await accounts_collection.find_one({"linkedin_email": email})
        if account["linkedin_password"] != password:
            return False
        return True
    except Exception as e:
        print(f"ERROR: validate_credentials: {e}")
        return False

async def create_new_account(email: str, password: str) -> Optional[str]:
    """
    Creates a new account with the given email and password. Returns accId
    """
    try:
        account_id = await connect_account(email, password)
        
        if not account_id:
            print("ERROR: Failed to create account via Unipile API")
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


