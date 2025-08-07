
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure
async def companies_mongodb_indexes(mongo_client):
    """Create necessary indexes for MongoDB collections."""
    # Get stores collection
    companies_collection = mongo_client.linkedin_db.companies
    


    company_indexes = [
        # Existing unique index
        IndexModel(
            [("industry", ASCENDING)],
            name="idx_company_id_unique"
        )

    ]
    for index in company_indexes:
        try:
            await companies_collection.create_indexes([index])
            print("Created/verified MongoDB indexes for companies collection")
    
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise
