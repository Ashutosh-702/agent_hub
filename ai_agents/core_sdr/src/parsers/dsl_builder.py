import json
from pathlib import Path
from typing import Dict, List, Any

from ..core.models import ParsedEntity, DSLQuery


class DSLQueryBuilder:
    """Build Elasticsearch DSL queries from parsed entities."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_mappings()
    
    def _load_mappings(self):
        """Load field mappings configuration."""
        try:
            with open(self.config_dir / "query_mappings.json") as f:
                self.mappings = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("query_mappings.json configuration file not found")
    
    def build_dsl_query(self, entities: ParsedEntity, size: int = 20, from_offset: int = 0) -> DSLQuery:
        """
        Build Elasticsearch DSL query from parsed entities.
        
        Args:
            entities: Parsed entities from natural language query
            size: Maximum number of results to return
            from_offset: Offset for pagination
            
        Returns:
            DSLQuery object containing the Elasticsearch query
        """
        query_parts = {
            "bool": {
                "must": [],
                "should": [],
                "filter": []
            }
        }
        
        # Add location filters
        if entities.location:
            self._add_location_filters(query_parts, entities.location)
        
        # Add industry filters
        if entities.industry:
            self._add_industry_filters(query_parts, entities.industry)
        
        # Add technology filters
        if entities.technology:
            self._add_technology_filters(query_parts, entities.technology)
        
        # Add employee range filters
        if entities.employees:
            self._add_range_filter(query_parts, "employees_count", entities.employees)
        
        # Add revenue range filters
        if entities.revenue:
            self._add_range_filter(query_parts, "revenue_annual.source_1_annual_revenue.annual_revenue", entities.revenue)
        
        # Add founded year filters
        if entities.founded:
            self._add_range_filter(query_parts, "founded_year", entities.founded)
        
        # Add boolean filters
        if entities.is_public is not None:
            self._add_exact_filter(query_parts, "is_public", entities.is_public)
        
        if entities.is_b2b is not None:
            self._add_exact_filter(query_parts, "is_b2b", entities.is_b2b)
        
        # Add company type filter
        if entities.company_type:
            self._add_exact_filter(query_parts, "type", entities.company_type)
        
        # Clean up empty query parts
        query_parts["bool"] = {k: v for k, v in query_parts["bool"].items() if v}
        
        # If no filters were added, add a match_all query
        if not any(query_parts["bool"].values()):
            return DSLQuery(
                query={"match_all": {}},
                size=size,
                from_=from_offset
            )
        
        return DSLQuery(
            query=query_parts,
            size=size,
            from_=from_offset
        )
    
    def _add_location_filters(self, query_parts: Dict, location: Dict[str, str]):
        """Add location-based filters to the query."""
        location_should = []
        
        if "country" in location:
            location_should.append({
                "term": {
                    self.mappings["location_fields"]["country"]: location["country"]
                }
            })
        
        if "state" in location:
            location_should.append({
                "term": {
                    self.mappings["location_fields"]["state"]: location["state"]
                }
            })
        
        if "city" in location:
            location_should.append({
                "term": {
                    self.mappings["location_fields"]["city"]: location["city"]
                }
            })
        
        if location_should:
            query_parts["bool"]["must"].append({
                "bool": {
                    "should": location_should,
                    "minimum_should_match": 1
                }
            })
    
    def _add_industry_filters(self, query_parts: Dict, industries: List[str]):
        """Add industry-based filters to the query."""
        industry_should = []
        
        for industry in industries:
            industry_should.append({
                "match": {
                    self.mappings["exact_fields"]["industry"]: {
                        "query": industry,
                        "fuzziness": "AUTO"
                    }
                }
            })
        
        if industry_should:
            query_parts["bool"]["must"].append({
                "bool": {
                    "should": industry_should,
                    "minimum_should_match": 1
                }
            })
    
    def _add_technology_filters(self, query_parts: Dict, technologies: List[str]):
        """Add technology-based filters to the query."""
        tech_should = []
        
        for tech in technologies:
            tech_should.append({
                "nested": {
                    "path": "technologies_used",
                    "query": {
                        "match": {
                            self.mappings["exact_fields"]["technology"]: {
                                "query": tech,
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                }
            })
        
        if tech_should:
            query_parts["bool"]["must"].append({
                "bool": {
                    "should": tech_should,
                    "minimum_should_match": 1
                }
            })
    
    def _add_range_filter(self, query_parts: Dict, field: str, range_dict: Dict[str, Any]):
        """Add range-based filters to the query."""
        range_query = {}
        
        if "min" in range_dict:
            range_query["gte"] = range_dict["min"]
        
        if "max" in range_dict:
            range_query["lte"] = range_dict["max"]
        
        if range_query:
            query_parts["bool"]["filter"].append({
                "range": {
                    field: range_query
                }
            })
    
    def _add_exact_filter(self, query_parts: Dict, field: str, value: Any):
        """Add exact match filters to the query."""
        query_parts["bool"]["filter"].append({
            "term": {
                field: value
            }
        })
    
    def add_text_search(self, query_parts: Dict, search_text: str, fields: List[str] = None):
        """Add full-text search across specified fields."""
        if not fields:
            fields = ["company_name^3", "description^2", "industry"]
        
        query_parts["bool"]["must"].append({
            "multi_match": {
                "query": search_text,
                "fields": fields,
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    
    def add_sorting(self, dsl_query: Dict, sort_field: str = "employees_count", sort_order: str = "desc"):
        """Add sorting to the DSL query."""
        dsl_query["sort"] = [
            {sort_field: {"order": sort_order, "missing": "_last"}}
        ]
        return dsl_query
    
    def add_aggregations(self, dsl_query: Dict, aggs: Dict[str, Any]):
        """Add aggregations to the DSL query."""
        dsl_query["aggs"] = aggs
        return dsl_query