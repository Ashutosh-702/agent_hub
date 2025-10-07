from fastapi import APIRouter
from app.routing import CustomRequestRoute
from ai_agents.leadgen.views.ai_agents import upload_leadgen_form, update_campaign_status, get_company_mapping_list
from ai_agents.leadgen.workflow.ai_agent import ResponseData

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
