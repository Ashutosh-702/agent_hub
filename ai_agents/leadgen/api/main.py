import asyncio
import os
import json
import uuid
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ai_agents.core_sdr.src.cli.main import process_company_search
from ai_agents.leadgen.workflow.prompt_reader import submit_company_data
from database.collection_dao.campaigns import CampaignsDao
from database.connection_manager import ConnectionManager
from config.loaded_config import loaded_config
from typing import Dict, Any
from ai_agents.leadgen.workflow.health_service import HealthService
from fastapi.responses import ORJSONResponse
from ai_agents.ai_sdr.cli_app_orchestrated import run_orchestrated_workflow
from kafkautils.producer.event_helpers import emit_event_helper
from kafkautils.constants import LEADGEN_BATCH_PROCESSING, KAFKA_SERVICE_CONFIG_MAPPING, LeadgenServices

# Consumer imports
from kafkautils.consumer.consumer import start_eventbridge_consumer
from kafkautils.consumer.kafka_config import get_available_consumer_types
from eventbridge.health import _healthz, _readyz
import uvicorn


async def initialize_database():
    loaded_config.connection_manager = ConnectionManager(mongo_uri=loaded_config.mongo_uri, db_name="linkedin_sdr")
    # Initialize EventBridge producer in connection manager (pigeon pattern)
    await loaded_config.connection_manager.setup_eventbridge_producer()


async def close_database():
    if loaded_config.connection_manager:
        await loaded_config.connection_manager.close_connections()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Lead Generation API server...")
    try:
        await initialize_database()
        print("✅ Database and EventBridge connected successfully")
        # await campaign_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        # await company_mapping_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        # await companies_mongodb_indexes(loaded_config.connection_manager.mongo_client)
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

    yield  # Server is running

    # Shutdown
    print("🔒 Shutting down Lead Generation API server...")
    try:
        await close_database()
        print("✅ Database and EventBridge disconnected successfully")
    except Exception as e:
        print(f"❌ Shutdown failed: {e}")


load_dotenv()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://ai-sdr.tmsz0.de"],
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


@app.get("/env-config", tags=["Configuration"])
def get_env_config():
    """Return environment configuration as JavaScript"""
    config = {
        "AGENTHUB_MAIN_DOMAIN": os.getenv("AGENTHUB_MAIN_DOMAIN", "http://0.0.0.0:80"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "VERSION": "2.0.0",
        "FEATURES": {
            "document_management": True,
            "advanced_analytics": True,
            "export_functionality": True
        }
    }
    config_json = json.dumps(config)

    js_config = f"""
window.ENV_CONFIG = {config_json};
window.AGENTHUB_MAIN_DOMAIN = "{config['AGENTHUB_MAIN_DOMAIN']}";
window.ENVIRONMENT = "{config['ENVIRONMENT']}";
console.log('Environment configuration loaded:', window.ENV_CONFIG);
"""

    return Response(content=js_config, media_type="application/javascript")


@app.post("/api/v1/sheets/upload_data_from_form")
async def upload_data_from_form(data: FormSubmission):
    try:
        db_data = {
            "prompts": {"web": data.web_prompt,
                        "persona": data.persona_prompt},
            "segmentation": {
                "industry": sorted([industry.strip() for industry in data.industry.split(';') if industry]),
                "keywords": data.keywords,
                "categories": data.categories},
            "target": {"employee_count": sorted(
                [employee_count.strip() for employee_count in data.employee_count.split(',') if employee_count]),
                       "revenue_min": data.revenue_min,
                       "revenue_max": data.revenue_max,
                       "currency": data.currency,
                       "location": {
                           "type": data.location_type,
                           "names": sorted([name.strip() for name in data.location.split(',') if name])
                       }

                       },
            "ownership": {
                "hubspot_email": data.hubspot_email,
                "product_name": data.product_name,
                "business_team": data.business_team,
                "user_email": data.user_email
            },
            "lifecycle": {"status": "active"},
            "metadata": {}
        }

        response = await submit_company_data(db_data)
        if response.get("status") == "error":
            print(f"Error while submitting data to database: {response.get('message', 'Failed to submit data.')}")
            return {"status": "error", "message": response.get("message", "Failed to submit data.")}

        # Get campaign_id from database insert
        campaign_id = response.get("campaign_id")
        if not campaign_id:
            print("❌ Error: No campaign_id returned from database")
            return {"status": "error", "message": "Failed to get campaign_id from database"}

        # Send to EventBridge using pigeon pattern with emit_event_helper
        request_id = str(uuid.uuid4())

        # Send only campaign_id via Kafka (much cleaner!)
        if loaded_config.connection_manager.event_emitter:
            event = {
                "request_id": request_id,
                "action": "process_company_search",
                "campaign_id": campaign_id,  # Only send the ID, not all data
                "timestamp": asyncio.get_event_loop().time()
            }

            await emit_event_helper(
                event_emitter=loaded_config.connection_manager.event_emitter,
                topics=KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_BATCH_PROCESSING]["topics"],
                # Use actual topic from mapping
                partition_value=request_id,
                event=event,
                event_meta={"service": "leadgen", "campaign_id": campaign_id}
            )
            print(f"📤 Campaign ID {campaign_id} queued for processing: {request_id}")
        else:
            print("⚠️ EventBridge Producer not initialized, skipping background processing")

        return {
            "status": "success",
            "message": "Data uploaded and queued for processing via EventBridge",
            "request_id": request_id,
            "campaign_id": campaign_id
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("api/v1/company_flow")
async def call_data_apis(config: Dict[str, Any]):
    company_data = await process_company_search(config)
    return company_data


@app.post("/api/v1/ai-sdr")
async def run_ai_sdr():
    campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
    unprocessed_campaigns = await campaigns_dao.get_campaigns({'lifecycle.status': 'pending'})
    print(f"Unprocessed Campaigns: {len(unprocessed_campaigns)}")
    for campaign in unprocessed_campaigns[-1:]:
        campaign_id = campaign.get("_id", "")
        if not campaign_id:
            raise ValueError("No campaign Id")
        web_enricher_prompt = campaign.get("prompts", {}).get("web", "")
        persona_prompt = campaign.get("prompts", {}).get("persona", "")
        hubspot_owner_email = campaign.get("ownership", {}).get("hubspot_email", "")
        user_email = campaign.get("ownership", {}).get("user_email", "")
        product_name = campaign.get("ownership", {}).get("user_email", "")
        business_team = campaign.get("ownership", {}).get("business_team")
        ai_sdr_custom_config = {
            "HUBSPOT_OWNER_EMAIL": hubspot_owner_email,
            "USER_EMAIL": user_email,
            "PRODUCT_NAME": product_name,
            "BUSINESS_TEAM": business_team,
            "custom_prompts": {},
            "CAMPAIGN_ID": campaign_id,
            "DATA_SOURCE_TYPE": "mongo"
        }
        web_enrichment_prompt = f"""Relevance Criteria: Determine if the company fits either of the following:
        
            {web_enricher_prompt}

    Begin your research now using the web search tool to determine if companies match these criteria."""

        ai_sdr_custom_config["custom_prompts"]["web_enricher_user_prompt"] = web_enrichment_prompt
        ai_sdr_custom_config["custom_prompts"]["prospect_enricher_user_prompt"] = persona_prompt
        print(f"Running orchestrated workflow for Campaign Id: {campaign_id}")
        await run_orchestrated_workflow(ai_sdr_custom_config)

    return


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
    static_path = os.getenv("STATIC_PATH", "/Users/ahmedropewala/PycharmProjects/etc1/agent_hub/ai_agents/ui/dist")

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

    static_assets_path = Path(static_path) / "app/static"
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


# ==========================================
# CONSUMER SERVER FUNCTIONS
# ==========================================

async def consumer_main():
    """Async consumer startup (following LinkedIn SDR pattern)"""
    consumer_type = os.getenv("CONSUMER_TYPE", "")
    print("🤖 Starting Leadgen Kafka Consumer Server...")
    print(f"   📡 Consumer type: {consumer_type}")
    print("   📨 Listening for company search requests...")
    print("   🔄 Will process company searches asynchronously")
    print("   🌉 Using EventBridge abstraction")

    try:
        # Validate consumer type
        available_types = get_available_consumer_types()
        if consumer_type not in available_types:
            print(f"❌ Unknown consumer type: {consumer_type}")
            print(f"   Available consumer types: {available_types}")
            print("   Set CONSUMER_TYPE environment variable")
            print("   Examples:")
            for consumer in available_types:
                print(f"     CONSUMER_TYPE={consumer}")
            sys.exit(1)

        print(f"   ⚙️  Service: leadgen")
        print(f"   📂 Topic: leadgen-batch-processing")

        # Start health check endpoints
        print("   ❤️ Starting health check endpoints...")
        asyncio.create_task(_healthz())
        asyncio.create_task(_readyz())

        # Start EventBridge consumer
        print("   🚀 Starting EventBridge consumer...")
        await start_eventbridge_consumer(consumer_type)

    except KeyError as e:
        available_types = get_available_consumer_types()
        print(f"❌ Configuration error: {e}")
        print(f"   Available consumer types: {available_types}")
        print("   Set CONSUMER_TYPE environment variable")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Consumer startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ==========================================
# MAIN ENTRY POINT
# ==========================================

def server_main():
    """Main entry point for API server only"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "80"))
    workers = int(os.getenv("API_WORKERS", "1"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"

    print("=" * 60)
    print("🚀 LEADGEN API SERVER")
    print("=" * 60)
    print(f"🌐 Starting API server on {host}:{port}")
    print(f"👥 Workers: {workers}")
    print(f"🔄 Reload: {reload}")

    uvicorn.run(
        "ai_agents.leadgen.api.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload
    )
