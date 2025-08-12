"""Health check endpoints for leadgen Kafka consumer."""
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

def add_health_endpoints(app: FastAPI):
    """Add health check endpoints to FastAPI app."""
    
    @app.get("/_healthz")
    async def healthz():
        """Kubernetes health check endpoint."""
        return ORJSONResponse(status_code=200, content={"status": "healthy"})
    
    @app.get("/_readyz")
    async def readyz():
        """Kubernetes readiness check endpoint."""
        return ORJSONResponse(status_code=200, content={"status": "ready"})