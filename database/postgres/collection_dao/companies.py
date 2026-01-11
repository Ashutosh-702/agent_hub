"""PostgreSQL Companies DAO."""

from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import Company


class PostgresCompaniesDao(BasePostgresDao):
    """PostgreSQL Data Access Object for companies table."""
    
    model = Company
    
    COLUMN_MAP = {
        "_id": "id",
        "identifiers.name": "name",
        "identifiers.source_id": "source_id",
        "identifiers.source_domain": "source_domain",
        "profile.industry": "industry",
        "metadata.api_response.primary_domain": "primary_domain",
        "source": "source",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "identifiers": "identifiers",
        "profile": "profile",
        "location": "location",
        "metadata": "metadata_json",
        "deep_research": "deep_research",
        "red_flags_history": "red_flags_history",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_company(self, company: dict) -> str:
        """Create a new company.
        
        Args:
            company: Company document
            
        Returns:
            Inserted document ID
        """
        # Extract searchable fields for columns
        if "identifiers" in company:
            company["name"] = company["identifiers"].get("name")
            company["source_id"] = company["identifiers"].get("source_id")
            company["source_domain"] = company["identifiers"].get("source_domain")
        
        if "profile" in company:
            company["industry"] = company["profile"].get("industry")
        
        if "metadata" in company and "api_response" in company["metadata"]:
            company["primary_domain"] = company["metadata"]["api_response"].get("primary_domain")
        
        return await self.insert_one(company)
    
    async def create_companies(self, companies: List[Dict[str, Any]]) -> List[str]:
        """Create multiple companies.
        
        Args:
            companies: List of company documents
            
        Returns:
            List of inserted document IDs
        """
        ids = []
        for company in companies:
            doc_id = await self.create_company(company)
            ids.append(doc_id)
        return ids
    
    async def get_companies(self, filters: dict = None) -> List[Dict[str, Any]]:
        """Get companies matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            List of company documents
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID.
        
        Args:
            company_id: Company ID
            
        Returns:
            Company document or None
        """
        return await self.find_one({"_id": company_id})

    async def get_company_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get a company by its domain.
        
        Args:
            domain: Domain to search
            
        Returns:
            Company document or None
        """
        # Try source_domain first
        company = await self.find_one({"source_domain": domain})
        if company:
            return company
        
        # Try primary_domain
        company = await self.find_one({"primary_domain": domain})
        if company:
            return company
        
        # Try regex search in metadata (less efficient)
        # Note: This would need special handling for JSONB
        return None
    
    async def get_company_by_source_domain(self, source_domain: str) -> Optional[Dict[str, Any]]:
        """Get a company by source domain.
        
        Args:
            source_domain: Source domain
            
        Returns:
            Company document or None
        """
        return await self.find_one({"source_domain": source_domain})

    async def get_company_by_filters(self, filters: dict = None) -> Optional[Dict[str, Any]]:
        """Get a single company matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            Company document or None
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_one(filters)
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> int:
        """Update a company.
        
        Args:
            company_id: Company ID
            update_data: Fields to update (supports both dot notation and nested dict)
            
        Returns:
            Number of modified documents
        """
        has_operators = any(key.startswith('$') for key in update_data.keys())
        if not has_operators:
            update_data = {"$set": update_data}
        
        # Handle dot notation that maps to both columns and JSONB
        # For fields like "identifiers.source_id", we need to update both:
        # 1. The source_id column (for indexed queries)
        # 2. The identifiers JSONB (for data consistency when reading)
        if "$set" in update_data:
            set_data = update_data["$set"]
            
            # Track JSONB updates needed
            identifiers_updates = {}
            profile_updates = {}
            metadata_updates = {}
            
            # Map dot notation to column names and collect JSONB updates
            if "identifiers.name" in set_data:
                set_data["name"] = set_data["identifiers.name"]
                identifiers_updates["name"] = set_data.pop("identifiers.name")
            if "identifiers.source_id" in set_data:
                set_data["source_id"] = set_data["identifiers.source_id"]
                identifiers_updates["source_id"] = set_data.pop("identifiers.source_id")
            if "identifiers.source_domain" in set_data:
                set_data["source_domain"] = set_data["identifiers.source_domain"]
                identifiers_updates["source_domain"] = set_data.pop("identifiers.source_domain")
            if "profile.industry" in set_data:
                set_data["industry"] = set_data["profile.industry"]
                profile_updates["industry"] = set_data.pop("profile.industry")
            if "metadata.updated_at" in set_data:
                metadata_updates["updated_at"] = set_data.pop("metadata.updated_at")
            if "metadata.api_response.primary_domain" in set_data:
                set_data["primary_domain"] = set_data["metadata.api_response.primary_domain"]
                del set_data["metadata.api_response.primary_domain"]
            
            # Merge JSONB updates with current data if any
            if identifiers_updates or profile_updates or metadata_updates:
                current = await self.find_one({"_id": company_id})
                if current:
                    if identifiers_updates:
                        current_identifiers = current.get("identifiers", {}) or {}
                        current_identifiers.update(identifiers_updates)
                        set_data["identifiers"] = current_identifiers
                    if profile_updates:
                        current_profile = current.get("profile", {}) or {}
                        current_profile.update(profile_updates)
                        set_data["profile"] = current_profile
                    if metadata_updates:
                        current_metadata = current.get("metadata", {}) or {}
                        if isinstance(current_metadata, str):
                            current_metadata = {}
                        current_metadata.update(metadata_updates)
                        set_data["metadata"] = current_metadata
            
        return await self.update_one({"_id": company_id}, update_data)
    
    async def get_companies_paginated(self, query: dict = None, page: int = 1, limit: int = 100) -> tuple:
        """Get paginated companies.
        
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
    
    async def add_red_flags(self, company_id: str, meeting_id: str, flags: List[Dict[str, Any]], 
                           transcript_excerpts: Dict[str, Any] = None) -> int:
        """Add red flags from a meeting.
        
        Args:
            company_id: Company ID
            meeting_id: Meeting ID
            flags: List of flag objects
            transcript_excerpts: Relevant transcript excerpts
            
        Returns:
            Number of modified documents
        """
        red_flag_entry = {
            "meeting_id": meeting_id,
            "date": datetime.utcnow(),
            "flags": flags,
            "transcript_excerpts": transcript_excerpts or {},
        }
        
        return await self.update_one(
            {"_id": company_id},
            {"$push": {"red_flags_history": red_flag_entry}}
        )
    
    async def get_red_flags_history(self, company_id: str) -> List[Dict[str, Any]]:
        """Get red flags history for a company.
        
        Args:
            company_id: Company ID
            
        Returns:
            List of red flag entries
        """
        company = await self.get_company(company_id)
        if not company:
            return []
        return company.get("red_flags_history", [])
    
    async def set_deep_research(self, company_id: str, research_data: Dict[str, Any]) -> int:
        """Set deep research data.
        
        Args:
            company_id: Company ID
            research_data: Research data
            
        Returns:
            Number of modified documents
        """
        update_data = {
            "deep_research": {
                "last_updated": datetime.utcnow(),
                "data": research_data,
            }
        }
        return await self.update_company(company_id, update_data)
    
    async def get_deep_research(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get deep research data.
        
        Args:
            company_id: Company ID
            
        Returns:
            Deep research data or None
        """
        company = await self.get_company(company_id)
        if not company:
            return None
        return company.get("deep_research")


