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
    CreateCampaignFromProspectingJob,
    CreateCampaignFromSingleCompany,
    CreateCampaignFromCSVImport,
    ManualCompanyQualification,
    AiCompanyQualification,
    AiContactQualification,
    ApolloContactList,
    UpdateApolloContactEnrichmentStatus,
    GetCampaignContactList,
    CompanyQualificationProgress,
    SyncToHubspot,
    SaveContactPersonalization,
    BulkSaveContactPersonalization,
    GetEnrollmentContacts,
    EnrollContactsToSequence
)
from ai_agents.leadgen.services.ai_agents_service import (
    CampaignService,
    CompanyService,
    ContactService
)

from ai_agents.leadgen.helper.ai_agents_helper import LushaContactEnrichmentHelper, SaveProspectsDataToMongoHelper
from ai_agents.leadgen.helper.ai_agents_helper import ApolloContactEnrichmentHelper
from ai_agents.leadgen.helper.ai_agents_helper import CampaignsHelper
from ai_agents.leadgen.helper.ai_agents_helper import CompaniesHelper
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


async def get_prospecting_campaigns(
    page: int = 1,
    limit: int = 10,
    prospecting_cycle_status: str = None
) -> Dict[str, Any]:
    """
    Get campaigns filtered by prospecting_cycle.status.
    Only returns campaigns that have prospecting_cycle.status defined.
    
    Query params:
    - page: Page number (default 1)
    - limit: Page size (default 10)
    - prospecting_cycle_status: Filter by specific status (e.g., 'prospecting', 'company_qualification', 'contact_qualification', 'contact_enriched')
    """
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaigns_helper = CampaignsHelper()

    response = await leadgen_campaigns_helper.get_prospecting_campaigns(page, limit, prospecting_cycle_status)
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

