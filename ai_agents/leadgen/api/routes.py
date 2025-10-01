from fastapi import APIRouter, Depends

from app.routing import CustomRequestRoute
from ai_agents.leadgen.views.ai_agents import upload_leadgen_form
from ai_agents.leadgen.workflow.ai_agent import ResponseData

router = APIRouter(tags=["AI Agents"], route_class=CustomRequestRoute)

router.add_api_route(
    "/sheets/upload_data_from_form",
    methods=["POST"],
    endpoint=upload_leadgen_form,
    response_model=ResponseData,
)   
