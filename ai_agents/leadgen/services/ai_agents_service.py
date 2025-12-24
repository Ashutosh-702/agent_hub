"""AI Agents Service"""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from structlog.contextvars import bind_contextvars

from config.loaded_config import loaded_config
from config.logging import logger
from global_utils.exceptions import ApiException
from ai_agents.leadgen.schemas.ai_agents import (
    CampaignStatusUpdate,
    CompanyMappingList, 
    CompanyListWithDetails, 
    FormSubmission,
    CampaignContactData,
    CountCompanyMappings,
    Campaigns,
    Companies,
    CompanyContacts
)
from ai_agents.leadgen.schemas.contact_models import ContactCampaignMapping, ContactDocument
from ai_agents.leadgen.utils import serialize_objectid
from database.collection_dao.campaigns import CampaignsDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.campaign_contact_runs import CampaignContactRunsDao
from kafkautils.producer.event_helpers import emit_event_helper
from kafkautils.constants import(
    LEADGEN_BATCH_PROCESSING, 
    KAFKA_SERVICE_CONFIG_MAPPING, 
    LeadgenServices
)
from integrations.lusha.lusha_api import LushaAPIClient


class CampaignService:
    def __init__(self):
        self.campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_BATCH_PROCESSING]

    async def upload_leadgen_form(self, form_submission: FormSubmission) -> Dict[str, str]:

        db_data = self._transform_form_to_db_data(form_submission)
        bind_contextvars(
            operation="upload_leadgen_form",
            component="ai_agents_service", 
            event_type="upload_leadgen_form"
        )
        campaign_id = await self.campaign_dao.create_campaign(db_data)

        if not campaign_id:
            raise ApiException("campaign_id not generated")

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_company_search",
            "campaign_id": str(campaign_id), 
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": str(campaign_id)}
        )

        logger.info(f"📤 Campaign ID {str(campaign_id)} queued for processing: {request_id}")

        return {
            "request_id": request_id,
            "campaign_id": str(campaign_id)
        }

    def _transform_form_to_db_data(self, form_submission: FormSubmission) -> Dict[str, Any]:
        """Transform form submission to database format"""
        return {
            "prompts": {
                "web": form_submission.web_prompt,
                "persona": form_submission.persona_prompt
            },
            "segmentation": {
                "industry": self._parse_list(form_submission.industry, ';'),
                "keywords": form_submission.keywords,
                "categories": form_submission.categories
            },
            "target": {
                "employee_count": self._parse_list(form_submission.employee_count, ','),
                "revenue_min": form_submission.revenue_min,
                "revenue_max": form_submission.revenue_max,
                "currency": form_submission.currency,
                "location": {
                    "type": form_submission.location_type,
                    "names": self._parse_list(form_submission.location, ',')
                }
            },
            "ownership": {
                "hubspot_email": form_submission.hubspot_email,
                "product_name": form_submission.product_name,
                "business_team": form_submission.business_team,
                "user_email": form_submission.user_email
            },
            "lifecycle": {"status": "active"},
            "shortlisting_approach": form_submission.shortlisting_approach,
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }

    def _parse_list(self, value: str, delimiter: str) -> List[str]:
        """Parse string to list with validation"""
        if not value:
            return []
            
        return sorted([item.strip() for item in value.split(delimiter) if item.strip()])

    async def update_campaign_status(self, campaign_status_update: CampaignStatusUpdate):
        response = await self.campaign_dao.update_campaign_status(campaign_status_update.campaign_id, campaign_status_update.status)

        if not response:
            raise ApiException(f"No campaign found with campaign id {campaign_status_update.campaign_id} to update status or it's already updated")

        return response
    
    async def fetch_campaign_by_status(self, status: str):
        campaign = await self.campaign_dao.get_campaign_by_status(status)

        if not campaign:
            return {"config": {}}

        campaign_id = campaign.get("_id")
        ownership = campaign.get("ownership", {})
        prompts = campaign.get("prompts", {})
        ai_sdr_custom_config = {
            "HUBSPOT_OWNER_EMAIL": ownership.get("hubspot_email", ""),
            "USER_EMAIL": ownership.get("user_email", ""),
            "PRODUCT_NAME": ownership.get("product_name", ""),
            "BUSINESS_TEAM": ownership.get("business_team", ""),
            "custom_prompts": {},
            "CAMPAIGN_ID": str(campaign_id),
            "DATA_SOURCE_TYPE": "mongo",
            "target_executives": prompts.get("persona", "")
        }
        web_enrichment_prompt = (
            "Relevance Criteria: Determine if the company fits either of the following:\n\n"
            f"{prompts.get('web', '')}\n\n"
            "Begin your research now using the web search tool to determine if companies "
            "match these criteria."
        )
        ai_sdr_custom_config["custom_prompts"]["web_enricher_user_prompt"] = web_enrichment_prompt
        ai_sdr_custom_config["custom_prompts"]["prospect_enricher_target_executives"] = prompts.get("persona", "")

        return {"config": ai_sdr_custom_config}

    async def get_campaigns(self, query_params: Campaigns):
        query = {}
        if query_params.campaign_id:
            query["_id"] = query_params.campaign_id
        if query_params.user_email:
            query["ownership.user_email"] = query_params.user_email
        if query_params.product_name:
            query["ownership.product_name"] = query_params.product_name
        if query_params.status:
            query["lifecycle.status"] = query_params.status
        campaigns, pagination_info = await self.campaign_dao.get_campaigns_paginated(query, query_params.page, query_params.limit)
        serialized_campaigns = serialize_objectid(campaigns)
        return {"campaigns": serialized_campaigns, "pagination_info": pagination_info}

    async def get_campaign_details(self, campaign_id: str):
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException(f"Campaign not found with id {campaign_id}")
        serialized_campaign = serialize_objectid(campaign)
        return {"campaign": serialized_campaign}


class CompanyService:
    def __init__(self):
        self.campaign_company_run_dao = CampaignCompanyRunsDao(
            loaded_config.connection_manager.mongo_client)
        self.companies_dao = CompaniesDao(
            loaded_config.connection_manager.mongo_client)

    async def get_company_mapping_list(self, query_params: CompanyMappingList):
        projection = {
            "_id": 0,           
            "company_status": 0, 
            "metadata": 0
        }
        query = {
            "campaign_id": query_params.campaign_id, 
            "is_relevant": True
        }
        response, pagination_info = await self.campaign_company_run_dao.get_campaign_company_runs_paginated(
            query=query,
            page=query_params.page,
            limit=query_params.limit,
            projection=projection
        )

        if not response:
            raise ApiException(
                f"No company mappings found for campaign_id {query_params.campaign_id}")

        serialized_response = serialize_objectid(response)
        serialized_pagination = serialize_objectid(pagination_info)

        return {"company_map_list": serialized_response, "pagination_info": serialized_pagination}

    async def fetch_companies_from_mappings(self, query_params: CompanyListWithDetails):
        mapping_docs = await self.campaign_company_run_dao.get_campaign_company_runs({"campaign_id": query_params.campaign_id})

        if not mapping_docs:
            raise ApiException(
                f"No company mappings found for campaign_id {query_params.campaign_id}")

        data_rows = []

        for mapping in mapping_docs:
            company_id = mapping.get("company_id")

            if not company_id:
                logger.info(f"Company id is not found for campaign {query_params.campaign_id}")
                continue

            company_doc = await self.companies_dao.get_company(company_id)

            if not company_doc or not company_doc.get("identifiers", {}).get("name"):
                logger.info(f"Company data is not found for campaign {query_params.campaign_id}")
                continue

            name = company_doc.get("identifiers", {}).get("name")
            profile = company_doc.get("profile") or {}
            location = company_doc.get("location") or {}
            data_rows.append({
                "company_name": name,
                "company_id": str(company_id),
                "industry": profile.get("industry"),
                "company_size": profile.get("employeeCount"),
                "location": location.get("name"),
            })

        if not data_rows:
            raise ApiException(
                f"No valid companies found in Mongo for campaign {query_params.campaign_id}")

        return {"company_details": data_rows}
    
    async def count_company_mappings(self, query_params: CountCompanyMappings):
        query = {
            "campaign_id": query_params.campaign_id, 
            "is_relevant": True
        }
        count = await self.campaign_company_run_dao.get_campaign_company_runs_count(query)
        
        return {"count": count}

    async def get_companies(self, query_params: Companies):
        query = {}
        if query_params.name:
            query["identifiers.name"] = {
                "$regex": query_params.name,
                "$options": "i"
            }
        if query_params.domain:
            query["identifiers.domain"] = query_params.domain
        companies, pagination_info = await self.companies_dao.get_companies_paginated(query, query_params.page, query_params.limit)
        serialized_companies = serialize_objectid(companies)
        return {"companies": serialized_companies, "pagination_info": pagination_info}


    async def get_company_details(self, company_id: str):
        company = await self.companies_dao.get_company(company_id)
        if not company:
            raise ApiException(f"Company not found with id {company_id}")
        serialized_company = serialize_objectid(company)
        return {"company": serialized_company}


