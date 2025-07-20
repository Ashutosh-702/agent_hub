from ..database import batch_values_collection

async def add_batch(batch_id: str, linkedin_url: str, task: str) -> None:
    """
    Adds a new batch value document with the given batch_id, linkedin_url, and task(hardcoded "connection" for now).
    Status is set to False by default.
    """
    try:
        batch_value_doc = {
            "batch_id": batch_id,
            "data": {
                "url": linkedin_url,
                "task": task
            },
            "status": False
        }
        
        await batch_values_collection.insert_one(batch_value_doc)
    except Exception as e:
        print(f"ERROR: add_batch: {e}")

async def find_pending_batches(batch_id: str) -> list:
    """
    Finds and returns a list of batch value documents with status=False for the given batch_id.
    """
    try:
        return await batch_values_collection.find({
            "batch_id": batch_id,
            "status": False
        }).to_list(length=None) 
    except Exception as e:
        print(f"ERROR: find_pending_batches: {e}")
        return []

# NEW: Added for individual processor support
async def get_batch_value_by_url(batch_id: str, linkedin_url: str) -> dict | None:
    """
    Gets a specific batch value by batch_id and linkedin_url.
    """
    try:
        return await batch_values_collection.find_one({
            "batch_id": batch_id,
            "data.url": linkedin_url
        })
    except Exception as e:
        print(f"ERROR: get_batch_value_by_url: {e}")
        return None

async def update_status(batch_id: str, linkedin_url: str, status: bool = True) -> None:
    """
    Updates the status of a specific linkedin_url in the given batch_id to the given status.
    """
    try:
        await batch_values_collection.update_one(
            {
                "batch_id": batch_id,
                "data.url": linkedin_url
            },
            {
                "$set": {"status": status}
            }
        )
    except Exception as e:
        print(f"ERROR: update_status: {e}")
