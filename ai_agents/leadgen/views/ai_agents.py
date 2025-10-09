from fastapi import Request, Body
from typing import Dict, Any
from ai_agents.leadgen.schemas.ai_agents import FormSubmission
from ai_agents.leadgen.workflow.ai_agent import ResponseData
from ai_agents.leadgen.api.main import upload_data_from_form


async def upload_leadgen_form(request: Request,
    request_data: FormSubmission = Body(),
) -> Dict[str, Any]:
   
    response_data = ResponseData.model_construct(data={}, success=False)

    response_data.success = True
    return response_data.dict()
