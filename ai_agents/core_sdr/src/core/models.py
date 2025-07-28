from typing import Dict, Any

from pydantic import BaseModel, Field

class DSLQuery(BaseModel):
    """Elasticsearch DSL query payload"""
    query: Dict[str, Any] = Field(..., description="Elasticsearch DSL query payload")