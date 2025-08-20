
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure
async def campaign_company_run_mongodb_indexes(mongo_client):
    """Create necessary indexes for MongoDB collections."""
    # Get stores collection
    campaign_company_runs_collection = mongo_client.linkedin_db.campaign_company_runs
    
    campaign_company_run_indexes = [
        # Existing unique index
        IndexModel(
            [("campaign_id", ASCENDING)],
            name="idx_campaign_id_unique"
        )
    ]
    for index in campaign_company_run_indexes:
        try:
            await campaign_company_runs_collection.create_indexes([index])
            print("Created/verified MongoDB indexes for campaign_company_runs collection")
    
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise
