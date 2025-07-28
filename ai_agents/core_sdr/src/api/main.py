"""
Lead Generation HTTP API

FastAPI-based REST API for the lead generation system.

Usage:
    uvicorn core_sdr.src.api.main:app --reload --port 8000
"""

import logging
import os
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]


# FastAPI app configuration
app = FastAPI(
    title="Lead Generation API",
    description="API for searching and collecting company data using natural language queries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
async def root():
    """API root endpoint."""
    return "Lead Generation API v1.0.0\nGo to /docs for API documentation"


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health status."""
    try:
        # Simple health check without orchestrator
        openai_key = os.getenv('OPENAI_API_KEY')
        coresignal_key = os.getenv('CORESIGNAL_API_KEY')
        
        status = "healthy" if openai_key and coresignal_key else "unhealthy"
        
        components = {
            "openai_api": "configured" if openai_key else "missing",
            "coresignal_api": "configured" if coresignal_key else "missing"
        }
        
        return HealthResponse(status=status, components=components)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(status="error", components={"error": str(e)})


# @app.get("/search")

# @app.get("/collect")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="info"
    )