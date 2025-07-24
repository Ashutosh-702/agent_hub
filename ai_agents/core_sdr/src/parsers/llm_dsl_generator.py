import json
import logging
from typing import Dict, Any, Optional

from openai import OpenAI

from ..schema import SchemaManager
logger = logging.getLogger(__name__)


class LLMDSLGenerator:
    """Generates Elasticsearch DSL queries directly from natural language using LLM."""
    
    def __init__(self, 
                 api_key: str,
                 model: str = "gpt-4o",
                 schema_manager: Optional[SchemaManager] = None):
        self.client = OpenAI(api_key=api_key)
        self.schema_manager = schema_manager or SchemaManager()
        # Load LLM config from schema manager
        llm_config = self.schema_manager.config.get("llm_config", {})
        self.model = model or llm_config.get("model", "gpt-4o")
        self.temperature = llm_config.get("temperature", 0.1)
        self.max_tokens = llm_config.get("max_tokens", 1500)
        self.reasoning_effort = llm_config.get("reasoning_effort", "medium")
        
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt with current schema information."""
        schema = self.schema_manager.get_schema()
        fields = schema.get("fields", {})
        
        prompt = """You are an expert Elasticsearch DSL query generator for CoreSignal company search.

Convert natural language queries into valid Elasticsearch DSL queries.

COMPANY SCHEMA:
"""
        
        # Add field information
        for field_name, field_info in fields.items():
            prompt += f"""
{field_name}:
  - Type: {field_info.get('elasticsearch_type', 'keyword')}
  - Description: {field_info.get('description', 'No description')}
  - Query Types: {', '.join(field_info.get('query_types', ['term']))}"""
            
            # Add predefined values if available
            predefined_values = field_info.get("predefined_values", [])
            if predefined_values:
                if isinstance(predefined_values, list) and len(predefined_values) <= 15:
                    prompt += f"\n  - Valid Values: {', '.join(map(str, predefined_values))}"
                elif isinstance(predefined_values, dict):
                    prompt += "\n  - Value Categories:"
                    for category, values in predefined_values.items():
                        if isinstance(values, list) and len(values) <= 10:
                            prompt += f"\n    * {category}: {', '.join(map(str, values))}"
                        else:
                            prompt += f"\n    * {category}: {len(values)} values available"
            
            # Add value ranges if available
            value_ranges = field_info.get("value_ranges", {})
            if value_ranges:
                prompt += "\n  - Value Ranges:"
                for range_name, range_value in value_ranges.items():
                    prompt += f"\n    * {range_name}: {range_value}"
        
        prompt += """

DSL GENERATION RULES:
1. Always return valid JSON that Elasticsearch can execute
2. Use appropriate query types based on field definitions above:
   - "match" for text fields with fuzzy matching
   - "term" for exact keyword matches
   - "range" for numeric/date fields
   - "nested" for nested objects like technologies_used
   - "bool" with "must" for AND conditions
   - "bool" with "should" for OR conditions
3. Only use predefined values when they exist for a field
4. For location queries, check country, state, and city fields
5. For technology queries, use nested query on technologies_used.technology
6. For employee/revenue ranges, use appropriate range operators (gte, lte, gt, lt)
7. Include "size" and "from" fields for pagination
8. Use fuzzy matching (fuzziness: "AUTO") for text searches when appropriate

OUTPUT FORMAT:
{
  "query": {
    // Your Elasticsearch query here
  },
  "size": 20,
  "from": 0
}

EXAMPLES:

Query: "AI startups in San Francisco with 10+ employees"
Output: {
  "query": {
    "bool": {
      "must": [
        {"match": {"industry": {"query": "Technology", "fuzziness": "AUTO"}}},
        {"term": {"type": "startup"}},
        {"match": {"hq_city": "San Francisco"}},
        {"range": {"employees_count": {"gte": 10}}}
      ]
    }
  },
  "size": 20,
  "from": 0
}

Query: "Public SaaS companies using AWS and React"
Output: {
  "query": {
    "bool": {
      "must": [
        {"match": {"industry": {"query": "Software", "fuzziness": "AUTO"}}},
        {"term": {"is_public": true}},
        {"nested": {
          "path": "technologies_used",
          "query": {
            "bool": {
              "must": [
                {"term": {"technologies_used.technology": "AWS"}},
                {"term": {"technologies_used.technology": "React"}}
              ]
            }
          }
        }}
      ]
    }
  },
  "size": 20,
  "from": 0
}

Query: "Healthcare companies founded after 2020"
Output: {
  "query": {
    "bool": {
      "must": [
        {"match": {"industry": "Healthcare"}},
        {"range": {"founded_year": {"gt": 2020}}}
      ]
    }
  },
  "size": 20,
  "from": 0
}

IMPORTANT: Always return valid JSON. Do not include any explanations or comments outside the JSON.
"""
        
        return prompt
    
    def generate_dsl(self, query: str, max_results: int = 20, from_offset: int = 0) -> Dict[str, Any]:
        """
        Generate Elasticsearch DSL query from natural language.
        
        Args:
            query: Natural language search query
            max_results: Maximum number of results
            from_offset: Offset for pagination
            
        Returns:
            Complete Elasticsearch DSL query dict
            
        Raises:
            Exception: If LLM request fails or returns invalid JSON
        """
        try:
            user_prompt = f"""Query: "{query}"
