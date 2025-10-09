from fastapi import APIRouter

from app.routing import CustomRequestRoute
from ai_agents.leadgen.schemas.ai_agents import ResponseData
from ai_agents.leadgen.views.ai_agents import ( 
    upload_leadgen_form, 
    update_campaign_status, 
    get_company_mapping_list, 
    fetch_companies_from_mappings,
    get_campaign_contact_data
)

router = APIRouter(tags=["AI Agents"], route_class=CustomRequestRoute)

router.add_api_route(
    "/sheets/upload_data_from_form",
    methods=["POST"],
    endpoint=upload_leadgen_form,
    response_model=ResponseData,
)

router.add_api_route(
    "/update_campaign_status",
    methods=["POST"],
    endpoint=update_campaign_status,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_company_mapping_list",
    methods=["GET"],
    endpoint=get_company_mapping_list,
    response_model=ResponseData,
)

router.add_api_route(
    "/fetch_companies",
    methods=["GET"],
    endpoint=fetch_companies_from_mappings,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_campaign_contact_data",
    methods=["GET"],
    endpoint=get_campaign_contact_data,
    response_model=ResponseData,
)