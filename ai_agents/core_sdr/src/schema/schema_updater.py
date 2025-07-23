import json
import logging
import time
from collections import defaultdict
from typing import Dict, Any, List

from .feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class SchemaUpdater:
    """Handles schema updates through API discovery and validation."""
    
    def __init__(self, coresignal_client=None, config_file: str = "config/system_config.json"):
        self.coresignal_client = coresignal_client
        self.feature_flags = FeatureFlags(config_file)
        self.config_file = config_file
    
    def discover_schema_from_api(self, sample_size: int = 10) -> Dict[str, Any]:
        """Discover schema by analyzing API responses (if enabled)."""
        if not self.feature_flags.api_driven_updates_enabled():
            logger.info("API-driven schema discovery disabled via feature flags")
            return {}
        
        if not self.coresignal_client:
            logger.warning("No CoreSignal client provided for schema discovery")
            return {}
        
        logger.info(f"Discovering schema from {sample_size} API samples")
        
        try:
            # Make sample search to get company IDs
            sample_dsl = {"query": {"match_all": {}}, "size": sample_size}
            search_response = self.coresignal_client.search_companies_raw(sample_dsl)
            
            if not search_response or "hits" not in search_response:
                logger.warning("No search results for schema discovery")
                return {}
            
            company_ids = [hit["_id"] for hit in search_response["hits"]["hits"][:sample_size]]
            
            # Collect detailed company data
            discovered_schema = {"fields": {}, "new_values": defaultdict(set)}
            
            for company_id in company_ids:
                try:
                    company_data = self.coresignal_client.collect_company_raw(company_id)
                    if company_data:
                        self._analyze_company_data(company_data, discovered_schema)
                except Exception as e:
                    logger.warning(f"Failed to collect company {company_id}: {e}")
                    continue
            
            # Convert sets to lists for JSON serialization
            for field_name in discovered_schema["new_values"]:
                discovered_schema["new_values"][field_name] = list(discovered_schema["new_values"][field_name])
            
            logger.info(f"Discovered schema with {len(discovered_schema['fields'])} fields")
            return discovered_schema
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {e}")
            return {}
    
    def _analyze_company_data(self, company_data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Analyze a single company's data to extract schema information."""
        for field_name, value in company_data.items():
            field_type = self._infer_field_type(value)
            
            # Update field information
            if field_name not in schema["fields"]:
                schema["fields"][field_name] = {
                    "type": field_type,
                    "elasticsearch_type": self._map_to_elasticsearch_type(field_type),
                    "description": f"Auto-discovered field: {field_name}",
                    "discovered": True
                }
            
            # Collect possible values for certain field types
            if field_type in ["keyword", "boolean"] and value is not None:
                if isinstance(value, (str, int, bool)):
                    schema["new_values"][field_name].add(str(value))
            
            # Handle nested objects (like technologies_used)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value[:5]:  # Sample first 5 items
                    for nested_field, nested_value in item.items():
                        nested_field_name = f"{field_name}.{nested_field}"
                        if isinstance(nested_value, (str, int, bool)) and nested_value is not None:
                            schema["new_values"][nested_field_name].add(str(nested_value))
    
    def _infer_field_type(self, value: Any) -> str:
        """Infer field type from value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "long"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            # Use text for long strings, keyword for short ones
            return "text" if len(value) > 50 else "keyword"
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                return "nested"
            else:
                return "keyword"  # Array of simple values
        elif isinstance(value, dict):
            return "object"
        else:
            return "keyword"  # Default fallback
    
    def _map_to_elasticsearch_type(self, field_type: str) -> str:
        """Map internal field type to Elasticsearch type."""
        mapping = {
            "boolean": "boolean",
            "long": "long",
            "double": "double",
            "text": "text",
            "keyword": "keyword",
            "nested": "nested",
            "object": "object"
        }
        return mapping.get(field_type, "keyword")
    
    def update_predefined_values(self, recent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update predefined values by analyzing recent API responses (if enabled)."""
        if not self.feature_flags.api_driven_updates_enabled():
            logger.debug("API-driven value updates disabled via feature flags")
            return {}
        
        if not recent_responses:
            return {}
        
        logger.info(f"Analyzing {len(recent_responses)} recent responses for value updates")
        
        # Load current schema to get existing predefined values
        try:
            with open(self.config_file) as f:
                config = json.load(f)
            current_schema = config.get("coresignal_schema", {})
            fields = current_schema.get("fields", {})
        except Exception as e:
            logger.error(f"Error loading current schema: {e}")
            return {}
        
        # Analyze responses for new values
        discovered_updates = {"new_values": defaultdict(set), "field_frequency": defaultdict(int)}
        
        for response in recent_responses:
            self._extract_new_values(response, fields, discovered_updates)
        
        # Validate and filter discovered updates
        validated_updates = self._validate_discovered_values(discovered_updates, len(recent_responses))
        
        return validated_updates
    
    def _extract_new_values(self, response: Dict[str, Any], fields: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Extract new values from a single API response."""
        for field_name, field_info in fields.items():
            if field_name in response:
                value = response[field_name]
                
                # Track field frequency
                updates["field_frequency"][field_name] += 1
                
                # Extract values based on field type
                existing_values = field_info.get("predefined_values", [])
                
                if field_info.get("type") == "keyword" and isinstance(value, str):
                    if value not in existing_values:
                        updates["new_values"][field_name].add(value)
                
                elif field_info.get("type") == "nested" and isinstance(value, list):
                    # Handle nested fields like technologies_used
                    for item in value:
                        if isinstance(item, dict):
                            for nested_field, nested_value in item.items():
                                nested_field_name = f"{field_name}.{nested_field}"
                                if isinstance(nested_value, str):
                                    # Check against existing nested values
                                    existing_nested = self._get_nested_predefined_values(field_info, nested_field)
                                    if nested_value not in existing_nested:
                                        updates["new_values"][nested_field_name].add(nested_value)
    
    def _get_nested_predefined_values(self, field_info: Dict[str, Any], nested_field: str) -> List[str]:
        """Get existing predefined values for a nested field."""
        properties = field_info.get("properties", {})
        nested_info = properties.get(nested_field, {})
        predefined = nested_info.get("predefined_values", {})
        
        # Flatten nested predefined values
        all_values = []
        if isinstance(predefined, dict):
            for category_values in predefined.values():
                if isinstance(category_values, list):
                    all_values.extend(category_values)
        elif isinstance(predefined, list):
            all_values = predefined
        
        return all_values
    
    def _validate_discovered_values(self, discovered: Dict[str, Any], total_responses: int) -> Dict[str, Any]:
        """Validate discovered values based on frequency and confidence."""
        # Load validation rules from config
        try:
            with open(self.config_file) as f:
                config = json.load(f)
            validation_rules = config.get("schema_update_config", {}).get("validation_rules", {})
        except Exception:
            validation_rules = {}
        
        min_frequency = validation_rules.get("min_sample_size", 5)
        confidence_threshold = validation_rules.get("confidence_threshold", 0.1)  # 10% of responses
        max_new_values = validation_rules.get("max_new_values_per_update", 20)
        
        validated_updates = {"new_values": {}, "validation_info": {}}
        
        for field_name, values in discovered["new_values"].items():
            field_frequency = discovered["field_frequency"].get(field_name.split('.')[0], 0)
            
            # Calculate confidence (how often this field appears)
            confidence = field_frequency / total_responses if total_responses > 0 else 0
            
            validated_values = []
            for value in values:
                # For now, accept values that appear in fields with reasonable frequency
                if field_frequency >= min_frequency and confidence >= confidence_threshold:
                    validated_values.append(value)
            
            # Limit number of new values per field
            validated_values = validated_values[:max_new_values]
            
            if validated_values:
                validated_updates["new_values"][field_name] = validated_values
                validated_updates["validation_info"][field_name] = {
                    "frequency": field_frequency,
                    "confidence": confidence,
                    "total_new_values": len(values),
                    "accepted_values": len(validated_values)
                }
        
        logger.info(f"Validated {len(validated_updates['new_values'])} field updates")
        return validated_updates
    
    def merge_with_existing_schema(self, discovered_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Merge discovered schema updates with existing schema."""
        if not discovered_schema.get("new_values"):
            logger.info("No new values to merge")
            return {}
        
        try:
            # Load current config
            with open(self.config_file) as f:
                config = json.load(f)
            
            current_fields = config["coresignal_schema"]["fields"]
            updates_applied = {}
            
            # Merge new values into existing fields
            for field_name, new_values in discovered_schema["new_values"].items():
                if "." in field_name:
                    # Handle nested fields
                    parent_field, nested_field = field_name.split(".", 1)
                    if parent_field in current_fields:
                        properties = current_fields[parent_field].setdefault("properties", {})
                        nested_info = properties.setdefault(nested_field, {"type": "keyword"})
                        
                        # Add to existing predefined values
                        if "predefined_values" in nested_info:
                            if isinstance(nested_info["predefined_values"], dict):
                                # Add to 'other' category
                                other_category = nested_info["predefined_values"].setdefault("other", [])
                                for value in new_values:
                                    if value not in other_category:
                                        other_category.append(value)
                            elif isinstance(nested_info["predefined_values"], list):
                                for value in new_values:
                                    if value not in nested_info["predefined_values"]:
                                        nested_info["predefined_values"].append(value)
                        else:
                            nested_info["predefined_values"] = new_values
                        
                        updates_applied[field_name] = new_values
                else:
                    # Handle top-level fields
                    if field_name in current_fields:
                        current_values = current_fields[field_name].get("predefined_values", [])
                        for value in new_values:
                            if value not in current_values:
                                current_values.append(value)
                        current_fields[field_name]["predefined_values"] = current_values
                        updates_applied[field_name] = new_values
            
            # Update metadata
            config["coresignal_schema"]["last_schema_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            config["coresignal_schema"]["update_source"] = "api_discovery"
            
            # Save updated config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Schema updated with {len(updates_applied)} field changes")
            return updates_applied
            
        except Exception as e:
            logger.error(f"Error merging schema updates: {e}")
            return {}