Max results: {max_results}
From offset: {from_offset}

Generate the Elasticsearch DSL query:"""
            
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # Add reasoning effort for reasoning models
            if "o1" in self.model.lower() or "reasoning" in self.model.lower():
                request_params["reasoning_effort"] = self.reasoning_effort
            
            response = self.client.chat.completions.create(**request_params)
            
            dsl_json = response.choices[0].message.content
            dsl_query = json.loads(dsl_json)
            
            # Ensure size and from are set correctly
            dsl_query["size"] = max_results
            dsl_query["from"] = from_offset
            
            # Validate the generated DSL
            self._validate_dsl(dsl_query)
            
            logger.debug(f"Generated DSL for query '{query}': {json.dumps(dsl_query, indent=2)}")
            return dsl_query
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            # Return fallback query
            return self._fallback_query(query, max_results, from_offset)
        
        except Exception as e:
            logger.error(f"DSL generation failed: {e}")
            # Return fallback query
            return self._fallback_query(query, max_results, from_offset)
    
    def _validate_dsl(self, dsl: Dict[str, Any]) -> None:
        """Validate the generated DSL query."""
        required_fields = ["query", "size"]
        for field in required_fields:
            if field not in dsl:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(dsl["size"], int) or dsl["size"] <= 0:
            raise ValueError("Invalid size field")
        
        if "from" in dsl and (not isinstance(dsl["from"], int) or dsl["from"] < 0):
            raise ValueError("Invalid from field")
        
        # Basic query structure validation
        query = dsl["query"]
        if not isinstance(query, dict):
            raise ValueError("Query must be a dictionary")
        
        # Check for common query types
        valid_root_queries = ["match_all", "bool", "match", "term", "range", "nested"]
        if not any(qt in query for qt in valid_root_queries):
            logger.warning(f"Unusual query structure: {list(query.keys())}")
    
    def _fallback_query(self, query: str, max_results: int, from_offset: int) -> Dict[str, Any]:
        """Generate a fallback query when LLM fails."""
        logger.warning(f"Using fallback query for: {query}")
        
        # Simple text search across common fields
        return {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["company_name^3", "industry^2", "description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": max_results,
            "from": from_offset
        }
    
    def explain_generation(self, query: str) -> Dict[str, Any]:
        """
        Generate DSL and provide explanation of the generation process.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with DSL query and explanation
        """
        dsl_query = self.generate_dsl(query)
        
        return {
            "original_query": query,
            "generated_dsl": dsl_query,
            "model_used": self.model,
            "schema_version": self.schema_manager.get_schema().get("version", "unknown"),
            "interpretation": self._interpret_dsl(dsl_query)
        }
    
    def _interpret_dsl(self, dsl_query: Dict[str, Any]) -> str:
        """Generate human-readable interpretation of the DSL query."""
        query = dsl_query.get("query", {})
        
        if "match_all" in query:
            return "Search all companies"
        
        if "bool" in query:
            bool_query = query["bool"]
            conditions = []
            
            if "must" in bool_query:
                for condition in bool_query["must"]:
                    conditions.append(self._interpret_condition(condition))
            
            if "should" in bool_query:
                should_conditions = [self._interpret_condition(c) for c in bool_query["should"]]
                conditions.append(f"({' OR '.join(should_conditions)})")
            
            return f"Find companies where: {' AND '.join(conditions)}"
        
        # Single condition
        return self._interpret_condition(query)
    
    def _interpret_condition(self, condition: Dict[str, Any]) -> str:
        """Interpret a single query condition."""
        if "match" in condition:
            field = list(condition["match"].keys())[0]
            value = condition["match"][field]
            if isinstance(value, dict):
                value = value.get("query", str(value))
            return f"{field} matches '{value}'"
        
        elif "term" in condition:
            field = list(condition["term"].keys())[0]
            value = condition["term"][field]
            return f"{field} equals '{value}'"
        
        elif "range" in condition:
            field = list(condition["range"].keys())[0]
            range_spec = condition["range"][field]
            parts = []
            if "gte" in range_spec:
                parts.append(f"{field} >= {range_spec['gte']}")
            if "lte" in range_spec:
                parts.append(f"{field} <= {range_spec['lte']}")
            if "gt" in range_spec:
                parts.append(f"{field} > {range_spec['gt']}")
            if "lt" in range_spec:
                parts.append(f"{field} < {range_spec['lt']}")
            return " AND ".join(parts)
        
        elif "nested" in condition:
            path = condition["nested"]["path"]
            nested_query = condition["nested"]["query"]
            nested_interpretation = self._interpret_condition(nested_query)
            return f"{path} contains {nested_interpretation}"
        
        else:
            return f"Complex condition: {list(condition.keys())[0]}"
    
    def refresh_schema(self) -> None:
        """Refresh the schema and rebuild system prompt."""
        self.schema_manager._load_config()
        self.system_prompt = self._build_system_prompt()
        logger.info("Schema refreshed and system prompt updated")