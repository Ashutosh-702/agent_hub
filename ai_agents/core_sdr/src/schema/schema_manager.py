import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages CoreSignal schema with feature-flagged auto-updates."""
    
    def __init__(self, config_file: str = "config/system_config.json"):
        self.config_file = Path(config_file)
        self.feature_flags = FeatureFlags(config_file)
        self.schema: Optional[Dict[str, Any]] = None
        self.config: Optional[Dict[str, Any]] = None
        self.last_loaded = 0
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration and schema from file."""
        try:
            with open(self.config_file) as f:
                self.config = json.load(f)
            
            self.schema = self.config.get("coresignal_schema", {})
            self.last_loaded = time.time()
            
            logger.info(f"Loaded schema with {len(self.schema.get('fields', {}))} fields")
            
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """Get current schema with optional auto-update check."""
        # Check if we should auto-update (only if feature flag enabled)
        if self.feature_flags.schema_auto_update_enabled() and self._should_update():
            logger.info("Auto-update enabled and due - updating schema")
            self.update_schema()
        
        if self.schema is None:
            self._load_config()
        
        return self.schema
    
    def _should_update(self) -> bool:
        """Check if schema should be updated based on time elapsed."""
        if not self.schema:
            return True
        
        # Update every 24 hours if auto-update enabled
        time_since_update = time.time() - self.last_loaded
        return time_since_update > 86400  # 24 hours
    
    def update_schema(self, force: bool = False) -> None:
        """Update schema from various sources (only if enabled or forced)."""
        if not force and not self.feature_flags.schema_auto_update_enabled():
            logger.info("Schema auto-update disabled via feature flags")
            return
        
        logger.info("Updating schema...")
        
        # For now, just reload from file
        # In future, this would trigger SchemaUpdater
        self._load_config()
        
        # Update timestamp
        if self.config:
            self.config["coresignal_schema"]["last_schema_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self._save_config()
    
    def _save_config(self) -> None:
        """Save current config back to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.debug("Config saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """Get detailed info about a specific field."""
        schema = self.get_schema()
        fields = schema.get("fields", {})
        return fields.get(field_name, {})
    
    def get_predefined_values(self, field_name: str) -> List[Any]:
        """Get predefined values for a field."""
        field_info = self.get_field_info(field_name)
        return field_info.get("predefined_values", [])
    
    def get_all_predefined_values(self) -> Dict[str, List[Any]]:
        """Get all predefined values for all fields."""
        schema = self.get_schema()
        fields = schema.get("fields", {})
        result = {}
        
        for field_name, field_info in fields.items():
            if "predefined_values" in field_info:
                result[field_name] = field_info["predefined_values"]
            elif field_info.get("type") == "nested" and "properties" in field_info:
                # Handle nested fields like technologies_used
                for prop_name, prop_info in field_info["properties"].items():
                    if "predefined_values" in prop_info:
                        result[f"{field_name}.{prop_name}"] = prop_info["predefined_values"]
        
        return result
    
    def validate_query_value(self, field_name: str, value: Any) -> bool:
        """Validate if a value is valid for a field."""
        predefined_values = self.get_predefined_values(field_name)
        if not predefined_values:
            return True  # No restrictions if no predefined values
        
        # Handle nested predefined values (like technologies)
        if isinstance(predefined_values, dict):
            # Flatten all values from all categories
            all_values = []
            for category_values in predefined_values.values():
                if isinstance(category_values, list):
                    all_values.extend(category_values)
            return value in all_values
        
        return value in predefined_values
    
    def get_elasticsearch_mapping(self) -> Dict[str, Any]:
        """Generate Elasticsearch mapping from schema."""
        schema = self.get_schema()
        fields = schema.get("fields", {})
        
        mapping = {"properties": {}}
        
        for field_name, field_info in fields.items():
            es_type = field_info.get("elasticsearch_type", "keyword")
            
            if es_type == "nested":
                mapping["properties"][field_name] = {
                    "type": "nested",
                    "properties": {}
                }
                
                # Add nested properties
                if "properties" in field_info:
                    for prop_name, prop_info in field_info["properties"].items():
                        prop_type = prop_info.get("type", "keyword")
                        mapping["properties"][field_name]["properties"][prop_name] = {
                            "type": prop_type
                        }
            
            elif es_type == "object":
                mapping["properties"][field_name] = {
                    "type": "object",
                    "properties": {}
                }
                
                # Add object properties
                if "properties" in field_info:
                    for prop_name, prop_info in field_info["properties"].items():
                        prop_type = prop_info.get("type", "keyword")
                        mapping["properties"][field_name]["properties"][prop_name] = {
                            "type": prop_type
                        }
            
            else:
                mapping["properties"][field_name] = {"type": es_type}
                
                # Add text fields with keyword mapping
                if es_type == "text":
                    mapping["properties"][field_name]["fields"] = {
                        "keyword": {"type": "keyword"}
                    }
        
        return mapping
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema metadata and statistics."""
        schema = self.get_schema()
        fields = schema.get("fields", {})
        
        field_count = len(fields)
        fields_with_predefined = sum(
            1 for field in fields.values() 
            if "predefined_values" in field
        )
        
        total_predefined_values = 0
        for field in fields.values():
            if "predefined_values" in field:
                values = field["predefined_values"]
                if isinstance(values, list):
                    total_predefined_values += len(values)
                elif isinstance(values, dict):
                    for category_values in values.values():
                        if isinstance(category_values, list):
                            total_predefined_values += len(category_values)
        
        return {
            "version": schema.get("version", "unknown"),
            "last_update": schema.get("last_schema_update", "unknown"),
            "total_fields": field_count,
            "fields_with_predefined_values": fields_with_predefined,
            "total_predefined_values": total_predefined_values,
            "auto_update_enabled": self.feature_flags.schema_auto_update_enabled(),
            "api_driven_updates_enabled": self.feature_flags.api_driven_updates_enabled(),
            "scheduled_updates_enabled": self.feature_flags.scheduled_updates_enabled()
        }