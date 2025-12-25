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
    SaveProspectsDataToMongo,
    LushaGetContactEnrichment,
    CountCompanyMappings,
    ApolloContactEnrichment,
    Campaigns,
    Companies,
    CompanyContacts,
    CampaignDetailsWithCompanies,
    CampaignCompanyRun,
    CampaignContactRuns
)
from ai_agents.leadgen.services.ai_agents_service import (
    CampaignService,
    CompanyService,
    ContactService
)

from ai_agents.leadgen.helper.ai_agents_helper import LushaContactEnrichmentHelper, SaveProspectsDataToMongoHelper
from ai_agents.leadgen.helper.ai_agents_helper import ApolloContactEnrichmentHelper
from ai_agents.leadgen.helper.ai_agents_helper import CampaignsHelper
from ai_agents.leadgen.helper.ai_agents_helper import CompaniesHelper, CampaignCompanyRunHelper, CampaignContactRunsHelper
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
    config = response.get("config")

    if not config:
        response_data.data = {
            "message": "No campaign found with status",
        }
        return response_data.dict()
    
    response_data.data = config
    response_data.success = True
    
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


async def lusha_get_contact_enrichment(query_params: LushaGetContactEnrichment) -> Dict[str, Any]:
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


async def count_company_mappings(query_params: CountCompanyMappings = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CompanyService()

    response = await leadgen_form_upload_service.count_company_mappings(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def apollo_contact_enrichment(query_params: ApolloContactEnrichment = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    apollo_contact_enrichment_helper = ApolloContactEnrichmentHelper()

    response = await apollo_contact_enrichment_helper.apollo_contact_enrichment(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def get_campaigns(query_params: Campaigns = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaigns_helper = CampaignsHelper()

    response = await leadgen_campaigns_helper.get_campaigns(query_params)
    response_data.success = True
    response_data.data = response.get("campaigns")
    response_data.pagination = response.get("pagination_info")

    return response_data.dict()

async def get_companies(query_params: Companies = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_companies_helper = CompaniesHelper()

    response = await leadgen_companies_helper.get_companies_with_contact_counts(query_params)
    response_data.success = True
    response_data.data = response.get("companies")
    response_data.pagination = response.get("pagination_info")

    return response_data.dict()

async def get_company_details_with_contacts(query_params: CompanyContacts = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_companies_helper = CompaniesHelper()

    if not query_params.campaign_id and not query_params.company_id:
        response_data.data = {
            "message": "Campaign ID or company ID is required",
        }
        return response_data.dict()

    response = await leadgen_companies_helper.get_company_details_with_contacts(query_params)
    response_data.success = True
    response_data.data = response.get("company")
    response_data.data["contacts"] = response.get("contacts")
    response_data.pagination = response.get("pagination_info")

    return response_data.dict()

async def get_campaign_details_with_companies(query_params: CampaignDetailsWithCompanies = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaigns_helper = CampaignsHelper()

    response = await leadgen_campaigns_helper.get_campaign_details_with_companies(query_params)
    response_data.success = True
    response_data.data = response.get("campaign")
    response_data.data["companies"] = response.get("companies")
    response_data.pagination = response.get("pagination_info")
    return response_data.dict()

async def update_campaign_company_run(query_params: CampaignCompanyRun = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaign_company_run_helper = CampaignCompanyRunHelper()

    response = await leadgen_campaign_company_run_helper.update_campaign_company_run(query_params)
    response_data.success = True
    response_data.data = response
    return response_data.dict()

async def update_campaign_contact_runs(query_params: CampaignContactRuns = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaign_contact_runs_helper = CampaignContactRunsHelper()

    response = await leadgen_campaign_contact_runs_helper.update_campaign_contact_runs(query_params)
    response_data.success = True
    response_data.data = response
    return response_data.dict()