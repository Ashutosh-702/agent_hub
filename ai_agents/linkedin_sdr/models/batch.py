import uuid
from typing import Optional

from ..database import batches_collection

async def create_batch(account_id: str) -> str:
    """
    Creates a new batch for the given account_id with is_completed=False. Returns the generated batch_id (UUID).
    """
    try:
        # Generate unique batch ID
        batch_id = str(uuid.uuid4())
        
        batch_doc = {
            "batch_id": batch_id,
            "account_id": account_id,
            "is_completed": False,
        }
        
        result = batches_collection.insert_one(batch_doc)
        
        if result.inserted_id:
            return batch_id
        else:
            raise Exception("Failed to create batch")
    except Exception as e:
        print(f"ERROR: create_batch: {e}")
        raise

async def get_batch(batch_id: str) -> Optional[dict]:
    """
    Fetches the batch document using batch_id. Returns the batch if found, else None.
    """
    try:
        return batches_collection.find_one({"batch_id": batch_id})
    except Exception as e:
        print(f"ERROR: get_batch: {e}")
        return None

async def update_batch_completion(batch_id: str, is_completed: bool) -> bool:
    """
    Update batch completion status
    """
    try:
        result = batches_collection.update_one(
            {"batch_id": batch_id},
            {
                "$set": {
                    "is_completed": is_completed,
                }
            }
        )
        
        return result.modified_count > 0
    except Exception as e:
        print(f"ERROR: update_batch_completion: {e}")
        return False
