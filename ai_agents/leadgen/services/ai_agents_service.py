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
    LEADGEN_PROSPECTING_JOB_PROCESSING,
    LEADGEN_SINGLE_COMPANY_PROCESSING,
    KAFKA_SERVICE_CONFIG_MAPPING, 
    LeadgenServices
)
from integrations.lusha.lusha_api import LushaAPIClient
from ai_agents.leadgen.schemas.ai_agents import CreateCampaignFromProspectingJob, CreateCampaignFromSingleCompany


class CampaignService:
    def __init__(self):
        self.campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_BATCH_PROCESSING]
        self.prospecting_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_PROSPECTING_JOB_PROCESSING]
        self.single_company_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_SINGLE_COMPANY_PROCESSING]

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

    async def create_campaign_from_prospecting_job(self, query_params: CreateCampaignFromProspectingJob) -> Dict[str, Any]:
        db_data = self._transform_create_campaign_from_prospecting_job_to_db_data(query_params)
        campaign_id = await self.campaign_dao.create_campaign(db_data)

        if not campaign_id:
            raise ApiException("campaign_id not generated")

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_prospecting_job",
            "campaign_id": str(campaign_id), 
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.prospecting_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": str(campaign_id)}
        )

        logger.info(f"📤 Campaign ID {str(campaign_id)} queued for processing: {request_id}")

        return {
            "request_id": request_id,
            "campaign_id": str(campaign_id)
        }

    async def create_campaign_from_single_company(self, query_params: CreateCampaignFromSingleCompany) -> Dict[str, Any]:
        """
        Create a campaign from a single company URL/domain.
        - If company already exists in DB (by identifiers.source_domain): use existing, skip Kafka
        - Otherwise: create placeholder, emit Kafka for Apollo enrichment
        """
        # Initialize DAOs
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        
        # Check if company already exists by domain
        existing_company = await companies_dao.get_company_by_source_domain(query_params.company_domain)
        
        if existing_company:
            # Company already exists - skip Kafka, create campaign and mapper directly
            logger.info(f"✅ Company already exists for domain {query_params.company_domain}, skipping Apollo search")
            
            company_id = str(existing_company.get("_id"))
            company_name = existing_company.get("identifiers", {}).get("name", "")
            
            # Create campaign with completed status
            db_data = self._transform_single_company_to_db_data(query_params)
            db_data["single_company"]["status"] = "completed"
            db_data["single_company"]["company_id"] = company_id
            db_data["single_company"]["company_name"] = company_name
            db_data["prospecting_cycle"]["status"] = "company_qualification"  # Company is qualified, ready for contact fetching
            db_data["lifecycle"]["status"] = "company_qualification"
            
            campaign_id = await self.campaign_dao.create_campaign(db_data)
            if not campaign_id:
                raise ApiException("campaign_id not generated")
            
            # Create campaign_company_run with is_relevant=true (already enriched)
            campaign_company_run = {
                "campaign_id": str(campaign_id),
                "company_id": company_id,
                "company_status": False,
                "linkedin_contact_status": False,
                "is_relevant": True,  # Already enriched, mark as relevant
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "source": "single_company_flow",
                    "enrichment_source": "existing_company"
                }
            }
            await campaign_company_runs_dao.create_campaign_company_run(campaign_company_run)
            
            logger.info(f"✅ Campaign {campaign_id} created with existing company {company_id}")
            
            return {
                "request_id": None,  # No Kafka event
                "campaign_id": str(campaign_id),
                "company_exists": True,
                "company_id": company_id
            }
        
        # Company doesn't exist - create placeholder and emit Kafka
        # 1. Create campaign
        db_data = self._transform_single_company_to_db_data(query_params)
        campaign_id = await self.campaign_dao.create_campaign(db_data)

        if not campaign_id:
            raise ApiException("campaign_id not generated")

        # 2. Create placeholder company with domain
        company_data = {
            "identifiers": {
                "name": "",
                "source_domain": query_params.company_domain,
                "source_id": "",
                "website_url": f"https://{query_params.company_domain}"
            },
            "source": "single_company_flow",
            "webhook_sent": False,
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "api_response": {}
            },
            "location": {
                "name": "",
                "type": ""
            },
            "profile": {
                "employee_count": [],
                "industry": [],
                "revenue_max": "",
                "revenue_min": ""
            }
        }
        company_id = await companies_dao.create_company(company_data)
        
        # 3. Create campaign_company_run with is_relevant=false (will be set true after Apollo enrichment)
        campaign_company_run = {
            "campaign_id": str(campaign_id),
            "company_id": str(company_id),
            "company_status": False,
            "linkedin_contact_status": False,
            "is_relevant": False,  # Initially false, will be set true after Apollo enrichment
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source": "single_company_flow"
            }
        }
        await campaign_company_runs_dao.create_campaign_company_run(campaign_company_run)

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        # 4. Emit Kafka event with only campaign_id (handler will fetch domain from campaign)
        event = {
            "request_id": request_id,
            "action": "process_single_company",
            "campaign_id": str(campaign_id),
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.single_company_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": str(campaign_id)}
        )

        logger.info(f"📤 Single Company Campaign ID {str(campaign_id)} queued for Apollo domain search: {request_id}")

        return {
            "request_id": request_id,
            "campaign_id": str(campaign_id),
            "company_exists": False
        }

    def _transform_single_company_to_db_data(self, query_params: CreateCampaignFromSingleCompany) -> Dict[str, Any]:
        """Transform single company request to database format"""
        return {
            "prompts": {
                "web": None,
                "persona": None
            },
            "segmentation": {
                "industry": [],
                "keywords": None,
                "categories": None
            },
            "target": {
                "employee_count": [],
                "revenue_min": None,
                "revenue_max": None,
                "currency": None,
                "location": {
                    "type": None,
                    "names": []
                }
            },
            "ownership": {
                "hubspot_email": query_params.hubspot_email,
                "product_name": query_params.product_name,
                "business_team": query_params.business_team,
                "user_email": query_params.user_email
            },
            "lifecycle": {"status": "active"},
            "prospecting_cycle": {
                "status": query_params.prospecting_cycle_status
            },
            "campaign_type": query_params.campaign_type,
            "single_company": {
                "domain": query_params.company_domain,
                "status": "pending"  # pending -> processing -> completed -> failed
            },
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }

    def _transform_create_campaign_from_prospecting_job_to_db_data(self, query_params: CreateCampaignFromProspectingJob) -> Dict[str, Any]:
        return {
            "prompts": {
                "web": query_params.web_prompt,
                "persona": query_params.persona_prompt
            },
            "segmentation": {
                "industry": self._parse_list(query_params.industry, ';'),
                "keywords": query_params.keywords,
                "categories": query_params.categories
            },
            "target": {
                "employee_count": self._parse_list(query_params.employee_count, ','),
                "revenue_min": query_params.revenue_min,
                "revenue_max": query_params.revenue_max,
                "currency": query_params.currency,
                "location": {
                    "type": query_params.location_type,
                    "names": self._parse_list(query_params.location, ',')
                }
            },
            "ownership": {
                "hubspot_email": query_params.hubspot_email,
                "product_name": query_params.product_name,
                "business_team": query_params.business_team,
                "user_email": query_params.user_email
            },
            "lifecycle": {"status": "active"},
            "prospecting_cycle": {
                "status": query_params.prospecting_cycle_status
            },
            "shortlisting_approach": query_params.shortlisting_approach,
            "campaign_type": query_params.campaign_type,  # Store campaign type for future reference
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
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
        if query_params.prospecting_cycle_status:
            query["prospecting_cycle.status"] = query_params.prospecting_cycle_status
        campaigns, pagination_info = await self.campaign_dao.get_campaigns_paginated(query, query_params.page, query_params.limit)
        serialized_campaigns = serialize_objectid(campaigns)
        return {"campaigns": serialized_campaigns, "pagination_info": pagination_info}

    async def get_prospecting_campaigns(self, page: int = 1, limit: int = 10, prospecting_cycle_status: str = None):
        """Get campaigns that have prospecting_cycle.status defined (i.e., are part of prospecting workflow)"""
        query = {
            "prospecting_cycle.status": {"$exists": True, "$ne": None}
        }
        # If specific status provided, filter by it
        if prospecting_cycle_status:
            query["prospecting_cycle.status"] = prospecting_cycle_status
        
        campaigns, pagination_info = await self.campaign_dao.get_campaigns_paginated(query, page, limit)
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
               