
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure
async def campaign_mongodb_indexes(mongo_client):
    """Create necessary indexes for MongoDB collections."""
    # Get stores collection
    campaigns_collection = mongo_client.linkedin_db.campaigns
    campaign_company_runs_collection = mongo_client.linkedin_db.campaign_company_runs
    companies_collection = mongo_client.linkedin_db.companies
    

    campaign_indexes = [
        # Existing unique index
        IndexModel(
            [("user_email", ASCENDING)],
            name="idx_user_email_unique"
        ),
        # For serviceable geohash queries
        IndexModel(
            [("status", ASCENDING)],
            name="idx_status_enum"
        )
    ]

    for index in campaign_indexes:
        try:
            await campaigns_collection.create_indexes([index])
            print("Created/verified MongoDB indexes for campaigns collection")
    
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise
