"""
Lead Generation HTTP API

FastAPI-based REST API for the lead generation system.

Usage:
    uvicorn core_sdr.src.api.main:app --reload --port 8000
"""

import logging
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

from ..core import LeadGenerationOrchestrator, LeadGenerationError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class SearchRequestAPI(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language search query")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    timeout: int = Field(default=30, ge=5, le=300, description="Timeout in seconds")
    output_format: str = Field(default="json", regex="^(json|csv|summary)$", description="Output format")


class SearchResponseAPI(BaseModel):
    search_id: str
    query: Dict[str, Any]
    results: Dict[str, Any]
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    timestamp: float


class StatsResponse(BaseModel):
    total_searches: int
    cache_hits: int
    cache_misses: int
    total_credits_used: int
    total_processing_time: float
    api_usage: Dict[str, Any]


# Global orchestrator instance
orchestrator: Optional[LeadGenerationOrchestrator] = None


def get_orchestrator() -> LeadGenerationOrchestrator:
    """Dependency to get the orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="System not initialized")
    return orchestrator


def initialize_orchestrator():
    """Initialize the orchestrator with environment configuration."""
    global orchestrator
    
    api_key = os.getenv('CORESIGNAL_API_KEY')
    if not api_key:
        raise ValueError("CORESIGNAL_API_KEY environment variable not set")
    
    base_url = os.getenv('CORESIGNAL_BASE_URL', 'https://api.coresignal.com')
    mongo_uri = os.getenv('MONGODB_URI')
    cache_ttl_hours = int(os.getenv('CACHE_TTL_HOURS', '24'))
    
    orchestrator = LeadGenerationOrchestrator(
        coresignal_api_key=api_key,
        coresignal_base_url=base_url,
        config_dir="config",
        mongo_uri=mongo_uri,
        cache_ttl_hours=cache_ttl_hours
    )


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


@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    try:
        initialize_orchestrator()
        logger.info("Lead Generation API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {str(e)}")
        raise


@app.get("/", response_class=PlainTextResponse)
async def root():
    """API root endpoint."""
    return "Lead Generation API v1.0.0\nGo to /docs for API documentation"


@app.get("/health", response_model=HealthResponse)
async def health_check(orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)):
    """Check system health status."""
    try:
        health_status = orchestrator.health_check()
        return HealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/search", response_model=SearchResponseAPI)
async def search_companies(
    request: SearchRequestAPI,
    background_tasks: BackgroundTasks,
    orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)
):
    """
    Search for companies using natural language query.
    
    Returns results in the specified format (JSON by default).
    """
    try:
        # Convert API request to internal format
        request_data = request.dict()
        
        # Process search request
        response = orchestrator.process_search_request(request_data)
        
        # Log successful search in background
        background_tasks.add_task(
            log_search_request,
            request.query,
            response.metadata.get('credits_used', 0),
            response.metadata.get('processing_time', 0)
        )
        
        return SearchResponseAPI(**response.dict())
        
    except LeadGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/search/formatted")
async def search_companies_formatted(
    request: SearchRequestAPI,
    background_tasks: BackgroundTasks,
    orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)
):
    """
    Search for companies and return formatted results.
    
    Returns results in the requested format (JSON, CSV, or summary).
    """
    try:
        # Convert API request to internal format
        request_data = request.dict()
        
        # Process search request
        response = orchestrator.process_search_request(request_data)
        
        # Format response
        formatted_output = orchestrator.format_response(response, request.output_format)
        
        # Log successful search in background
        background_tasks.add_task(
            log_search_request,
            request.query,
            response.metadata.get('credits_used', 0),
            response.metadata.get('processing_time', 0)
        )
        
        # Return appropriate response type
        if request.output_format == "json":
            return response.dict()
        elif request.output_format == "csv":
            return PlainTextResponse(formatted_output, media_type="text/csv")
        else:  # summary
            return PlainTextResponse(formatted_output, media_type="text/plain")
        
    except LeadGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Formatted search request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/search/{search_id}")
async def get_search_result(search_id: str):
    """Get cached search result by ID (if implemented in cache)."""
    # This would require extending the cache system to store by search_id
    raise HTTPException(status_code=501, detail="Search result retrieval not implemented")


@app.post("/explain")
async def explain_query(
    query: Dict[str, str],
    orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)
):
    """
    Explain how a query would be parsed without executing it.
    
    Request body: {"query": "your search query"}
    """
    try:
        if "query" not in query:
            raise HTTPException(status_code=400, detail="Query field is required")
        
        explanation = orchestrator.explain_query(query["query"])
        return explanation
        
    except LeadGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query explanation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/stats", response_model=StatsResponse)
async def get_stats(orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)):
    """Get processing statistics."""
    try:
        stats = orchestrator.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@app.delete("/cache")
async def clear_cache(orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)):
    """Clear all cached data."""
    try:
        success = orchestrator.clear_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@app.get("/config/industries")
async def get_industries():
    """Get available industry categories."""
    try:
        import json
        with open("config/industries.json") as f:
            industries = json.load(f)
        return industries
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Industries configuration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load industries: {str(e)}")


@app.get("/config/technologies")
async def get_technologies():
    """Get available technology categories."""
    try:
        import json
        with open("config/technologies.json") as f:
            technologies = json.load(f)
        return technologies
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Technologies configuration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load technologies: {str(e)}")


@app.get("/config/locations")
async def get_locations():
    """Get available location mappings."""
    try:
        import json
        with open("config/locations.json") as f:
            locations = json.load(f)
        return locations
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Locations configuration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load locations: {str(e)}")


@app.get("/demo")
async def run_demo(orchestrator: LeadGenerationOrchestrator = Depends(get_orchestrator)):
    """Run a demo search to test the system."""
    demo_query = "AI startups in San Francisco with 10+ employees"
    
    try:
        request_data = {
            'query': demo_query,
            'max_results': 3,
            'timeout': 30,
            'output_format': 'json'
        }
        
        response = orchestrator.process_search_request(request_data)
        
        return {
            "demo_query": demo_query,
            "results": response.dict(),
            "message": "Demo completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


# Background task functions
async def log_search_request(query: str, credits_used: int, processing_time: float):
    """Log search request for analytics (background task)."""
    logger.info(f"Search completed: query='{query}', credits={credits_used}, time={processing_time:.2f}s")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return HTTPException(status_code=404, detail="Resource not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="info"
    )