
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure
async def company_mapping_mongodb_indexes(mongo_client):
    """Create necessary indexes for MongoDB collections."""
    # Get stores collection
    company_mappings_collection = mongo_client.linkedin_db.company_mappings
    
    company_mapping_indexes = [
        # Existing unique index
        IndexModel(
            [("campaign_id", ASCENDING)],
            name="idx_campaign_id_unique"
        )
    ]
    for index in company_mapping_indexes:
        try:
            await company_mappings_collection.create_indexes([index])
            print("Created/verified MongoDB indexes for company_mappings collection")
    
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise
