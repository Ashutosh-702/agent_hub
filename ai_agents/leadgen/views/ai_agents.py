from fastapi import Request, Body, Depends
from typing import Dict, Any

from ai_agents.leadgen.schemas.ai_agents import (
    CampaignStatusUpdate,
    ResponseData,
    FormSubmission,
    CompanyMappingList,
    CompanyListWithDetails,
    CampaignContactData,
    LinkedinContactDetails,
    LushaContactEnrichment,
    SaveProspectsDataToMongo
)
from ai_agents.leadgen.services.ai_agents_service import (
    CampaignService,
    CompanyService,
    ContactService
)

from ai_agents.leadgen.helper.ai_agents_helper import LushaContactEnrichmentHelper, SaveProspectsDataToMongoHelper

async def upload_leadgen_form(
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


async def get_company_mapping_list(query_params: CompanyMappingList = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CompanyService()

    response = await leadgen_form_upload_service.get_company_mapping_list(query_params)
    response_data.success = True
    response_data.data = response.get("company_map_list")
    response_data.pagination = response.get("pagination_info")
    return response_data.dict()


async def fetch_companies_from_mappings(query_params: CompanyListWithDetails = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CompanyService()

    response = await leadgen_form_upload_service.fetch_companies_from_mappings(query_params)
    response_data.success = True
    response_data.data = response.get("company_details")
    return response_data.dict()


async def get_campaign_contact_data(query_params: CampaignContactData = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = ContactService()

    response = await leadgen_form_upload_service.get_campaign_contact_data(query_params)
    response_data.success = True
    response_data.data = response.get("campaign_contact_data")
    response_data.pagination = response.get("pagination_info")
    return response_data.dict()


async def fetch_campaign_by_status(status: str) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CampaignService()

    response = await leadgen_form_upload_service.fetch_campaign_by_status(status)
    response_data.success = True
    response_data.data = response.get("config")
    return response_data.dict()


async def get_linkedin_contact_details(query_params: LinkedinContactDetails = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = ContactService()

    response = await leadgen_form_upload_service.get_linkedin_contact_details(query_params.linkedin_url)
    contact_data = response.get("contact", {})

    if "error" not in contact_data:
        response_data.success = True
    response_data.data = contact_data
    return response_data.dict()


async def lusha_get_contact_enrichment(query_params: LushaContactEnrichment) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    lusha_contact_enrichment_helper = LushaContactEnrichmentHelper()

    response = await lusha_contact_enrichment_helper.lusha_get_contact_enrichment(query_params)
    response_data.success = True
    response_data.data = response
    return response_data.dict()


async def lusha_contact_enrichment(query_params: LushaContactEnrichment) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    lusha_contact_enrichment_helper = LushaContactEnrichmentHelper()

    response = await lusha_contact_enrichment_helper.lusha_contact_enrichment(query_params)
    response_data.success = True
    response_data.data = response
    return response_data.dict()


async def save_prospects_data_to_mongo(query_params: SaveProspectsDataToMongo) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    save_prospects_data_to_mongo_helper = SaveProspectsDataToMongoHelper()

    response = await save_prospects_data_to_mongo_helper.save_prospects_data_to_mongo(query_params)
    response_data.success = True
    response_data.data = response
    return response_data.dict()