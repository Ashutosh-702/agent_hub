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
    get_companies
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
    "/companies",
    methods=["GET"],
    endpoint=get_companies,
    response_model=ResponseData,
)