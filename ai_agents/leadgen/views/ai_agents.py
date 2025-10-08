from fastapi import Request, Body
from typing import Dict, Any
from ai_agents.leadgen.schemas.ai_agents import FormSubmission, CampaignStatusUpdate
from ai_agents.leadgen.workflow.ai_agent import ResponseData
from ai_agents.leadgen.services.ai_agents_service import CampaignService


async def upload_leadgen_form(request: Request,
    request_data: FormSubmission = Body(),
) -> Dict[str, Any]:

    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CampaignService()

    response = await leadgen_form_upload_service.upload_leadgen_form(request_data)
    response_data.success = True
    response_data.data = {
        "message": "Data uploaded and queued for processing via EventBridge",
        "campaign_id": response.get("campaign_id")
    }
       
    return response_data.dict()


async def update_campaign_status(campaign_status_update: CampaignStatusUpdate) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CampaignService()
    
    await leadgen_form_upload_service.update_campaign_status(campaign_status_update)
    response_data.success = True
    response_data.data = {
        "message": "Campaign status updated",   
        "campaign_id": campaign_status_update.campaign_id
    }
    
    return response_data.dict()
