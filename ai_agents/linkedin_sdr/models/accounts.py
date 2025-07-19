import uuid
from pymongo import MongoClient
from ..database import accounts_collection

async def get_account_id(email: str, password: str) -> str:
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
        account = accounts_collection.find_one({"linkedin_email": email})
        if not account:
            return False, "account not found"
        
        if account["linkedin_password"] != password:
            return False, "invalid email-password combination"
        
        return True, "Valid credentials"
    except Exception as e:
        print(f"ERROR: validate_credentials: {e}")
        return False

async def create_new_account(email: str, password: str) -> str:
    """
    Creates a new account with the given email and password. Returns accId
    """
    try:
        # TODO: Make actual UNIPILE API call to create account
        account_id = str(uuid.uuid4())
        await accounts_collection.insert_one({
            "linkedin_email": email,
            "linkedin_password": password,
            "account_id": account_id
        })
        return account_id
    except Exception as e:
        print(f"ERROR: create_new_account: {e}")
        return None
