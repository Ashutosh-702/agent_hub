# Dynamic CoreSignal Schema Management Plan

## Overview
Create a comprehensive schema management system that:
1. Maintains up-to-date CoreSignal field definitions
2. Includes predefined values for each attribute
3. Supports regular schema updates
4. Provides the LLM with complete context about available fields and values

## Schema Structure Design

### Enhanced Schema Format
```python
CORESIGNAL_SCHEMA = {
    "company_name": {
        "type": "text",
        "elasticsearch_type": "text",
        "searchable": True,
        "description": "Company's official name",
        "example_values": ["Apple Inc.", "Microsoft Corporation", "OpenAI"],
        "query_types": ["match", "fuzzy", "wildcard"]
    },
    "industry": {
        "type": "keyword", 
        "elasticsearch_type": "keyword",
        "searchable": True,
        "description": "Primary industry classification",
        "predefined_values": [
            "Technology", "Healthcare", "Finance", "Retail", "Manufacturing",
            "Education", "Real Estate", "Energy", "Media", "Transportation"
        ],
        "query_types": ["term", "terms", "match"]
    },
    "employees_count": {
        "type": "long",
        "elasticsearch_type": "long", 
        "range_queryable": True,
        "description": "Total number of employees",
        "value_ranges": {
            "startup": "1-50",
            "small": "51-200", 
            "medium": "201-1000",
            "large": "1001-5000",
            "enterprise": "5000+"
        },
        "query_types": ["range", "term"]
    },
    "company_type": {
        "type": "keyword",
        "elasticsearch_type": "keyword",
        "description": "Type of company organization",
        "predefined_values": [
            "startup", "sme", "enterprise", "corporation", "non-profit",
            "government", "partnership", "sole_proprietorship"
        ],
        "query_types": ["term", "terms"]
    },
    "technologies_used": {
        "type": "nested",
        "elasticsearch_type": "nested",
        "description": "Technologies and tools used by the company",
        "properties": {
            "technology": {
                "type": "keyword",
                "predefined_values": {
                    "cloud_platforms": ["AWS", "Azure", "Google Cloud", "Digital Ocean"],
                    "programming_languages": ["Python", "JavaScript", "Java", "C#", "Go"],
                    "frameworks": ["React", "Angular", "Django", "Spring", "Laravel"],
                    "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
                    "analytics": ["Google Analytics", "Mixpanel", "Tableau", "Power BI"]
                }
            }
        },
        "query_types": ["nested"]
    },
    "funding_total": {
        "type": "long",
        "elasticsearch_type": "long",
        "range_queryable": True,
        "description": "Total funding raised (USD)",
        "value_ranges": {
            "pre_seed": "0-250000",
            "seed": "250000-2000000", 
            "series_a": "2000000-15000000",
            "series_b": "15000000-50000000",
            "series_c_plus": "50000000+"
        },
        "query_types": ["range", "term"]
    },
    "headquarters_location": {
        "type": "object",
        "elasticsearch_type": "object",
        "description": "Company headquarters location",
        "properties": {
            "country": {
                "type": "keyword",
                "predefined_values": [
                    "United States", "United Kingdom", "Germany", "France", 
                    "Canada", "Australia", "India", "China", "Japan"
                ]
            },
            "state": {
                "type": "keyword", 
                "predefined_values": [
                    "California", "New York", "Texas", "Florida", "Illinois",
                    "Massachusetts", "Washington", "Colorado", "Georgia"
                ]
            },
            "city": {
                "type": "keyword",
                "predefined_values": [
                    "San Francisco", "New York", "Los Angeles", "Chicago",
                    "Boston", "Seattle", "Austin", "Miami", "London", "Berlin"
                ]
            }
        },
        "query_types": ["term", "terms"]
    },
    "is_public": {
        "type": "boolean",
        "elasticsearch_type": "boolean", 
        "description": "Whether company is publicly traded",
        "predefined_values": [True, False],
        "query_types": ["term"]
    },
    "founded_year": {
        "type": "date",
        "elasticsearch_type": "date",
        "range_queryable": True,
        "description": "Year company was founded",
        "value_ranges": {
            "very_new": "2020-2024",
            "new": "2015-2019", 
            "established": "2000-2014",
            "mature": "1980-1999",
            "legacy": "before 1980"
        },
        "query_types": ["range", "term"]
    }
}
```

## Implementation Architecture

### 1. Schema Management Components

