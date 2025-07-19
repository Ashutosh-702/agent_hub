def add_batch(batch_id: str, linkedin_url: str, task: str) -> None:
    """
    Adds a new batch value document with the given batch_id, linkedin_url, and task(hardcoded "connection" for now).
    Status is set to False by default.
    """

def find_pending_batches(batch_id: str) -> list:
    """
    Finds and returns a list of batch value documents with status=False for the given batch_id.
    
    """

def update_status(batch_id: str, linkedin_url: str, status: bool = True) -> None:
    """
    Updates the status of a specific linkedin_url in the given batch_id to the given status.
    """
