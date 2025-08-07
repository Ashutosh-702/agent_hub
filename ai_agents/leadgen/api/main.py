from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai_agents.core_sdr.src.cli.main import process_company_search
from ai_agents.leadgen.workflow.prompt_reader import submit_company_data
from database.connection_manager import ConnectionManager
from config.loaded_config import loaded_config
from database.collection_index.campaign_index import campaign_mongodb_indexes
from database.collection_index.company_mapping_index import company_mapping_mongodb_indexes
from database.collection_index.companies_index import companies_mongodb_indexes
from typing import Dict, Any
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
        await campaign_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        await company_mapping_mongodb_indexes(loaded_config.connection_manager.mongo_client)
        await companies_mongodb_indexes(loaded_config.connection_manager.mongo_client)
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
    allow_origins=["http://localhost:5173"],
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
            print(f"Error while submitting data to Google Sheets: {response.get('message', 'Failed to submit data to Google Sheets.')}")
            return {"status": "error", "message": response.get("message", "Failed to submit data to Google Sheets.")}

        print(f"📤 Data submitted to Google Sheets: {response}")
        return response

    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("api/v1/company_flow")
async def call_data_apis(config: Dict[str,Any]):
    company_data = await process_company_search(config)
    return company_data