```python
# src/schema/schema_manager.py
class SchemaManager:
    def __init__(self, schema_file: str = "config/coresignal_schema.json"):
        self.schema_file = schema_file
        self.schema = self._load_schema()
        self.last_updated = self._get_last_update_time()
        self.auto_update_enabled = self._check_feature_flag("SCHEMA_AUTO_UPDATE")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get current schema with optional auto-update check"""
        if self.auto_update_enabled and self._should_update():
            self.update_schema()
        return self.schema
    
    def update_schema(self) -> None:
        """Update schema from various sources (only if feature flag enabled)"""
        if not self.auto_update_enabled:
            logger.info("Schema auto-update disabled via feature flag")
            return
        
        logger.info("Updating schema...")
        # Update logic here
    
    def _check_feature_flag(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        import os
        return os.getenv(flag_name, "false").lower() in ("true", "1", "yes")
    
    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """Get detailed info about a specific field"""
        return self.schema.get(field_name, {})
    
    def get_predefined_values(self, field_name: str) -> List[Any]:
        """Get predefined values for a field"""
        field_info = self.schema.get(field_name, {})
        return field_info.get("predefined_values", [])
    
    def validate_query_value(self, field_name: str, value: Any) -> bool:
        """Validate if a value is valid for a field"""
        predefined_values = self.get_predefined_values(field_name)
        return value in predefined_values if predefined_values else True

# src/schema/schema_updater.py  
class SchemaUpdater:
    def __init__(self, coresignal_client, feature_flags=None):
        self.coresignal_client = coresignal_client
        self.feature_flags = feature_flags or {}
        self.update_enabled = self._check_feature_flag("SCHEMA_AUTO_UPDATE")
    
    def _check_feature_flag(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        import os
        return os.getenv(flag_name, "false").lower() in ("true", "1", "yes")
    
    def discover_schema_from_api(self) -> Dict[str, Any]:
        """Discover schema by analyzing API responses (if enabled)"""
        if not self.update_enabled:
            return {}
        # Discovery logic here
    
    def update_predefined_values(self) -> Dict[str, Any]:
        """Update predefined values by sampling data (if enabled)"""
        if not self.update_enabled:
            return {}
        # Update logic here
    
    def merge_with_existing_schema(self, new_schema: Dict) -> Dict[str, Any]:
        """Merge discovered schema with existing one"""
        # Always allow manual merging regardless of feature flag
        pass
```

### 2. Schema Update Strategies

#### A. Scheduled Updates (Feature Flag Controlled)
```python
# src/schema/schema_scheduler.py
class SchemaScheduler:
    def __init__(self, schema_manager: SchemaManager):
        self.schema_manager = schema_manager
        self.auto_update_enabled = self._check_feature_flag("SCHEMA_AUTO_UPDATE")
    
    def _check_feature_flag(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        import os
        return os.getenv(flag_name, "false").lower() in ("true", "1", "yes")
    
    def schedule_daily_update(self):
        """Schedule daily schema updates (only if enabled)"""
        if not self.auto_update_enabled:
            logger.info("Schema auto-update disabled - skipping scheduled updates")
            return
            
        import schedule
        schedule.every().day.at("02:00").do(self._update_schema)
    
    def schedule_weekly_deep_update(self):
        """Schedule weekly comprehensive updates (only if enabled)"""
        if not self.auto_update_enabled:
            return
            
        schedule.every().sunday.at("03:00").do(self._deep_update_schema)
    
    def _update_schema(self):
        """Light update - refresh predefined values (if enabled)"""
        if self.auto_update_enabled:
            self.schema_manager.update_schema()
    
    def _deep_update_schema(self):
        """Deep update - discover new fields and validate existing ones (if enabled)"""
        if self.auto_update_enabled:
            # Deep update logic here
            pass
```

#### B. API-Driven Updates (Feature Flag Controlled)
```python
# Update schema by analyzing recent API responses
def update_from_recent_queries(self, recent_responses: List[Dict]):
    """Update schema based on recent API responses (only if enabled)"""
    if not self._check_feature_flag("SCHEMA_AUTO_UPDATE"):
        logger.debug("Schema auto-update disabled - skipping API-driven update")
        return
    
    for response in recent_responses:
        self._analyze_response_structure(response)
        self._extract_new_values(response)
    
    self._save_updated_schema()

def _check_feature_flag(self, flag_name: str) -> bool:
    """Check if a feature flag is enabled"""
    import os
    return os.getenv(flag_name, "false").lower() in ("true", "1", "yes")
```

#### C. Manual Update Interface (Always Available)
```python
# CLI command for manual updates (works regardless of feature flag)
@click.command()
@click.option('--force', is_flag=True, help='Force update even if auto-update is disabled')
def update_schema(force):
    """Update CoreSignal schema manually"""
    schema_manager = SchemaManager()
    
    if not schema_manager.auto_update_enabled and not force:
        click.echo("Schema auto-update is disabled. Use --force to update anyway.")
        return
    
    schema_manager.update_schema()
    click.echo("Schema updated successfully")
```

### 3. LLM Integration

#### Enhanced System Prompt Generation
```python
class LLMPromptBuilder:
    def __init__(self, schema_manager: SchemaManager):
        self.schema_manager = schema_manager
    
    def build_system_prompt(self) -> str:
        """Build comprehensive system prompt with current schema"""
        schema = self.schema_manager.get_schema()
        
        prompt = """
You are an expert Elasticsearch DSL query generator for CoreSignal company search.

COMPANY SCHEMA:
"""
        
        for field_name, field_info in schema.items():
            prompt += f"""
{field_name}:
  - Type: {field_info['elasticsearch_type']}
  - Description: {field_info['description']}
  - Query Types: {', '.join(field_info['query_types'])}
"""
            
            if 'predefined_values' in field_info:
                values = field_info['predefined_values']
                if len(values) <= 20:  # Show all if reasonable number
                    prompt += f"  - Valid Values: {', '.join(map(str, values))}\n"
                else:  # Show categories or ranges
                    prompt += f"  - Value Categories: {self._format_value_categories(values)}\n"
        
        prompt += """
DSL GENERATION RULES:
1. Always return valid JSON
2. Use appropriate query types based on field definitions above
3. Only use predefined values when available
4. Combine conditions with bool/must for AND logic
5. Include size and from fields

OUTPUT FORMAT: {...}
"""
        
        return prompt
```

### 4. Unified Configuration File

#### config/system_config.json (Single Config File)
```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-15T10:30:00Z",
  
  "feature_flags": {
    "schema_auto_update": false,
    "schema_api_driven_updates": false,
    "schema_scheduled_updates": false
  },
  
  "coresignal_schema": {
    "version": "1.2.0",
    "last_schema_update": "2024-01-15T10:30:00Z",
    "update_source": "manual",
    "metadata": {
      "total_fields": 25,
      "api_version": "v2",
      "compatibility": "elasticsearch_7.x"
    },
    "fields": {
      "company_name": {
        "type": "text",
        "elasticsearch_type": "text",
        "searchable": true,
        "description": "Company's official name",
        "example_values": ["Apple Inc.", "Microsoft Corporation", "OpenAI"],
        "query_types": ["match", "fuzzy", "wildcard"]
      },
      "industry": {
        "type": "keyword",
        "elasticsearch_type": "keyword",
        "searchable": true,
        "description": "Primary industry classification",
        "predefined_values": [
          "Technology", "Healthcare", "Finance", "Retail", "Manufacturing",
          "Education", "Real Estate", "Energy", "Media", "Transportation",
          "Artificial Intelligence", "Machine Learning", "Software", "SaaS"
        ],
        "query_types": ["term", "terms", "match"]
      },
      "employees_count": {
        "type": "long",
        "elasticsearch_type": "long",
        "range_queryable": true,
        "description": "Total number of employees",
        "value_ranges": {
          "startup": "1-50",
          "small": "51-200",
          "medium": "201-1000",
          "large": "1001-5000",
          "enterprise": "5000+"
        },
        "query_types": ["range", "term"]
      },
      "company_type": {
        "type": "keyword",
        "elasticsearch_type": "keyword",
        "description": "Type of company organization",
        "predefined_values": [
          "startup", "sme", "enterprise", "corporation", "non-profit",
          "government", "partnership", "sole_proprietorship"
        ],
        "query_types": ["term", "terms"]
      },
      "technologies_used": {
        "type": "nested",
        "elasticsearch_type": "nested",
        "description": "Technologies and tools used by the company",
        "properties": {
          "technology": {
            "type": "keyword",
            "predefined_values": {
              "cloud_platforms": ["AWS", "Azure", "Google Cloud", "Digital Ocean"],
              "programming_languages": ["Python", "JavaScript", "Java", "C#", "Go", "Rust"],
              "frameworks": ["React", "Angular", "Django", "Spring", "Laravel", "FastAPI"],
              "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch"],
              "analytics": ["Google Analytics", "Mixpanel", "Tableau", "Power BI"]
            }
          }
        },
        "query_types": ["nested"]
      },
      "headquarters_location": {
        "type": "object",
        "elasticsearch_type": "object",
        "description": "Company headquarters location",
        "properties": {
          "country": {
            "type": "keyword",
            "predefined_values": [
              "United States", "United Kingdom", "Germany", "France",
              "Canada", "Australia", "India", "China", "Japan"
            ]
          },
          "state": {
            "type": "keyword",
            "predefined_values": [
              "California", "New York", "Texas", "Florida", "Illinois",
              "Massachusetts", "Washington", "Colorado", "Georgia"
            ]
          },
          "city": {
            "type": "keyword",
            "predefined_values": [
              "San Francisco", "New York", "Los Angeles", "Chicago",
              "Boston", "Seattle", "Austin", "Miami", "London", "Berlin"
            ]
          }
        },
        "query_types": ["term", "terms"]
      },
      "is_public": {
        "type": "boolean",
        "elasticsearch_type": "boolean",
        "description": "Whether company is publicly traded",
        "predefined_values": [true, false],
        "query_types": ["term"]
      },
      "founded_year": {
        "type": "date",
        "elasticsearch_type": "date",
        "range_queryable": true,
        "description": "Year company was founded",
        "value_ranges": {
          "very_new": "2020-2024",
          "new": "2015-2019",
          "established": "2000-2014",
          "mature": "1980-1999",
          "legacy": "before 1980"
        },
        "query_types": ["range", "term"]
      }
    }
  },
  
  "schema_update_config": {
    "update_schedule": {
      "daily_update": "02:00",
      "weekly_deep_update": "sunday_03:00"
    },
    "update_sources": {
      "api_discovery": true,
      "manual_validation": true,
      "documentation_scraping": false
    },
    "validation_rules": {
      "min_sample_size": 100,
      "confidence_threshold": 0.8,
      "max_new_values_per_update": 50
    }
  }
}
```

### 5. Schema Validation & Quality

#### Data Quality Checks
```python
class SchemaValidator:
    def validate_schema_quality(self, schema: Dict) -> Dict[str, Any]:
        """Validate schema quality and completeness"""
        results = {
            "coverage": self._check_field_coverage(schema),
            "accuracy": self._check_value_accuracy(schema), 
            "completeness": self._check_predefined_values_completeness(schema),
            "consistency": self._check_field_consistency(schema)
        }
        return results
    
    def suggest_improvements(self, validation_results: Dict) -> List[str]:
        """Suggest schema improvements based on validation"""
        suggestions = []
        if validation_results["coverage"] < 0.9:
            suggestions.append("Discover missing fields through API sampling")
        if validation_results["accuracy"] < 0.8:
            suggestions.append("Validate predefined values against recent data")
        return suggestions
```

## Benefits of This Approach

### 1. **Comprehensive LLM Context**
- LLM knows exact field names and types
- Understands valid values for each field
- Can generate more accurate DSL queries

### 2. **Controlled Automatic Maintenance (Feature Flag Controlled)**
- Schema updates only when explicitly enabled
- Safe default: manual updates only
- Predefined values updated on-demand
- Reduces manual maintenance overhead when enabled

### 3. **Quality Assurance**
- Validation ensures schema accuracy
- Quality metrics track schema health
- Suggestions for improvements

### 4. **Flexibility & Safety**
- Easy to add new fields manually
- Feature flags prevent unwanted changes
- Multiple update sources when enabled
- Always allows manual overrides

## Feature Flag Environment Variables

```bash
# Schema update controls
SCHEMA_AUTO_UPDATE=false           # Master switch for all auto-updates
SCHEMA_API_DRIVEN_UPDATES=false   # API response analysis updates
SCHEMA_SCHEDULED_UPDATES=false    # Scheduled daily/weekly updates

# Manual updates always work regardless of flags
# Use CLI commands with --force to override
```

## Implementation Timeline

**Week 1**: Core schema management infrastructure + feature flag system
**Week 2**: Schema discovery and update mechanisms (behind flags)
**Week 3**: LLM integration with enhanced prompts
**Week 4**: Scheduling, validation, and monitoring (all feature-flagged)

## Deployment Strategy

### Phase 1: Static Schema (Safe Default)
- Deploy with all feature flags disabled
- Schema updates only via manual CLI commands
- Validates existing functionality

### Phase 2: Controlled Testing  
- Enable feature flags in development/staging
- Test auto-update mechanisms
- Validate schema quality improvements

### Phase 3: Production Rollout
- Optionally enable feature flags in production
- Monitor schema update quality
- Can disable immediately if issues arise

**Approval needed for:**
1. Schema structure format ✓
2. Feature flag approach ✓  
3. Default state (auto-update disabled) ✓
4. Manual override capabilities ✓

This approach ensures safety-first deployment while providing the option for automated schema maintenance when needed.