"""PostgreSQL Base DAO with MongoDB-compatible query interface.

This module provides a base DAO class that translates MongoDB-style queries
to SQLAlchemy queries, allowing for a gradual migration from MongoDB to PostgreSQL
while maintaining API compatibility.

Supported MongoDB operators:
- Query: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $exists, $regex, $or, $and
- Update: $set, $inc, $push, $addToSet, $unset

JSONB path access is supported via dot notation (e.g., "metadata.created_at")
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
import re
import json

from bson import ObjectId
from sqlalchemy import select, update, delete, func, text, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import DeclarativeBase

from database.postgres.models import Base


T = TypeVar("T", bound=DeclarativeBase)


def generate_objectid() -> str:
    """Generate a new ObjectId-style string for PostgreSQL.
    
    Returns:
        24-character hex string
    """
    return str(ObjectId())


def normalize_value_for_jsonb(value: Any) -> Any:
    """Convert ObjectId and datetime instances to JSON-serializable types for JSONB columns.
    
    Args:
        value: Any value that might be an ObjectId or datetime
        
    Returns:
        String if ObjectId, ISO format string if datetime, otherwise original value
    """
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def normalize_value(value: Any) -> Any:
    """Convert ObjectId instances to strings, but preserve datetime objects.
    
    For queries/filters, datetime objects should remain as datetime so PostgreSQL
    can properly compare them with TIMESTAMP columns.
    
    Args:
        value: Any value that might be an ObjectId
        
    Returns:
        String if ObjectId, otherwise original value (including datetime)
    """
    if isinstance(value, ObjectId):
        return str(value)
    # DO NOT convert datetime to string - let SQLAlchemy handle it properly
    return value


# Alias for backward compatibility
normalize_objectid = normalize_value


def normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively normalize ObjectIds in a document for queries.
    
    Preserves datetime objects for proper timestamp column comparisons.
    
    Args:
        doc: Document dictionary
        
    Returns:
        Document with ObjectIds converted to strings, datetimes preserved
    """
    if not isinstance(doc, dict):
        return normalize_value(doc)
    
    result = {}
    for key, value in doc.items():
        if isinstance(value, dict):
            result[key] = normalize_document(value)
        elif isinstance(value, list):
            result[key] = [normalize_document(item) if isinstance(item, dict) else normalize_value(item) for item in value]
        else:
            result[key] = normalize_value(value)
    return result


