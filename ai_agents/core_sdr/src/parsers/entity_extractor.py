import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from ..core.models import ParsedEntity


class EntityExtractor:
    """Extract entities from natural language queries."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_configurations()
    
    def _load_configurations(self):
        """Load configuration files for entity matching."""
        try:
            with open(self.config_dir / "industries.json") as f:
                self.industries = json.load(f)
            
            with open(self.config_dir / "technologies.json") as f:
                self.technologies = json.load(f)
            
            with open(self.config_dir / "locations.json") as f:
                self.locations = json.load(f)
                
            with open(self.config_dir / "query_mappings.json") as f:
                self.mappings = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file not found: {e}")
    
    def extract_entities(self, query: str) -> ParsedEntity:
        """
        Extract all entities from a natural language query.
        
        Args:
            query: Natural language search query
            
        Returns:
            ParsedEntity object with extracted entities
        """
        query_lower = query.lower()
        
        return ParsedEntity(
            location=self._extract_location(query_lower),
            industry=self._extract_industry(query_lower),
            technology=self._extract_technology(query_lower),
            employees=self._extract_employee_range(query_lower),
            revenue=self._extract_revenue_range(query_lower),
            founded=self._extract_founded_range(query_lower),
            company_type=self._extract_company_type(query_lower),
            is_public=self._extract_public_status(query_lower),
            is_b2b=self._extract_b2b_status(query_lower)
        )
    
    def _extract_location(self, query: str) -> Optional[Dict[str, str]]:
        """Extract location entities from query."""
        location = {}
        
        # Check countries
        for country, variations in self.locations["countries"].items():
            for variation in variations:
                if variation in query:
                    location["country"] = country
                    break
        
        # Check US states
        for state, variations in self.locations["us_states"].items():
            for variation in variations:
                if variation in query:
                    location["state"] = state
                    break
        
        # Check cities
        for city, variations in self.locations["cities"].items():
            for variation in variations:
                if variation in query:
                    location["city"] = city
                    break
        
        return location if location else None
    
    def _extract_industry(self, query: str) -> Optional[List[str]]:
        """Extract industry entities from query."""
        found_industries = []
        
        for industry, keywords in self.industries.items():
            for keyword in keywords:
                if keyword in query:
                    found_industries.append(industry)
                    break
        
        return found_industries if found_industries else None
    
    def _extract_technology(self, query: str) -> Optional[List[str]]:
        """Extract technology entities from query."""
        found_technologies = []
        
        for tech_category, technologies in self.technologies.items():
            for tech in technologies:
                if tech in query:
                    found_technologies.append(tech)
        
        return found_technologies if found_technologies else None
    
    def _extract_employee_range(self, query: str) -> Optional[Dict[str, int]]:
        """Extract employee count ranges from query."""
        # Pattern for ranges like "10-50", "100+", "over 500", "less than 20"
        patterns = [
            r'(\d+)-(\d+)\s*employees?',
            r'(\d+)\+\s*employees?',
            r'over\s+(\d+)\s*employees?',
            r'more\s+than\s+(\d+)\s*employees?',
            r'above\s+(\d+)\s*employees?',
            r'less\s+than\s+(\d+)\s*employees?',
            r'under\s+(\d+)\s*employees?',
            r'below\s+(\d+)\s*employees?',
            r'at\s+least\s+(\d+)\s*employees?',
            r'minimum\s+(\d+)\s*employees?',
            r'(\d+)\s*employees?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                if '-' in pattern:  # Range pattern
                    return {"min": int(match.group(1)), "max": int(match.group(2))}
                elif '+' in pattern or 'over' in pattern or 'more than' in pattern or 'above' in pattern:
                    return {"min": int(match.group(1))}
                elif 'less than' in pattern or 'under' in pattern or 'below' in pattern:
                    return {"max": int(match.group(1))}
                elif 'at least' in pattern or 'minimum' in pattern:
                    return {"min": int(match.group(1))}
                else:  # Exact number
                    num = int(match.group(1))
                    # For exact numbers, create a range around it
                    return {"min": max(1, num - 10), "max": num + 10}
        
        return None
    
    def _extract_revenue_range(self, query: str) -> Optional[Dict[str, float]]:
        """Extract revenue ranges from query."""
        # Pattern for revenue like "$1M+", "over $500K", "$10M-$50M"
        patterns = [
            r'\$(\d+(?:\.\d+)?)[km]?\+',
            r'over\s+\$(\d+(?:\.\d+)?)[km]?',
            r'more\s+than\s+\$(\d+(?:\.\d+)?)[km]?',
            r'\$(\d+(?:\.\d+)?)[km]?-\$(\d+(?:\.\d+)?)[km]?',
            r'revenue.*?(\d+(?:\.\d+)?)[km]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                def convert_to_number(value_str, unit_char):
                    value = float(value_str)
                    if unit_char == 'k':
                        return value * 1000
                    elif unit_char == 'm':
                        return value * 1000000
                    return value
                
                if '-' in pattern and len(match.groups()) == 2:  # Range
                    min_val = convert_to_number(match.group(1), query[match.end(1):match.end(1)+1].lower())
                    max_val = convert_to_number(match.group(2), query[match.end(2):match.end(2)+1].lower())
                    return {"min": min_val, "max": max_val}
                elif '+' in pattern or 'over' in pattern or 'more than' in pattern:
                    min_val = convert_to_number(match.group(1), query[match.end(1):match.end(1)+1].lower())
                    return {"min": min_val}
        
        return None
    
    def _extract_founded_range(self, query: str) -> Optional[Dict[str, int]]:
        """Extract founding year ranges from query."""
        patterns = [
            r'founded\s+after\s+(\d{4})',
            r'founded\s+before\s+(\d{4})',
            r'founded\s+in\s+(\d{4})',
            r'established\s+after\s+(\d{4})',
            r'established\s+before\s+(\d{4})',
            r'established\s+in\s+(\d{4})',
            r'after\s+(\d{4})',
            r'before\s+(\d{4})',
            r'since\s+(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                year = int(match.group(1))
                if 'after' in pattern or 'since' in pattern:
                    return {"min": year}
                elif 'before' in pattern:
                    return {"max": year}
                else:  # Exact year
                    return {"min": year, "max": year}
        
        return None
    
    def _extract_company_type(self, query: str) -> Optional[str]:
        """Extract company type from query."""
        type_patterns = {
            'startup': [r'startup', r'start-up'],
            'enterprise': [r'enterprise', r'large company', r'corporation'],
            'sme': [r'small', r'medium', r'sme', r'small business'],
            'public': [r'public company', r'publicly traded'],
            'private': [r'private company', r'privately held']
        }
        
        for company_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return company_type
        
        return None
    
    def _extract_public_status(self, query: str) -> Optional[bool]:
        """Extract public/private status from query."""
        if re.search(r'\bpublic\b(?!\s+sector)', query):
            return True
        elif re.search(r'\bprivate\b', query):
            return False
        elif re.search(r'publicly\s+traded', query):
            return True
        elif re.search(r'privately\s+held', query):
            return False
        
        return None
    
    def _extract_b2b_status(self, query: str) -> Optional[bool]:
        """Extract B2B/B2C status from query."""
        if re.search(r'\bb2b\b|\bbusiness\s+to\s+business\b', query):
            return True
        elif re.search(r'\bb2c\b|\bbusiness\s+to\s+consumer\b', query):
            return False
        
        return None