class ContactService:
    def __init__(self):
        self.campaign_contact_run_dao = CampaignContactRunsDao(
            loaded_config.connection_manager.mongo_client)
        self.contacts_dao = ContactsDao(
            loaded_config.connection_manager.mongo_client)
        self.lusha_api_client = LushaAPIClient()

    async def get_campaign_contact_data(self, query_params: CampaignContactData):
        filter_query = {"campaign_id": query_params.campaign_id}

        if query_params.company_id:
            filter_query["company_id"] = query_params.company_id

        campaign_contact_runs_projection = {
            "campaign_id": 1,
            "company_id": 1,
            "contact_id": 1,
            "_id": 0
        }

        contacts_projection = {
            "contact_data": 1,
            "linkedin_data": 1,
            "_id": 0
        }

        response, pagination_info = await self.campaign_contact_run_dao.get_campaign_contact_runs_paginated(
            filter_query, query_params.page,
            query_params.limit, sort_by=["company_id"],
            projection=campaign_contact_runs_projection
        )

        for contact in response:
            contact_id = contact.get("contact_id")
            contact_doc = await self.contacts_dao.get_contact(
                contact_id,
                projection=contacts_projection
            )

            if not contact_doc:
                logger.info(f"Contact data is not found for contact id {contact_id}")
                continue

            contact["contact_data"] = contact_doc.get("contact_data")
            contact["linkedin_data"] = contact_doc.get("linkedin_data")

        serialized_response = serialize_objectid(response)

        return {"campaign_contact_data": serialized_response, "pagination_info": pagination_info}

    async def get_linkedin_contact_details(self, linkedin_url: str):
        response = await self.lusha_api_client.lusha_get_linkedin_contact_details(linkedin_url)

        return response

    async def create_contact(self, contact_doc: ContactDocument, campaign_id: str):
        contact_id = await self.contacts_dao.create_contact(contact_doc.dict())
        contact_data =  {
            "campaign_id": campaign_id,
            "company_id": contact_doc.company_id,
            "contact_id": contact_id,
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        }
        await self.insert_campaign_contact_run(contact_data)

    async def insert_campaign_contact_run(self, campaign_contact_run_doc: ContactCampaignMapping):
        contact_data = {
            "campaign_id": campaign_contact_run_doc.get("campaign_id"),
            "company_id": campaign_contact_run_doc.get("company_id"),
            "contact_id": campaign_contact_run_doc.get("contact_id"),
            
        }
        check_campaign_contact_run = await self.campaign_contact_run_dao.get_campaign_contact_runs(contact_data)
        contact_data["metadata"] = campaign_contact_run_doc.get("metadata")
        
        if check_campaign_contact_run:
            return
        
        await self.campaign_contact_run_dao.create_campaign_contact_run(contact_data) 

    async def get_company_contacts(self, query_params: CompanyContacts):
        query = {"company_id": query_params.company_id}
        contacts, pagination_info = await self.contacts_dao.get_paginated_contacts(query, query_params.page, query_params.limit)
        serialized_contacts = serialize_objectid(contacts)
        return {"company_contacts": serialized_contacts, "pagination_info": pagination_info}
               