async def company_qualification_progress(query_params: CompanyQualificationProgress = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_campaigns_helper = CampaignsHelper()

    response = await leadgen_campaigns_helper.get_company_qualification_progress(query_params.campaign_id)
    response_data.success = True
    response_data.data = response
    return response_data.dict()

async def create_campaign_from_prospecting_job(query_params: CreateCampaignFromProspectingJob = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    leadgen_form_upload_service = CampaignService()

    response = await leadgen_form_upload_service.create_campaign_from_prospecting_job(query_params)
    response_data.success = True
    response_data.data = {
        "message": "Data uploaded and queued for processing via EventBridge",
        "campaign_id": response.get("campaign_id")
    }

    return response_data.dict()


async def create_campaign_from_single_company(query_params: CreateCampaignFromSingleCompany = Body()) -> Dict[str, Any]:
    """Create a campaign from a single company URL/domain and queue for Apollo search."""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_service = CampaignService()

    response = await campaign_service.create_campaign_from_single_company(query_params)
    response_data.success = True
    response_data.data = {
        "message": "Single company campaign created and queued for Apollo domain search",
        "campaign_id": response.get("campaign_id"),
        "request_id": response.get("request_id")
    }

    return response_data.dict()


async def create_campaign_from_csv_import(query_params: CreateCampaignFromCSVImport = Body()) -> Dict[str, Any]:
    """Create a campaign from CSV import with company domains and queue for Apollo search."""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_service = CampaignService()

    response = await campaign_service.create_campaign_from_csv_import(query_params)
    response_data.success = True
    response_data.data = {
        "message": "CSV import campaign created and queued for processing",
        "campaign_id": response.get("campaign_id"),
        "request_id": response.get("request_id"),
        "existing_companies": response.get("existing_companies"),
        "new_companies": response.get("new_companies"),
        "total_companies": response.get("total_companies")
    }

    return response_data.dict()


async def manual_company_qualification(query_params: ManualCompanyQualification = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.manual_company_qualification(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def ai_company_qualification(query_params: AiCompanyQualification = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.ai_company_qualification(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def ai_contact_qualification(query_params: AiContactQualification = Body()) -> Dict[str, Any]:
    """Queue AI contact qualification job via Kafka."""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.ai_contact_qualification(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def contact_qualification_progress(campaign_id: str) -> Dict[str, Any]:
    """Get progress of AI contact qualification job."""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_contact_qualification_progress(campaign_id)
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def get_apollo_contact_list(query_params: ApolloContactList = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_apollo_contact_list(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def enrich_apollo_contact_list(query_params: ApolloContactList = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_apollo_contact_list(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def update_apollo_contact_enrichment_status(
    contact_ids: list[str] = Body(default_factory=list),
    query_params: UpdateApolloContactEnrichmentStatus = Depends(),
) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    # Support passing contact_ids via JSON body (as per curl) in addition to query params.
    if contact_ids:
        query_params.contact_ids = contact_ids

    response = await campaign_helper.update_contact_relevance(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def get_campaign_contact_list(query_params: GetCampaignContactList = Depends()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_campaign_contact_list(query_params)
    response_data.success = True
    response_data.data = response.get("campaign")
    response_data.data["contacts"] = response.get("contacts")
    response_data.pagination = response.get("pagination_info")

    return response_data.dict()

async def sync_to_hubspot(query_params: SyncToHubspot = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.sync_to_hubspot(query_params.campaign_id)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def sync_from_hubspot_webhook(query_params: Dict[str, Any] = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.sync_from_hubspot_webhook(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def get_hubspot_synced_companies(campaign_id: str) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_hubspot_synced_companies(campaign_id)
    response_data.success = True
    response_data.data = response.get("campaign")
    response_data.data["synced_hubspot_companies_count"] = response.get("synced_hubspot_companies_count")
    response_data.data["total_hubspot_companies_count"] = response.get("total_hubspot_companies_count")
    response_data.data["campaign_id"] = response.get("campaign_id")

    return response_data.dict()


async def save_contact_personalization(query_params: SaveContactPersonalization) -> Dict[str, Any]:
    """Save personalization data for a single contact"""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.save_contact_personalization(
        campaign_id=query_params.campaign_id,
        contact_id=query_params.contact_id,
        email_id=query_params.email_id,
        personalized_message=query_params.personalized_message,
        ai_generated_deck=query_params.ai_generated_deck
    )
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def bulk_save_contact_personalization(query_params: BulkSaveContactPersonalization) -> Dict[str, Any]:
    """Save personalization data for multiple contacts"""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.bulk_save_contact_personalization(
        campaign_id=query_params.campaign_id,
        personalizations=query_params.personalizations
    )
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def get_enrollment_contacts(campaign_id: str, page: int = 1, limit: int = 100) -> Dict[str, Any]:
    """Get full contact details with all metadata for sequence enrollment"""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.get_enrollment_contacts(
        campaign_id=campaign_id,
        page=page,
        limit=limit
    )
    response_data.success = True
    response_data.data = response
    response_data.pagination = response.get("pagination")

    return response_data.dict()


async def enroll_contacts_to_sequence(query_params: EnrollContactsToSequence) -> Dict[str, Any]:
    """Enroll contacts to a Lemlist sequence"""
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.enroll_contacts_to_sequence(
        campaign_id=query_params.campaign_id,
        sequence_id=query_params.sequence_id,
        sequence_name=query_params.sequence_name,
        contact_ids=query_params.contact_ids
    )
    response_data.success = True
    response_data.data = response

    return response_data.dict()


async def get_lemlist_campaigns() -> Dict[str, Any]:
    """Fetch all available Lemlist campaigns/sequences for enrollment"""
    from integrations.lemlist.lemlist_inbox_client import LemlistInboxClient
    
    response_data = ResponseData.model_construct(data={}, success=False)
    
    try:
        lemlist_client = LemlistInboxClient()
        campaigns = await lemlist_client.get_campaigns()
        
        # Transform to a consistent format for the frontend
        formatted_campaigns = []
        for campaign in campaigns:
            formatted_campaigns.append({
                "id": campaign.get("_id"),
                "name": campaign.get("name", "Unnamed Campaign"),
                "labels": campaign.get("labels", []),
                "status": campaign.get("status", "unknown"),
                # Add computed stats if available
                "steps": len(campaign.get("sequences", [])) if campaign.get("sequences") else None,
                "created_at": campaign.get("createdAt"),
                "updated_at": campaign.get("updatedAt"),
            })
        
        response_data.success = True
        response_data.data = {
            "campaigns": formatted_campaigns,
            "total": len(formatted_campaigns)
        }
    except Exception as e:
        response_data.success = False
        response_data.errors = [str(e)]

    return response_data.dict()

async def webhook_from_deepsearch_research(query_params: Dict[str, Any] = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.webhook_from_deepsearch_research(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def webhook_for_legal_name_and_other_entities(query_params: Dict[str, Any] = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.webhook_for_legal_name_and_other_entities(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()

async def webhook_for_personalization(query_params: Dict[str, Any] = Body()) -> Dict[str, Any]:
    response_data = ResponseData.model_construct(data={}, success=False)
    campaign_helper = CampaignsHelper()

    response = await campaign_helper.webhook_for_personalization(query_params)
    response_data.success = True
    response_data.data = response

    return response_data.dict()