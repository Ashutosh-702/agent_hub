from fastapi import APIRouter

from app.routing import CustomRequestRoute
from ai_agents.leadgen.schemas.ai_agents import ResponseData
from ai_agents.leadgen.views.ai_agents import ( 
    upload_leadgen_form, 
    update_campaign_status, 
    get_company_mapping_list, 
    fetch_companies_from_mappings,
    get_campaign_contact_data,
    fetch_campaign_by_status,
    get_linkedin_contact_details,
    lusha_get_contact_enrichment,
    lusha_contact_enrichment,
    save_prospects_data_to_mongo,
    count_company_mappings,
    apollo_contact_enrichment,
    get_campaigns,
    get_prospecting_campaigns,
    get_companies,
    get_company_details_with_contacts,
    get_campaign_details_with_companies,
    company_qualification_progress,
    create_campaign_from_prospecting_job,
    create_campaign_from_single_company,
    create_campaign_from_csv_import,
    manual_company_qualification,
    ai_company_qualification,
    get_apollo_contact_list,
    enrich_apollo_contact_list,
    update_apollo_contact_enrichment_status,
    get_campaign_contact_list,
    sync_to_hubspot,
    sync_from_hubspot_webhook,
    get_hubspot_synced_companies,
    save_contact_personalization,
    bulk_save_contact_personalization,
    get_enrollment_contacts,
    enroll_contacts_to_sequence,
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

router.add_api_route(
    "/fetch_and_claim_first_campaign",
    methods=["GET"],
    endpoint=fetch_campaign_by_status,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_linkedin_contact_details",
    methods=["GET"],
    endpoint=get_linkedin_contact_details,
    response_model=ResponseData,
)

router.add_api_route(
    "/lusha_get_contact_enrichment",
    methods=["POST"],
    endpoint=lusha_get_contact_enrichment,
    response_model=ResponseData,
)

router.add_api_route(
    "/lusha_contact_enrichment",
    methods=["POST"],
    endpoint=lusha_contact_enrichment,
    response_model=ResponseData,
)

router.add_api_route(
    "/save_prospects_data_to_mongo",
    methods=["POST"],
    endpoint=save_prospects_data_to_mongo,
    response_model=ResponseData,
)

router.add_api_route(
    "/count_company_mappings",
    methods=["GET"],
    endpoint=count_company_mappings,
    response_model=ResponseData,
)

router.add_api_route(
    "/apollo_contact_enrichment",
    methods=["POST"],
    endpoint=apollo_contact_enrichment,
    response_model=ResponseData,
)

router.add_api_route(
    "/campaigns",
    methods=["GET"],
    endpoint=get_campaigns,
    response_model=ResponseData,
)

router.add_api_route(
    "/prospecting_campaigns",
    methods=["GET"],
    endpoint=get_prospecting_campaigns,
    response_model=ResponseData,
)

router.add_api_route(
    "/companies",
    methods=["GET"],
    endpoint=get_companies,
    response_model=ResponseData,
)

router.add_api_route(
    "/company_details_with_contacts",
    methods=["GET"],
    endpoint=get_company_details_with_contacts,
    response_model=ResponseData,
)

router.add_api_route(
    "/campaign_details_with_companies",
    methods=["GET"],
    endpoint=get_campaign_details_with_companies,
    response_model=ResponseData,
)

router.add_api_route(
    "/company_qualification_progress",
    methods=["GET"],
    endpoint=company_qualification_progress,
    response_model=ResponseData,
)

router.add_api_route(
    "/create_campaign_from_prospecting_job",
    methods=["POST"],
    endpoint=create_campaign_from_prospecting_job,
    response_model=ResponseData,
)

router.add_api_route(
    "/create_campaign_from_single_company",
    methods=["POST"],
    endpoint=create_campaign_from_single_company,
    response_model=ResponseData,
)

router.add_api_route(
    "/create_campaign_from_csv_import",
    methods=["POST"],
    endpoint=create_campaign_from_csv_import,
    response_model=ResponseData,
)

router.add_api_route(
    "/manual_company_qualification",
    methods=["POST"],
    endpoint=manual_company_qualification,
    response_model=ResponseData,
)

router.add_api_route(
    "/ai_company_qualification",
    methods=["POST"],
    endpoint=ai_company_qualification,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_apollo_contact_list",
    methods=["POST"],
    endpoint=get_apollo_contact_list,
    response_model=ResponseData,
)

router.add_api_route(
    "/enrich_apollo_contact_list",
    methods=["POST"],
    endpoint=enrich_apollo_contact_list,
    response_model=ResponseData,
)

router.add_api_route(
    "/update_apollo_contact_enrichment_status",
    methods=["POST"],
    endpoint=update_apollo_contact_enrichment_status,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_campaign_contact_list",
    methods=["GET"],
    endpoint=get_campaign_contact_list,
    response_model=ResponseData,
)

router.add_api_route(
    "/sync_to_hubspot",
    methods=["POST"],
    endpoint=sync_to_hubspot,
    response_model=ResponseData,
)

router.add_api_route(
    "/sync_from_hubspot_webhook",
    methods=["POST"],
    endpoint=sync_from_hubspot_webhook,
    response_model=ResponseData,
)

router.add_api_route(
    "/get_hubspot_syncd_companies",
    methods=["GET"],
    endpoint=get_hubspot_synced_companies,
    response_model=ResponseData,
)

router.add_api_route(
    "/save_contact_personalization",
    methods=["POST"],
    endpoint=save_contact_personalization,
    response_model=ResponseData,
)

router.add_api_route(
    "/bulk_save_contact_personalization",
    methods=["POST"],
    endpoint=bulk_save_contact_personalization,
    response_model=ResponseData,
)

router.add_api_route(
    "/enrollment_contacts",
    methods=["GET"],
    endpoint=get_enrollment_contacts,
    response_model=ResponseData,
)

router.add_api_route(
    "/enroll_contacts_to_sequence",
    methods=["POST"],
    endpoint=enroll_contacts_to_sequence,
    response_model=ResponseData,
)