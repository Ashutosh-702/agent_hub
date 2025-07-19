def create_batch(account_id: str) -> str:
    """
    Creates a new batch for the given account_id with is_completed=False. Returns the generated batch_id (UUID).
    """

def get_batch(batch_id: str) -> dict:
    """
    Fetches the batch document using batch_id. Returns the batch if found, else None.
    """
