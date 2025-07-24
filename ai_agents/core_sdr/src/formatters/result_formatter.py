import csv
import json
from abc import ABC, abstractmethod
from io import StringIO
from typing import List, Dict, Any, Optional

from ..core.models import Company, SearchResponse


class ResultFormatter(ABC):
    """Abstract base class for result formatters."""
    
    @abstractmethod
    def format(self, companies: List[Company], metadata: Dict[str, Any]) -> str:
        """Format companies data into specific output format."""
        pass


class JSONFormatter(ResultFormatter):
    """Format results as JSON."""
    
    def format(self, companies: List[Company], metadata: Dict[str, Any]) -> str:
        """
        Format companies as JSON.
        
        Args:
            companies: List of Company objects
            metadata: Search metadata
            
        Returns:
            JSON formatted string
        """
        # Convert companies to dictionaries, excluding raw_data by default
        companies_data = []
        for company in companies:
            company_dict = company.dict()
            # Remove raw_data to keep response clean unless specifically requested
            if 'raw_data' in company_dict and not metadata.get('include_raw_data', False):
                del company_dict['raw_data']
            companies_data.append(company_dict)
        
        result = {
            'companies': companies_data,
            'metadata': metadata
        }
        
        return json.dumps(result, indent=2, default=str)


class CSVFormatter(ResultFormatter):
    """Format results as CSV."""
    
    def __init__(self, fields: Optional[List[str]] = None):
        """
        Initialize CSV formatter.
        
        Args:
            fields: List of fields to include in CSV. If None, uses default fields.
        """
        self.fields = fields or [
            'company_name',
            'industry', 
            'hq_location',
            'employees_count',
            'founded_year',
            'website',
            'technologies',
            'is_public'
        ]
    
    def format(self, companies: List[Company], metadata: Dict[str, Any]) -> str:
        """
        Format companies as CSV.
        
        Args:
            companies: List of Company objects
            metadata: Search metadata
            
        Returns:
            CSV formatted string
        """
        if not companies:
            return self._create_empty_csv()
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.fields)
        
        # Write header
        writer.writeheader()
        
        # Write company data
        for company in companies:
            row = {}
            for field in self.fields:
                value = getattr(company, field, None)
                
                # Handle special formatting for certain fields
                if field == 'technologies' and value:
                    # Join technologies with semicolon for CSV
                    row[field] = '; '.join(value[:5])  # Limit to top 5
                elif field == 'is_public' and value is not None:
                    row[field] = 'Yes' if value else 'No'
                elif value is None:
                    row[field] = ''
                else:
                    row[field] = str(value)
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _create_empty_csv(self) -> str:
        """Create empty CSV with headers only."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.fields)
        writer.writeheader()
        return output.getvalue()


class SummaryFormatter(ResultFormatter):
    """Format results as human-readable summary."""
    
    def format(self, companies: List[Company], metadata: Dict[str, Any]) -> str:
        """
        Format companies as summary text.
        
        Args:
            companies: List of Company objects
            metadata: Search metadata
            
        Returns:
            Summary formatted string
        """
        if not companies:
            return "No companies found matching your criteria."
        
        lines = []
        
        # Add header with search info
        returned = len(companies)
        
        lines.append(f"Found {returned} companies:")
        lines.append("=" * 50)
        
        # Add each company summary
        for i, company in enumerate(companies, 1):
            lines.append(f"\n{i}. {self._format_company_summary(company)}")
        
        # Add footer with metadata
        lines.append("\n" + "=" * 50)
        
        if 'credits_used' in metadata:
            lines.append(f"Credits used: {metadata['credits_used']}")
        
        if 'processing_time' in metadata:
            lines.append(f"Processing time: {metadata['processing_time']:.1f}s")
        
        if metadata.get('cached', False):
            lines.append("Results served from cache")
        
        return "\n".join(lines)
    
    def _format_company_summary(self, company) -> str:
        """Format a single company as summary text."""
        parts = []
        
        # Handle both dict format (from MCP) and Company object format
        if isinstance(company, dict):
            # Simple MCP format: {"name": "...", "description": "..."}
            name = company.get('name', 'Unknown Company')
            parts.append(f"**{name}**")
            
            # Add description if available
            if company.get('description'):
                parts.append(f"• {company['description']}")
                
        else:
            # Full Company object format
            # Company name (required)
            name = company.company_name or f"Company ID: {company.id}"
            parts.append(f"**{name}**")
            
            # Industry and location
            details = []
            if company.industry:
                details.append(company.industry)
            if company.hq_location:
                details.append(company.hq_location)
            
            if details:
                parts.append(f"({', '.join(details)})")
            
            # Employee count
            if company.employees_count:
                parts.append(f"• {company.employees_count:,} employees")
            
            # Founded year
            if company.founded_year:
                parts.append(f"• Founded: {company.founded_year}")
            
            # Website
            if company.website:
                parts.append(f"• {company.website}")
            
            # Technologies (top 3)
            if company.technologies:
                tech_list = ', '.join(company.technologies[:3])
                if len(company.technologies) > 3:
                    tech_list += f" (+{len(company.technologies) - 3} more)"
                parts.append(f"• Tech: {tech_list}")
            
            # Public status
            if company.is_public is not None:
                status = "Public" if company.is_public else "Private"
                parts.append(f"• {status}")
        
        return " ".join(parts)


class ResultFormatterFactory:
    """Factory for creating result formatters."""
    
    _formatters = {
        'json': JSONFormatter,
        'csv': CSVFormatter,
        'summary': SummaryFormatter
    }
    
    @classmethod
    def create_formatter(self, format_type: str, **kwargs) -> ResultFormatter:
        """
        Create a result formatter for the specified format.
        
        Args:
            format_type: Format type ('json', 'csv', 'summary')
            **kwargs: Additional arguments for the formatter
            
        Returns:
            ResultFormatter instance
            
        Raises:
            ValueError: If format_type is not supported
        """
        if format_type not in self._formatters:
            raise ValueError(f"Unsupported format type: {format_type}")
        
        formatter_class = self._formatters[format_type]
        return formatter_class(**kwargs)
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported format types."""
        return list(cls._formatters.keys())


def format_search_response(search_response: SearchResponse, 
                         format_type: str = 'json',
                         **formatter_kwargs) -> str:
    """
    Convenience function to format a complete search response.
    
    Args:
        search_response: SearchResponse object
        format_type: Output format type
        **formatter_kwargs: Additional arguments for the formatter
        
    Returns:
        Formatted string
    """
    formatter = ResultFormatterFactory.create_formatter(format_type, **formatter_kwargs)
    
    companies = search_response.results.get('companies', [])
    
    # Check if we have simple MCP format (name/description only) or full Company data
    if companies and isinstance(companies[0], dict):
        # Check if it's the simple MCP format
        first_company = companies[0]
        if 'name' in first_company and 'description' in first_company and len(first_company) == 2:
            # Keep as simple dicts for MCP format - formatter will handle it
            pass
        else:
            # Convert dict to Company objects for full format
            companies = [Company(**company) for company in companies]
    
    return formatter.format(companies, search_response.metadata)