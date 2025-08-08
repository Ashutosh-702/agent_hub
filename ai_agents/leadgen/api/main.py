import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ai_agents.core_sdr.src.cli.main import process_company_search
from ai_agents.leadgen.workflow.prompt_reader import submit_company_data
from database.connection_manager import ConnectionManager
from config.loaded_config import loaded_config
from database.collection_index.campaign_index import campaign_mongodb_indexes
from database.collection_index.company_mapping_index import company_mapping_mongodb_indexes
from database.collection_index.companies_index import companies_mongodb_indexes
from typing import Dict, Any
from ai_agents.leadgen.workflow.health_service import HealthService
from fastapi.responses import ORJSONResponse

async def initialize_database():
    loaded_config.connection_manager = ConnectionManager(mongo_uri=loaded_config.mongo_uri, db_name="linkedin_db")
async def close_database():
    if loaded_config.connection_manager:
        await loaded_config.connection_manager.close_connections()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Lead Generation API server...")
    try:
        await initialize_database()
        print("✅ Database connected successfully")
        # await campaign_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        # await company_mapping_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        # await companies_mongodb_indexes(loaded_config.connection_manager.mongo_client)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    yield  # Server is running

    # Shutdown
    print("🔒 Shutting down Lead Generation API server...")
    try:
        await close_database()
        print("✅ Database disconnected successfully")
    except Exception as e:
        print(f"❌ Database disconnection failed: {e}")


load_dotenv()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str
    mode: str
class EnhanceRequest(BaseModel):
    query: str

class OrchestratedConfig(BaseModel):
    config: dict
class FormSubmission(BaseModel):
    web_prompt: str
    persona_prompt: str
    industry: str
    employee_count: str
    revenue_min: str
    revenue_max: str
    location_type: str
    location: str
    keywords: str
    categories: str
    currency: str
    hubspot_email: str
    product_name: str
    business_team: str
    user_email: str

@app.post("/api/v1/orchestrated/run")
async def run_orchestrated(config: OrchestratedConfig):
    pass
@app.post("/api/v1/sheets/upload_data_from_form")
async def upload_data_from_form(data: FormSubmission):
    try:
        db_data = {
            "web_prompt": data.web_prompt,
            "persona_prompt": data.persona_prompt,
            "industry": data.industry,
            "employee_count": data.employee_count,
            "revenue_min": data.revenue_min,
            "revenue_max": data.revenue_max,
            "location_type": data.location_type,
            "location": data.location,
            "keywords": data.keywords,
            "categories": data.categories,
            "currency": data.currency,
            "hubspot_email": data.hubspot_email,
            "product_name": data.product_name,
            "business_team": data.business_team,
            "user_email": data.user_email
        }

        response = await submit_company_data(db_data)
        if response.get("status") == "error":
            print(f"Error while submitting data to database: {response.get('message', 'Failed to submit data.')}")
            return {"status": "error", "message": response.get("message", "Failed to submit data.")}

        print(f"📤 Data submitted: {response}")
        return response

    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("api/v1/company_flow")
async def call_data_apis(config: Dict[str,Any]):
    company_data = await process_company_search(config)
    return company_data

@app.get("/api/v1/health_check")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    health_service = HealthService()
    health_status = await health_service.get_health_status()

    return health_status.model_dump()

@app.get("/api/v1/readiness_check")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    health_service = HealthService()
    readiness_status = await health_service.get_readiness_status()
    return readiness_status.model_dump()

# Kubernetes health check endpoints
@app.get("/_healthz")
async def healthz():
    return ORJSONResponse(status_code=200, content={"success": True})



@app.get("/_readyz")
async def k8s_readiness_check():
    return ORJSONResponse(status_code=200, content={"success": True})






def configure_static_serving_production(app: FastAPI):
    """
    Production-ready static file serving with proper error handling
    Uses separate mounting for static assets and catch-all for SPA routing
    """

    serve_static = os.getenv("SERVE_STATIC", "true").lower() == "true"
    static_path = os.getenv("STATIC_PATH","/Users/ahmedropewala/PycharmProjects/etc1/agent_hub/ai_agents/ui/dist")

    if not serve_static:
        print("Static file serving disabled (SERVE_STATIC=false)")
        return

    if not os.path.exists(static_path):
        print(f"WARNING: Static path does not exist: {static_path}")
        return

    index_path = Path(static_path) / "index.html"
    if not index_path.exists():
        print(f"WARNING: index.html not found in {static_path}")
        return

    print(f"✓ Serving static files from: {static_path}")

    static_assets_path = Path(static_path) / "static"
    if static_assets_path.exists():
        app.mount("/static", StaticFiles(directory=static_assets_path), name="static")
        print(f"✓ Mounted static assets from: {static_assets_path}")
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):

        if (full_path.startswith("api/") or
            full_path in ["_healthz", "_readyz", "env-config"]):
            raise HTTPException(status_code=404, detail="Not found")

        file_path = Path(static_path) / full_path

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(index_path, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        })

    print("✓ Static file serving configured successfully")


configure_static_serving_production(app)





