"""Health check related Pydantic schemas."""

from typing import Any, Dict

from pydantic import Field

from ai_agents.leadgen.workflow.ai_agent import DictDataResponse


class HealthResponse(DictDataResponse):
    """Health check response model."""
    data: Dict[str, Any] = Field(description="Health status data")


class ReadinessResponse(DictDataResponse):
    """Readiness check response model."""
    data: Dict[str, Any] = Field(description="Readiness status data")
