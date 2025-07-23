from linkedin_sdr.database import batch_values_collection

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

async def find_pending_batches(batch_id: str, limit: int = None) -> list:
    """
    Finds and returns a list of batch value documents with status=False for the given batch_id.
    
    Args:
        batch_id: The batch ID to search for
        limit: Maximum number of records to return (None = return all)
    """
    try:
        query = batch_values_collection.find({
            "batch_id": batch_id,
            "status": False
        })
        
        # Apply limit if specified
        if limit is not None:
            query = query.limit(limit)
            
        return await query.to_list(length=None)
    except Exception as e:
        print(f"ERROR: find_pending_batches: {e}")
        return []

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

# Added for individual processor support...will be used for chronos individual processing
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

#Had to create this function for frontend working, no need in backend working
async def get_all_batch_values(batch_id: str) -> list:
    """
    OPTION 1: Get all batch values for a specific batch (needed for counting leads)
    Returns all LinkedIn URLs and their statuses for this batch
    """
    try:
        batch_values = await batch_values_collection.find({
            "batch_id": batch_id
        }).to_list(length=None)
        return batch_values
    except Exception as e:
        print(f"ERROR: get_all_batch_values: {e}")
        return []