def normalize_document_for_jsonb(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively normalize ObjectIds and datetimes for JSONB storage.
    
    Args:
        doc: Document dictionary
        
    Returns:
        Document with ObjectIds and datetimes converted to strings
    """
    if not isinstance(doc, dict):
        return normalize_value_for_jsonb(doc)
    
    result = {}
    for key, value in doc.items():
        if isinstance(value, dict):
            result[key] = normalize_document_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [normalize_document_for_jsonb(item) if isinstance(item, dict) else normalize_value_for_jsonb(item) for item in value]
        else:
            result[key] = normalize_value_for_jsonb(value)
    return result


class BasePostgresDao:
    """Base Data Access Object for PostgreSQL with MongoDB-compatible interface."""
    
    # Model class to be set by subclasses
    model: Type[Base]
    
    # Mapping from MongoDB field names to SQLAlchemy column names
    # Subclasses should override this for their specific models
    COLUMN_MAP: Dict[str, str] = {
        "_id": "id",
    }
    
    # Fields stored in JSONB columns
    # Format: {"mongo_field": "jsonb_column_name"}
    JSONB_FIELDS: Dict[str, str] = {}
    
    # Array fields that need special handling
    ARRAY_FIELDS: List[str] = []
    
    def __init__(self, session: AsyncSession):
        """Initialize the DAO with a database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._session_factory = None  # Set by factory if available
        self._auto_commit = True  # Auto-commit after each operation by default
    
    @property
    def session(self) -> AsyncSession:
        """Get the current session."""
        return self._session
    
    @session.setter
    def session(self, value: AsyncSession):
        """Set the session."""
        self._session = value
    
    def set_session_factory(self, factory):
        """Set the session factory for creating new sessions.
        
        Args:
            factory: Callable that returns a new AsyncSession
        """
        self._session_factory = factory
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()
    
    async def close(self) -> None:
        """Close the session and return connection to pool."""
        await self._session.close()
    
    async def _get_fresh_session(self) -> AsyncSession:
        """Get a fresh session, closing the old one if needed."""
        if self._session_factory:
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
            self._session = self._session_factory()
        return self._session
    
    def _map_field(self, field: str) -> str:
        """Map MongoDB field name to PostgreSQL column name.
        
        Args:
            field: MongoDB field name (e.g., "_id", "lifecycle.status")
            
        Returns:
            PostgreSQL column name
        """
        # Direct mapping
        if field in self.COLUMN_MAP:
            return self.COLUMN_MAP[field]
        
        # Handle nested fields - check if base field is in JSONB_FIELDS
        base_field = field.split(".")[0]
        if base_field in self.JSONB_FIELDS:
            return field  # Will be handled as JSONB path
        
        # Default: return as-is (assume column name matches)
        return field.replace(".", "_")  # Convert dots to underscores for column names
    
    def _is_jsonb_field(self, field: str) -> bool:
        """Check if a field should be accessed via JSONB.
        
        Args:
            field: Field name
            
        Returns:
            True if field is in JSONB
        """
        # First check if there's an explicit column mapping - if so, use the column not JSONB
        if field in self.COLUMN_MAP:
            return False
        
        base_field = field.split(".")[0]
        return base_field in self.JSONB_FIELDS or "." in field
    
    def _get_jsonb_column(self, field: str) -> str:
        """Get the JSONB column name for a field.
        
        Args:
            field: Field name (potentially nested)
            
        Returns:
            JSONB column name
        """
        base_field = field.split(".")[0]
        return self.JSONB_FIELDS.get(base_field, "metadata_json")
    
    def _get_jsonb_path(self, field: str) -> List[str]:
        """Get the JSONB path for a nested field.
        
        Args:
            field: Field name (e.g., "lifecycle.status")
            
        Returns:
            List of path components
        """
        return field.split(".")
    
    def _build_jsonb_accessor(self, column_name: str, path: List[str]) -> Any:
        """Build SQLAlchemy expression for JSONB path access.
        
        Args:
            column_name: JSONB column name
            path: List of path components
            
        Returns:
            SQLAlchemy expression
        """
        column = getattr(self.model, column_name)
        
        # Use -> for intermediate keys and ->> for the final key (text extraction)
        if len(path) == 1:
            return column[path[0]].astext
        
        # Chain the path: column->'key1'->'key2'->>'final_key'
        expr = column[path[0]]
        for key in path[1:-1]:
            expr = expr[key]
        return expr[path[-1]].astext
    
    def _build_filter_expression(self, query: Dict[str, Any]) -> Any:
        """Build SQLAlchemy filter expression from MongoDB-style query.
        
        Args:
            query: MongoDB-style query dict
            
        Returns:
            SQLAlchemy filter expression
        """
        conditions = []
        
        for field, value in query.items():
            # Handle logical operators
            if field == "$or":
                or_conditions = [self._build_filter_expression(subq) for subq in value]
                conditions.append(or_(*or_conditions))
                continue
            
            if field == "$and":
                and_conditions = [self._build_filter_expression(subq) for subq in value]
                conditions.append(and_(*and_conditions))
                continue
            
            # Map field name
            mapped_field = self._map_field(field)
            
            # Normalize ObjectId values
            value = normalize_objectid(value)
            
            # Handle JSONB fields
            if self._is_jsonb_field(field):
                conditions.append(self._build_jsonb_filter(field, value))
                continue
            
            # Get column
            try:
                column = getattr(self.model, mapped_field)
            except AttributeError:
                # Field not found as column, try JSONB
                conditions.append(self._build_jsonb_filter(field, value))
                continue
            
            # Handle operators
            if isinstance(value, dict):
                for op, op_value in value.items():
                    op_value = normalize_objectid(op_value)
                    
                    if op == "$eq":
                        conditions.append(column == op_value)
                    elif op == "$ne":
                        # Handle special case: $ne: [] means "not empty"
                        # In PostgreSQL, translate to "is not null and != ''"
                        if isinstance(op_value, list) and len(op_value) == 0:
                            conditions.append(and_(column.isnot(None), column != ""))
                        else:
                            conditions.append(column != op_value)
                    elif op == "$gt":
                        conditions.append(column > op_value)
                    elif op == "$gte":
                        conditions.append(column >= op_value)
                    elif op == "$lt":
                        conditions.append(column < op_value)
                    elif op == "$lte":
                        conditions.append(column <= op_value)
                    elif op == "$in":
                        normalized_values = [normalize_objectid(v) for v in op_value]
                        conditions.append(column.in_(normalized_values))
                    elif op == "$nin":
                        normalized_values = [normalize_objectid(v) for v in op_value]
                        conditions.append(~column.in_(normalized_values))
                    elif op == "$exists":
                        if op_value:
                            conditions.append(column.isnot(None))
                        else:
                            conditions.append(column.is_(None))
                    elif op == "$regex":
                        # Use ILIKE for case-insensitive matching
                        pattern = f"%{op_value}%"
                        conditions.append(column.ilike(pattern))
                    else:
                        raise ValueError(f"Unsupported operator: {op}")
            else:
                # Simple equality
                conditions.append(column == value)
        
        if not conditions:
            return True  # No filter
        
        return and_(*conditions)
    
    def _build_jsonb_filter(self, field: str, value: Any) -> Any:
        """Build filter expression for JSONB field.
        
        Args:
            field: Field name with dot notation
            value: Filter value or operator dict
            
        Returns:
            SQLAlchemy filter expression
        """
        jsonb_column = self._get_jsonb_column(field)
        path = self._get_jsonb_path(field)
        
        column = getattr(self.model, jsonb_column)
        accessor = self._build_jsonb_accessor(jsonb_column, path)
        
        # Handle operators
        if isinstance(value, dict):
            conditions = []
            for op, op_value in value.items():
                op_value = normalize_objectid(op_value)
                
                if op == "$eq":
                    conditions.append(accessor == str(op_value))
                elif op == "$ne":
                    # Handle special case: $ne: [] means "not empty array" in JSONB
                    if isinstance(op_value, list) and len(op_value) == 0:
                        # Check that the JSONB array is not empty using jsonb_array_length
                        path_expr = "{" + ",".join(path) + "}"
                        conditions.append(text(f"jsonb_array_length({jsonb_column} #> '{path_expr}') > 0"))
                    else:
                        conditions.append(accessor != str(op_value))
                elif op == "$gt":
                    conditions.append(cast(accessor, String) > str(op_value))
                elif op == "$gte":
                    conditions.append(cast(accessor, String) >= str(op_value))
                elif op == "$lt":
                    conditions.append(cast(accessor, String) < str(op_value))
                elif op == "$lte":
                    conditions.append(cast(accessor, String) <= str(op_value))
                elif op == "$in":
                    normalized_values = [str(normalize_objectid(v)) for v in op_value]
                    conditions.append(accessor.in_(normalized_values))
                elif op == "$exists":
                    # Check if path exists in JSONB
                    path_expr = "{" + ",".join(path) + "}"
                    if op_value:
                        conditions.append(text(f"{jsonb_column} #> '{path_expr}' IS NOT NULL"))
                    else:
                        conditions.append(text(f"{jsonb_column} #> '{path_expr}' IS NULL"))
                elif op == "$regex":
                    conditions.append(accessor.ilike(f"%{op_value}%"))
                else:
                    raise ValueError(f"Unsupported JSONB operator: {op}")
            
            return and_(*conditions) if conditions else True
        else:
            # Simple equality
            return accessor == str(normalize_objectid(value))
    
    def _build_update_values(self, update_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Build SQLAlchemy update values from MongoDB-style update clause.
        
        Args:
            update_clause: MongoDB-style update dict (e.g., {"$set": {...}})
            
        Returns:
            Dict of column: value pairs for SQLAlchemy update
        """
        values = {}
        jsonb_updates = {}  # Track JSONB updates by column
        
        for op, fields in update_clause.items():
            if op == "$set":
                for field, value in fields.items():
                    mapped_field = self._map_field(field)
                    
                    if self._is_jsonb_field(field):
                        jsonb_column = self._get_jsonb_column(field)
                        path = self._get_jsonb_path(field)
                        
                        if jsonb_column not in jsonb_updates:
                            jsonb_updates[jsonb_column] = {}
                        
                        # Normalize for JSONB (convert datetime to string)
                        normalized_value = normalize_document_for_jsonb(value) if isinstance(value, dict) else normalize_value_for_jsonb(value)
                        
                        # If field is a top-level JSONB field, set directly (don't double-nest)
                        if len(path) == 1 and path[0] == jsonb_column:
                            jsonb_updates[jsonb_column] = normalized_value if isinstance(normalized_value, dict) else {path[0]: normalized_value}
                        else:
                            # Set nested path
                            self._set_nested_value(jsonb_updates[jsonb_column], path, normalized_value)
                    else:
                        # For regular columns, preserve datetime objects
                        value = normalize_objectid(value)  # Only normalize ObjectId, preserve datetime
                        try:
                            getattr(self.model, mapped_field)
                            values[mapped_field] = value
                        except AttributeError:
                            # Field doesn't exist as column, try JSONB
                            jsonb_column = "metadata_json"
                            if jsonb_column not in jsonb_updates:
                                jsonb_updates[jsonb_column] = {}
                            self._set_nested_value(jsonb_updates[jsonb_column], [field], normalize_value_for_jsonb(value))
            
            elif op == "$inc":
                for field, value in fields.items():
                    mapped_field = self._map_field(field)
                    try:
                        column = getattr(self.model, mapped_field)
                        values[mapped_field] = column + value
                    except AttributeError:
                        pass  # Skip for JSONB (would need special handling)
            
            elif op == "$push":
                # Handle array push - requires JSONB column
                for field, value in fields.items():
                    jsonb_column = self._get_jsonb_column(field)
                    path = self._get_jsonb_path(field)
                    
                    # This requires fetching current value and appending
                    # Will be handled specially in update methods
                    if jsonb_column not in jsonb_updates:
                        jsonb_updates[jsonb_column] = {"$push": {}}
                    jsonb_updates[jsonb_column]["$push"][".".join(path)] = normalize_document_for_jsonb(value) if isinstance(value, dict) else normalize_value_for_jsonb(value)
            
            elif op == "$addToSet":
                # Similar to $push but checks for duplicates
                for field, value in fields.items():
                    jsonb_column = self._get_jsonb_column(field)
                    path = self._get_jsonb_path(field)
                    
                    if jsonb_column not in jsonb_updates:
                        jsonb_updates[jsonb_column] = {"$addToSet": {}}
                    jsonb_updates[jsonb_column]["$addToSet"][".".join(path)] = normalize_document_for_jsonb(value) if isinstance(value, dict) else normalize_value_for_jsonb(value)
            
            elif op == "$unset":
                for field, _ in fields.items():
                    mapped_field = self._map_field(field)
                    try:
                        getattr(self.model, mapped_field)
                        values[mapped_field] = None
                    except AttributeError:
                        pass  # Skip for columns that don't exist
        
        # Handle JSONB updates
        for jsonb_column, updates in jsonb_updates.items():
            if "$push" in updates or "$addToSet" in updates:
                # These need special handling in the actual update method
                values[f"__{jsonb_column}_special"] = updates
            else:
                # Regular nested update - merge with existing
                values[f"__{jsonb_column}_merge"] = updates
        
        return values
    
    def _set_nested_value(self, d: Dict, path: List[str], value: Any) -> None:
        """Set a nested value in a dictionary.
        
        Args:
            d: Dictionary to update
            path: List of keys
            value: Value to set
        """
        for key in path[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[path[-1]] = value
    
    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document.
        
        Args:
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        # Normalize ObjectIds only (preserve datetime for timestamp columns)
        document = normalize_document(document)
        
        # Generate ID if not provided
        if "_id" not in document and "id" not in document:
            document["id"] = generate_objectid()
        elif "_id" in document:
            document["id"] = document.pop("_id")
        
        # Map fields to columns and separate JSONB data
        column_data = {}
        jsonb_data = {}
        
        for field, value in document.items():
            mapped_field = self._map_field(field)
            
            if self._is_jsonb_field(field):
                jsonb_column = self._get_jsonb_column(field)
                path = self._get_jsonb_path(field)
                
                if jsonb_column not in jsonb_data:
                    jsonb_data[jsonb_column] = {}
                
                # Normalize value for JSONB (convert datetime to string)
                normalized_value = normalize_document_for_jsonb(value) if isinstance(value, dict) else normalize_value_for_jsonb(value)
                
                # If field is a top-level JSONB field (e.g., "identifiers"), set directly
                # Otherwise it's a nested path (e.g., "identifiers.name"), use set_nested_value
                if len(path) == 1 and path[0] == jsonb_column:
                    # Direct assignment to JSONB column - don't double-nest
                    jsonb_data[jsonb_column] = normalized_value if isinstance(normalized_value, dict) else {path[0]: normalized_value}
                else:
                    self._set_nested_value(jsonb_data[jsonb_column], path, normalized_value)
            else:
                try:
                    getattr(self.model, mapped_field)
                    column_data[mapped_field] = value
                except AttributeError:
                    # Store unknown fields in metadata_json if it exists
                    if hasattr(self.model, "metadata_json"):
                        if "metadata_json" not in jsonb_data:
                            jsonb_data["metadata_json"] = {}
                        # Normalize for JSONB storage
                        jsonb_data["metadata_json"][field] = normalize_value_for_jsonb(value)
                    # Otherwise, silently skip unknown fields
        
        # Add JSONB data
        for jsonb_column, data in jsonb_data.items():
            column_data[jsonb_column] = data
        
        # Remove sl_no - let PostgreSQL auto-generate via sequence
        if "sl_no" in column_data:
            del column_data["sl_no"]
        
        # Add timestamps if not present and model has these fields
        now = datetime.utcnow()
        if "created_at" not in column_data and hasattr(self.model, "created_at"):
            column_data["created_at"] = now
        if "updated_at" not in column_data and hasattr(self.model, "updated_at"):
            column_data["updated_at"] = now
        
        # Create and add instance
        instance = self.model(**column_data)
        self._session.add(instance)
        await self._session.flush()
        
        result_id = instance.id
        
        # Auto-commit if enabled - commit and close to return connection to pool
        if self._auto_commit:
            await self._session.commit()
            await self._session.close()
            # Get fresh session for next operation if factory available
            if self._session_factory:
                self._session = self._session_factory()
        
        return result_id
    
    async def insert_many(self, documents: List[Dict[str, Any]], ordered: bool = False) -> List[str]:
        """Insert multiple documents.
        
        Args:
            documents: List of documents to insert
            ordered: If True, stop on first error (ignored in PostgreSQL)
            
        Returns:
            List of inserted document IDs
        """
        ids = []
        for doc in documents:
            doc_id = await self.insert_one(doc)
            ids.append(doc_id)
        return ids
    
    async def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Find a single document.
        
        Args:
            query: MongoDB-style query
            projection: Fields to include/exclude (not fully implemented)
            
        Returns:
            Document dict or None
        """
        # Normalize query
        query = normalize_document(query)
        
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr).limit(1)
        
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance is None:
            # Close session and get fresh one for next operation
            if self._session_factory:
                await self._session.close()
                self._session = self._session_factory()
            return None
        
        doc = self._instance_to_dict(instance)
        
        # Close session and get fresh one for next operation
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return doc
    
    async def find_many(
        self, 
        query: Dict[str, Any], 
        projection: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = None,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents.
        
        Args:
            query: MongoDB-style query
            projection: Fields to include/exclude (not fully implemented)
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples. Direction: 1=asc, -1=desc
            
        Returns:
            List of document dicts
        """
        # Normalize query
        query = normalize_document(query)
        
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr)
        
        # Apply sorting
        if sort:
            for field, direction in sort:
                mapped_field = self._map_field(field)
                try:
                    column = getattr(self.model, mapped_field)
                    if direction == -1:
                        stmt = stmt.order_by(column.desc())
                    else:
                        stmt = stmt.order_by(column.asc())
                except AttributeError:
                    pass  # Skip unknown fields
        elif skip is not None or limit is not None:
            # Default sorting for stable pagination when using skip/limit
            # Use sl_no (serial number) for optimal performance on large datasets
            if hasattr(self.model, 'sl_no'):
                stmt = stmt.order_by(self.model.sl_no.asc())
            elif hasattr(self.model, 'created_at'):
                stmt = stmt.order_by(self.model.created_at.desc())
                if hasattr(self.model, 'id'):
                    stmt = stmt.order_by(self.model.id.asc())
        
        # Apply pagination
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        # Close session and get fresh one for next operation
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs
    
    async def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query.
        
        Args:
            query: MongoDB-style query (optional, counts all if not provided)
            
        Returns:
            Count of matching documents
        """
        if query:
            query = normalize_document(query)
            filter_expr = self._build_filter_expression(query)
            stmt = select(func.count()).select_from(self.model).where(filter_expr)
        else:
            stmt = select(func.count()).select_from(self.model)
        
        result = await self._session.execute(stmt)
        count_result = result.scalar() or 0
        
        # Close session and get fresh one for next operation
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return count_result
    
    async def update_one(self, query: Dict[str, Any], update_clause: Dict[str, Any]) -> int:
        """Update a single document.
        
        Args:
            query: MongoDB-style query
            update_clause: MongoDB-style update (e.g., {"$set": {...}})
            
        Returns:
            Number of modified documents
        """
        # Normalize
        query = normalize_document(query)
        update_clause = normalize_document(update_clause)
        
        # Find the document first
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr).limit(1)
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance is None:
            return 0
        
        # Build update values
        values = self._build_update_values(update_clause)
        
        # Apply updates
        for key, value in values.items():
            if key.startswith("__") and key.endswith("_merge"):
                # JSONB merge update
                jsonb_column = key[2:-6]  # Remove __ prefix and _merge suffix
                current = getattr(instance, jsonb_column) or {}
                merged = self._deep_merge(current, value)
                setattr(instance, jsonb_column, merged)
            elif key.startswith("__") and key.endswith("_special"):
                # Special JSONB operations ($push, $addToSet)
                jsonb_column = key[2:-8]
                current = getattr(instance, jsonb_column) or {}
                
                for op, fields in value.items():
                    if op == "$push":
                        for path_str, item in fields.items():
                            path = path_str.split(".")
                            arr = self._get_nested_value(current, path) or []
                            arr.append(item)
                            self._set_nested_value(current, path, arr)
                    elif op == "$addToSet":
                        for path_str, item in fields.items():
                            path = path_str.split(".")
                            arr = self._get_nested_value(current, path) or []
                            if item not in arr:
                                arr.append(item)
                            self._set_nested_value(current, path, arr)
                
                setattr(instance, jsonb_column, current)
            else:
                setattr(instance, key, value)
        
        # Update timestamp if model has this field
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.utcnow()
        
        await self._session.flush()
        
        # Auto-commit if enabled - commit and close to return connection to pool
        if self._auto_commit:
            await self._session.commit()
            await self._session.close()
            # Get fresh session for next operation if factory available
            if self._session_factory:
                self._session = self._session_factory()
        
        return 1
    
    async def find_one_and_update(
        self,
        query: Dict[str, Any],
        update_clause: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        return_modified: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Find and update a document, returning the result.
        
        Args:
            query: MongoDB-style query
            update_clause: MongoDB-style update
            projection: Fields to include/exclude
            return_modified: If True, return modified document
            
        Returns:
            Document dict or None
        """
        # Normalize
        query = normalize_document(query)
        
        # Find before update if not returning modified
        if not return_modified:
            before = await self.find_one(query, projection)
        
        # Perform update
        await self.update_one(query, update_clause)
        
        if return_modified:
            return await self.find_one(query, projection)
        return before
    
    async def update_many(self, query: Dict[str, Any], update_clause: Dict[str, Any]) -> int:
        """Update multiple documents.
        
        Args:
            query: MongoDB-style query
            update_clause: MongoDB-style update
            
        Returns:
            Number of modified documents
        """
        # Normalize
        query = normalize_document(query)
        update_clause = normalize_document(update_clause)
        
        # Find all matching documents
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr)
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        if not instances:
            return 0
        
        # Build update values
        values = self._build_update_values(update_clause)
        
        count = 0
        for instance in instances:
            for key, value in values.items():
                if key.startswith("__") and key.endswith("_merge"):
                    jsonb_column = key[2:-6]
                    current = getattr(instance, jsonb_column) or {}
                    merged = self._deep_merge(current, value)
                    setattr(instance, jsonb_column, merged)
                elif key.startswith("__") and key.endswith("_special"):
                    jsonb_column = key[2:-8]
                    current = getattr(instance, jsonb_column) or {}
                    
                    for op, fields in value.items():
                        if op == "$push":
                            for path_str, item in fields.items():
                                path = path_str.split(".")
                                arr = self._get_nested_value(current, path) or []
                                arr.append(item)
                                self._set_nested_value(current, path, arr)
                        elif op == "$addToSet":
                            for path_str, item in fields.items():
                                path = path_str.split(".")
                                arr = self._get_nested_value(current, path) or []
                                if item not in arr:
                                    arr.append(item)
                                self._set_nested_value(current, path, arr)
                    
                    setattr(instance, jsonb_column, current)
                else:
                    setattr(instance, key, value)
            
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.utcnow()
            count += 1
        
        await self._session.flush()
        
        # Auto-commit if enabled - commit and close to return connection to pool
        if self._auto_commit:
            await self._session.commit()
            await self._session.close()
            # Get fresh session for next operation if factory available
            if self._session_factory:
                self._session = self._session_factory()
        
        return count
    
    async def delete_one(self, query: Dict[str, Any]) -> Dict[str, int]:
        """Delete a single document.
        
        Args:
            query: MongoDB-style query
            
        Returns:
            Dict with 'deleted_count' key (MongoDB-compatible)
        """
        query = normalize_document(query)
        
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr).limit(1)
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance is None:
            return {"deleted_count": 0}
        
        await self._session.delete(instance)
        await self._session.flush()
        
        # Auto-commit if enabled - commit and close to return connection to pool
        if self._auto_commit:
            await self._session.commit()
            await self._session.close()
            # Get fresh session for next operation if factory available
            if self._session_factory:
                self._session = self._session_factory()
        
        return {"deleted_count": 1}
    
    async def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents.
        
        Args:
            query: MongoDB-style query
            
        Returns:
            Number of deleted documents
        """
        query = normalize_document(query)
        
        filter_expr = self._build_filter_expression(query)
        stmt = select(self.model).where(filter_expr)
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        count = len(instances)
        for instance in instances:
            await self._session.delete(instance)
        
        await self._session.flush()
        
        # Auto-commit if enabled - commit and close to return connection to pool
        if self._auto_commit:
            await self._session.commit()
            await self._session.close()
            # Get fresh session for next operation if factory available
            if self._session_factory:
                self._session = self._session_factory()
        
        return count
    
    async def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching query.
        
        Args:
            filters: MongoDB-style query
            
        Returns:
            Count of matching documents
        """
        if filters is None:
            filters = {}
        
        filters = normalize_document(filters)
        filter_expr = self._build_filter_expression(filters)
        
        stmt = select(func.count()).select_from(self.model).where(filter_expr)
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        
        # Close session and get fresh one for next operation
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return count
    
    async def get_paginated_response(
        self,
        filter_query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        page_size: int = 10,
        page_number: int = 1,
        sort_by: Optional[List[tuple]] = None
    ) -> tuple:
        """Get paginated response.
        
        Args:
            filter_query: MongoDB-style query
            projection: Fields to include/exclude
            page_size: Items per page
            page_number: Page number (1-indexed)
            sort_by: List of (field, direction) tuples
            
        Returns:
            Tuple of (results list, pagination info dict)
        """
        filter_query = normalize_document(filter_query)
        filter_expr = self._build_filter_expression(filter_query)
        
        # Count total
        count_stmt = select(func.count()).select_from(self.model).where(filter_expr)
        count_result = await self._session.execute(count_stmt)
        total_records = count_result.scalar() or 0
        
        # Build query
        stmt = select(self.model).where(filter_expr)
        
        # Apply sorting
        if sort_by:
            for field, direction in sort_by:
                mapped_field = self._map_field(field)
                try:
                    column = getattr(self.model, mapped_field)
                    if direction == -1:
                        stmt = stmt.order_by(column.desc())
                    else:
                        stmt = stmt.order_by(column.asc())
                except AttributeError:
                    pass  # Skip invalid sort fields
        else:
            # Default sorting for stable pagination
            # Use sl_no (serial number) for optimal performance on large datasets
            if hasattr(self.model, 'sl_no'):
                stmt = stmt.order_by(self.model.sl_no.asc())
            elif hasattr(self.model, 'created_at'):
                stmt = stmt.order_by(self.model.created_at.desc())
                if hasattr(self.model, 'id'):
                    stmt = stmt.order_by(self.model.id.asc())
        
        # Apply pagination
        if page_size != -1:
            offset = (page_number - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
        
        result = await self._session.execute(stmt)
        instances = result.scalars().all()
        
        docs = [self._instance_to_dict(inst) for inst in instances]
        
        pagination_info = {
            "page_size": page_size,
            "page_number": page_number,
            "has_next": total_records - page_size * page_number > 0,
            "total_records": total_records
        }
        
        # Close session and get fresh one for next operation
        if self._session_factory:
            await self._session.close()
            self._session = self._session_factory()
        
        return docs, pagination_info
    
    def _instance_to_dict(self, instance: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy instance to dictionary.
        
        Args:
            instance: SQLAlchemy model instance
            
        Returns:
            Dictionary representation with MongoDB-compatible structure
        """
        result = {}
        
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            
            # Convert id to _id for MongoDB compatibility
            if column.name == "id":
                result["_id"] = value
            elif column.name.endswith("_json"):
                # Restore original field name for JSONB columns
                original_name = column.name[:-5]  # Remove "_json" suffix
                if original_name == "metadata":
                    result["metadata"] = value
                else:
                    result[original_name] = value
            else:
                result[column.name] = value
        
        return result
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            update: Dictionary with updates
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_nested_value(self, d: Dict, path: List[str]) -> Any:
        """Get a nested value from a dictionary.
        
        Args:
            d: Dictionary
            path: List of keys
            
        Returns:
            Value at path or None
        """
        for key in path:
            if not isinstance(d, dict) or key not in d:
                return None
            d = d[key]
        return d
    
    def _process_query_objectids(self, query: Optional[Dict] = None) -> Dict[str, Any]:
        """Process and normalize ObjectIds in query (MongoDB compatibility method).
        
        Args:
            query: Query dictionary
            
        Returns:
            Normalized query
        """
        return normalize_document(query) if query else {}


