"""PostgreSQL Contacts DAO."""

from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres.base_dao import BasePostgresDao
from database.postgres.models import Contact


class PostgresContactsDao(BasePostgresDao):
    """PostgreSQL Data Access Object for contacts table."""
    
    model = Contact
    
    COLUMN_MAP = {
        "_id": "id",
        "company_id": "company_id",
        "contact_data.firstname": "firstname",
        "contact_data.lastname": "lastname",
        "contact_data.email": "email",
        "contact_data.jobtitle": "jobtitle",
        "contact_data.source_id": "source_id",
        "webhook_sent": "webhook_sent",
        "enrichment_status": "enrichment_status",
        "is_relevant": "is_relevant",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    JSONB_FIELDS = {
        "contact_data": "contact_data",
        "linkedin_data": "linkedin_data",
        "metadata": "metadata_json",
    }
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_contact(self, contact: dict) -> str:
        """Create a new contact.
        
        Args:
            contact: Contact document
            
        Returns:
            Inserted document ID
        """
        # Extract searchable fields for columns
        if "contact_data" in contact:
            contact["firstname"] = contact["contact_data"].get("firstname")
            contact["lastname"] = contact["contact_data"].get("lastname")
            # Email might be a list in MongoDB
            email = contact["contact_data"].get("email")
            if isinstance(email, list) and email:
                contact["email"] = email[0]
            elif isinstance(email, str):
                contact["email"] = email
            contact["jobtitle"] = contact["contact_data"].get("jobtitle")
            contact["source_id"] = contact["contact_data"].get("source_id")
        
        contact = self._process_query_objectids(contact)
        return await self.insert_one(contact)
    
    async def create_contacts(self, contacts: List[Dict[str, Any]]) -> List[str]:
        """Create multiple contacts.
        
        Args:
            contacts: List of contact documents
            
        Returns:
            List of inserted document IDs
        """
        ids = []
        for contact in contacts:
            doc_id = await self.create_contact(contact)
            ids.append(doc_id)
        return ids
    
    async def get_contacts(self, filters: dict = None) -> List[Dict[str, Any]]:
        """Get contacts matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            List of contact documents
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.find_many(filters)
    
    async def get_contact(self, contact_id: str, projection: dict = None) -> Optional[Dict[str, Any]]:
        """Get a contact by ID.
        
        Args:
            contact_id: Contact ID
            projection: Fields to include/exclude
            
        Returns:
            Contact document or None
        """
        return await self.find_one({"_id": contact_id}, projection=projection)

    async def update_contact(self, contact_id: str, update_clause: dict) -> int:
        """Update a contact.
        
        Args:
            contact_id: Contact ID
            update_clause: Update clause (MongoDB style)
            
        Returns:
            Number of modified documents
        """
        if "$set" in update_clause:
            set_clause = update_clause["$set"]
            
            # Build JSONB update for contact_data fields
            # Since contact_data.* fields are in COLUMN_MAP, they update columns only
            # We need to also update the JSONB to keep data in sync
            contact_data_updates = {}
            
            # Handle contact_data.email specially
            if "contact_data.email" in set_clause:
                email = set_clause["contact_data.email"]
                if isinstance(email, list) and email:
                    set_clause["email"] = email[0]  # First email in indexed column
                    contact_data_updates["email"] = email  # Full array in JSONB
                elif isinstance(email, str):
                    set_clause["email"] = email
                    contact_data_updates["email"] = [email]
                # Remove from set_clause to avoid column type mismatch
                del set_clause["contact_data.email"]
            
            # Handle other contact_data nested fields
            if "contact_data.firstname" in set_clause:
                set_clause["firstname"] = set_clause["contact_data.firstname"]
                contact_data_updates["firstname"] = set_clause.pop("contact_data.firstname")
            if "contact_data.lastname" in set_clause:
                set_clause["lastname"] = set_clause["contact_data.lastname"]
                contact_data_updates["lastname"] = set_clause.pop("contact_data.lastname")
            if "contact_data.jobtitle" in set_clause:
                set_clause["jobtitle"] = set_clause["contact_data.jobtitle"]
                contact_data_updates["jobtitle"] = set_clause.pop("contact_data.jobtitle")
            if "contact_data.phone" in set_clause:
                contact_data_updates["phone"] = set_clause.pop("contact_data.phone")
            if "contact_data.source_id" in set_clause:
                set_clause["source_id"] = set_clause["contact_data.source_id"]
                contact_data_updates["source_id"] = set_clause.pop("contact_data.source_id")
            
            # If we have contact_data updates, fetch current and merge
            if contact_data_updates:
                current = await self.find_one({"_id": contact_id})
                if current:
                    current_contact_data = current.get("contact_data", {}) or {}
                    current_contact_data.update(contact_data_updates)
                    set_clause["contact_data"] = current_contact_data
        
        return await self.update_one({"_id": contact_id}, update_clause)

    async def get_contacts_count(self, filters: dict = None) -> int:
        """Count contacts matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            Count of matching contacts
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.count_documents(filters)

    async def get_paginated_contacts(self, filters: dict = None, page: int = 1, 
                                     limit: int = 10, projection: dict = None) -> tuple:
        """Get paginated contacts.
        
        Args:
            filters: Query filters
            page: Page number
            limit: Items per page
            projection: Fields to include/exclude
            
        Returns:
            Tuple of (results, pagination_info)
        """
        if filters is None:
            filters = {}
        filters = self._process_query_objectids(filters)
        return await self.get_paginated_response(filters, page_size=limit, page_number=page, projection=projection)


