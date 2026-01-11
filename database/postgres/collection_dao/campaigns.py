"""PostgreSQL Campaigns DAO."""

from typing import Dict, Any, Optional, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import Campaign


class PostgresCampaignsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for campaigns table."""
    
    model = Campaign
    
    COLUMN_MAP = {
        "_id": "id",
        "name": "name",
        "campaign_type": "campaign_type",
        "lifecycle.status": "lifecycle_status",
        "prospecting_cycle.status": "prospecting_status",
        "ownership.user_email": "user_email",
        "shortlisting_approach": "shortlisting_approach",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "prompts": "prompts",
        "segmentation": "segmentation",
        "target": "target",
        "ownership": "ownership",
        "lifecycle": "lifecycle",
        "prospecting_cycle": "prospecting_cycle",
        "sequence_enrollment": "sequence_enrollment",
        "metadata": "metadata_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_campaign(self, campaign: dict) -> str:
        """Create a new campaign.
        
        Args:
            campaign: Campaign document
            
        Returns:
            Inserted document ID
        """
        # Extract searchable fields for columns
        if "lifecycle" in campaign:
            campaign["lifecycle_status"] = campaign["lifecycle"].get("status")
        if "prospecting_cycle" in campaign:
            campaign["prospecting_status"] = campaign["prospecting_cycle"].get("status")
        if "ownership" in campaign:
            campaign["user_email"] = campaign["ownership"].get("user_email")
        
        return await self.insert_one(campaign)
    
    async def get_campaigns(self, filters: dict = None) -> List[Dict[str, Any]]:
        """Get campaigns matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            List of campaign documents
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign document or None
        """
        return await self.find_one({"_id": campaign_id})

    async def update_campaign(self, campaign_id: str, update_data: dict) -> int:
        """Update a campaign.
        
        Args:
            campaign_id: Campaign ID
            update_data: Fields to update (supports both dot notation and nested dict)
            
        Returns:
            Number of modified documents
        """
        # Handle column mapping for specific fields
        # Support nested dict format: {"lifecycle": {"status": "value"}}
        if "lifecycle" in update_data and isinstance(update_data["lifecycle"], dict) and "status" in update_data["lifecycle"]:
            update_data["lifecycle_status"] = update_data["lifecycle"]["status"]
        if "prospecting_cycle" in update_data and isinstance(update_data["prospecting_cycle"], dict) and "status" in update_data["prospecting_cycle"]:
            update_data["prospecting_status"] = update_data["prospecting_cycle"]["status"]
        
        # Support dot notation format: {"lifecycle.status": "value"} or {"prospecting_cycle.status": "value"}
        # For these, we need to update BOTH the column AND the JSONB field
        # The dot notation paths in COLUMN_MAP are treated as columns by base_dao, NOT JSONB
        # So we must:
        # 1. Set the column value
        # 2. Convert dot notation to nested dict for JSONB merge
        # 3. Ensure nested paths are processed AFTER the base dict to avoid overwrites
        
        # Collect other nested updates that should be applied AFTER the base status
        nested_updates = {}
        
        if "lifecycle.status" in update_data:
            status_value = update_data.pop("lifecycle.status")
            update_data["lifecycle_status"] = status_value
            # Merge into lifecycle JSONB - but check for other nested lifecycle paths first
            lifecycle_base = {"status": status_value}
            for key in list(update_data.keys()):
                if key.startswith("lifecycle.") and key != "lifecycle.status":
                    nested_updates[key] = update_data.pop(key)
            update_data["lifecycle"] = lifecycle_base
            
        if "prospecting_cycle.status" in update_data:
            status_value = update_data.pop("prospecting_cycle.status")
            update_data["prospecting_status"] = status_value
            # Collect all other nested prospecting_cycle paths
            for key in list(update_data.keys()):
                if key.startswith("prospecting_cycle.") and key != "prospecting_cycle.status":
                    nested_updates[key] = update_data.pop(key)
            # Set the base dict FIRST
            update_data["prospecting_cycle"] = {"status": status_value}
        
        # Re-add nested updates so they are processed AFTER the base dict
        # This ensures _set_nested_value merges INTO the base dict rather than being overwritten
        update_data.update(nested_updates)
        
        return await self.update_one({"_id": campaign_id}, {"$set": update_data})
    
    async def update_campaign_status(self, campaign_id: str, status: str) -> int:
        """Update campaign lifecycle status.
        
        Args:
            campaign_id: Campaign ID
            status: New status
            
        Returns:
            Number of modified documents
        """
        return await self.update_one(
            {"_id": campaign_id}, 
            {"$set": {"lifecycle": {"status": status}, "lifecycle_status": status}}
        )

    async def get_campaign_by_status(self, status: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by lifecycle status.
        
        Args:
            status: Lifecycle status
            
        Returns:
            Campaign document or None
        """
        return await self.find_one({"lifecycle_status": status})

    async def get_campaigns_paginated(self, query: dict = None, page: int = 1, limit: int = 10) -> tuple:
        """Get paginated campaigns.
        
        Args:
            query: Query filters
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (results, pagination_info)
        """
        if query is None:
            query = {}
        query = self._process_query_objectids(query)
        return await self.get_paginated_response(query, page_size=limit, page_number=page)

    async def check_campaign_name_exists(self, campaign_name: str, exclude_campaign_id: str = None) -> bool:
        """Check if a campaign name already exists.
        
        Args:
            campaign_name: Campaign name to check
            exclude_campaign_id: Campaign ID to exclude (for updates)
            
        Returns:
            True if name exists
        """
        query = {"name": campaign_name}
        if exclude_campaign_id:
            query["_id"] = {"$ne": exclude_campaign_id}
        
        existing = await self.find_one(query)
        return existing is not None
    
    async def get_campaign_by_name(self, campaign_name: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by name.
        
        Args:
            campaign_name: Campaign name
            
        Returns:
            Campaign document or None
        """
        return await self.find_one({"name": campaign_name})


