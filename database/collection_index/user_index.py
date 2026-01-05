"""MongoDB indexes for user authentication collections."""

from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure


async def user_mongodb_indexes(mongo_client):
    """Create necessary indexes for users and user_tokens collections."""
    
    users_collection = mongo_client.linkedin_db.users
    user_tokens_collection = mongo_client.linkedin_db.user_tokens

    # Users collection indexes
    user_indexes = [
        # Unique email index for fast lookups and uniqueness constraint
        IndexModel(
            [("email", ASCENDING)],
            name="idx_users_email_unique",
            unique=True
        ),
        # Active users filter
        IndexModel(
            [("is_active", ASCENDING)],
            name="idx_users_is_active"
        ),
    ]

    # User tokens collection indexes
    token_indexes = [
        # Unique token index for fast lookups
        IndexModel(
            [("token", ASCENDING)],
            name="idx_user_tokens_token_unique",
            unique=True
        ),
        # User's tokens lookup
        IndexModel(
            [("user_id", ASCENDING)],
            name="idx_user_tokens_user_id"
        ),
        # Valid token lookups (token + not revoked + not expired)
        IndexModel(
            [("token", ASCENDING), ("is_revoked", ASCENDING), ("expires_at", ASCENDING)],
            name="idx_user_tokens_valid_lookup"
        ),
        # TTL index to auto-delete expired tokens after 30 days
        IndexModel(
            [("expires_at", ASCENDING)],
            name="idx_user_tokens_expires_at_ttl",
            expireAfterSeconds=30 * 24 * 60 * 60  # 30 days after expiry
        ),
    ]

    # Create users indexes
    for index in user_indexes:
        try:
            await users_collection.create_indexes([index])
            print(f"Created/verified MongoDB index for users collection: {index.document['name']}")
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise

    # Create user_tokens indexes
    for index in token_indexes:
        try:
            await user_tokens_collection.create_indexes([index])
            print(f"Created/verified MongoDB index for user_tokens collection: {index.document['name']}")
        except OperationFailure as e:
            if "Index already exists" in str(e):
                print(f"Index already exists: {str(e)}")
            else:
                print(f"Failed to create MongoDB indexes: {str(e)}")
                raise

