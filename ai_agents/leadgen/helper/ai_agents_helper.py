from datetime import datetime
from bson import ObjectId
from typing import Dict, Any
import json
from ai_agents.leadgen.schemas.ai_agents import LushaContactEnrichment, LushaGetContactEnrichment
from database.collection_dao.companies import CompaniesDao
from database.factory import (
    get_campaigns_dao,
    get_companies_dao,
    get_contacts_dao,
    get_campaign_company_runs_dao,
    get_campaign_contact_runs_dao,
)
from config.logging import logger
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from ai_agents.leadgen.services.ai_agents_service import CompanyService, ContactService
from ai_agents.leadgen.schemas.contact_models import ContactDocument
from ai_agents.leadgen.schemas.ai_agents import SaveProspectsDataToMongo, ApolloContactEnrichment
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from database.collection_dao.campaign_contact_runs import CampaignContactRunsDao
from global_utils.exceptions import ApiException
from integrations.apollo.apollo_helper import ApolloHelper
from kafkautils.constants import (
    KAFKA_SERVICE_CONFIG_MAPPING,
    LeadgenServices,
    CONTACTS_ENRICHMENT,
    LEADGEN_COMPANY_QUALIFICATION_AI_PROCESSING,
    LEADGEN_CONTACT_QUALIFICATION_AI_PROCESSING,
    LEADGEN_APOLLO_CONTACT_LIST_PROCESSING,
    LEADGEN_HUBSPOT_SYNC_PROCESSING,
)
from kafkautils.producer.event_helpers import emit_event_helper
import uuid
import asyncio
from ai_agents.leadgen.schemas.ai_agents import Campaigns, Companies, CompanyContacts, ManualCompanyQualification
from ai_agents.leadgen.services.ai_agents_service import CampaignService
from ai_agents.leadgen.utils import serialize_objectid
from ai_agents.leadgen.schemas.ai_agents import CampaignDetailsWithCompanies
from database.collection_dao.campaigns import CampaignsDao
from ai_agents.leadgen.schemas.ai_agents import AiCompanyQualification, AiContactQualification, ApolloContactList, UpdateApolloContactEnrichmentStatus, GetCampaignContactList, CampaignContactList
class LushaContactEnrichmentHelper:

    def __init__(self):
        self.lusha_api_client = LushaAPIClient()
        self.company_service = CompanyService()
        self.contact_service = ContactService()
        # Use DAO factory for database-agnostic access
        self.companies_dao = get_companies_dao(loaded_config.connection_manager)

    async def lusha_get_contact_enrichment(self, query_params: LushaGetContactEnrichment):
        campaign_id = query_params.campaign_id
        company_map_list = query_params.company_map_list
        page = query_params.page
        page_size = query_params.page_size
        departments = query_params.departments

        if not campaign_id:
            raise ApiException("Campaign Id is required")

        # if len(company_map_list) > 10:
        #     raise ApiException("Company map list should be less than 10")

        company_names = []
        company_source_id_name_mappings = {}

        if company_map_list:
            for companies in company_map_list:
                company_id = companies.get("company_id", "")
                company_doc = await self.companies_dao.get_company(company_id)

                if not company_doc:
                    logger.warning(f"Company not found: {company_id}")
                    continue

                company_name = company_doc.get("identifiers", {}).get("name", "")
                company_source_id_name_mappings[company_name] = company_id
                company_names.append(company_name)

        payload = {
            "page": page,
            "page_size": page_size,
            "company_names": company_names
        }

        if departments:
            payload["departments"] = departments

        contact_ids = []
        result = {
            'contact_ids': [],
            'company_source_id_name_mappings': [],
            'campaign_id': str(campaign_id),
            'lusha_request_id': "",
            'total_results': 0
        }

        if company_names:
            response = await self.lusha_api_client.lusha_contact_search_api(payload)
            logger.info(f"Lusha contact search API response: {response}")
            req_id = response.get("requestId", "")
            result['lusha_request_id'] = req_id
            result['total_results'] = response.get("totalResults", 0)
            contacts = response.get("data", [])

            for contact in contacts:
                id = contact.get("contactId")
                contact_ids.append(id)

        logger.info("fetching enrich data")

        result['contact_ids'] = contact_ids
        result['company_source_id_name_mappings'] = company_source_id_name_mappings

        return result

    async def lusha_contact_enrichment(self, query_params: LushaContactEnrichment):
        contact_ids = query_params.contact_ids
        company_source_id_name_mappings = query_params.company_source_id_name_mappings
        campaign_id = query_params.campaign_id
        req_id = query_params.lusha_request_id

        if req_id and contact_ids:
            enriched_contact_data = await self.lusha_api_client.lusha_contact_enrich_api(req_id, contact_ids)
            logger.info("fetched enrich data")

            if "contacts" in enriched_contact_data:
                for contact in enriched_contact_data["contacts"]:
                    data = contact.get("data", {})
                    linkedin_url = data.get("socialLinks", {}).get("linkedin", "")
                    email_addresses = [email["email"] for email in data.get("emailAddresses", []) if "email" in email]
                    phone_numbers = [phone["number"] for phone in data.get("phoneNumbers", []) if "number" in phone]
                    contact_dao = self.contact_service.contacts_dao
                    db_contacts = await contact_dao.get_contacts(
                        {
                            "linkedin_data.linkedin_url": linkedin_url
                        }
                    )

                    if db_contacts:
                        db_contact = db_contacts[0]
                        contact_id = db_contact["_id"]
                        db_company_name = db_contact.get("contact_data", {}).get("company", "")
                        company_id = company_source_id_name_mappings.get(db_company_name, "")
                        logger.info(f"company_id: {company_id} db_company_name: {db_company_name}")

                        if not company_id:
                            logger.info(f"company mismatch, skipping: {contact_id}")
                            continue


                        logger.info(f"contact found, updating contact: {contact_id}")
                        await contact_dao.update_contact(
                            contact_id,
                            {
                                "$set": {
                                    "contact_data.email": email_addresses,
                                    "contact_data.phone": phone_numbers,
                                    "metadata.updated_at": datetime.utcnow(),
                                    "metadata.lusha_raw_data": data
                                }
                            }
                        )
                        await self.contact_service.insert_campaign_contact_run(
                            {
                                "campaign_id": campaign_id,
                                "company_id": company_id,
                                "contact_id": contact_id,
                                "metadata": {
                                    "created_at": datetime.utcnow(),
                                    "updated_at": datetime.utcnow(),
                                }
                            }
                        )
                        
                    else:
                        firstname = data.get("firstName", "")
                        lastname = data.get("lastName", "")
                        job_title = data.get("jobTitle", "")
                        company_name = data.get("companyName", "")

                        contact_company_id = company_source_id_name_mappings.get(
                            company_name, "")

                        if not contact_company_id:
                            logger.info(
                                f"Company name not found in company_source_id_name_mappings: {data['companyName']}")
                            continue

                        contact_doc = {
                            "company_id": contact_company_id,
                            "contact_data": {
                                "firstname": firstname,
                                "lastname": lastname,
                                "email": email_addresses,
                                "phone": phone_numbers,
                                "jobtitle": job_title,
                                "company": company_name,
                            },
                            "linkedin_data": {
                                "linkedin_url": linkedin_url,
                                "source": "LUSHA-ENRICHER"
                            },
                            "metadata": {
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                                "lusha_raw_data": data
                            }
                        }
                        contact_doc = ContactDocument(**contact_doc)
                        await self.contact_service.create_contact(contact_doc, campaign_id)
                        logger.info(f"contact_doc: {contact_doc}")
                        
        return {"message": "Contact enrichment completed"}


class SaveProspectsDataToMongoHelper:

    def __init__(self):
        self.contact_service = ContactService()
        self.company_service = CompanyService()
        # Use DAO factory for database-agnostic access
        self.campaign_company_runs_dao = get_campaign_company_runs_dao(loaded_config.connection_manager)
        self.contacts_dao = get_contacts_dao(loaded_config.connection_manager)

    async def save_prospects_data_to_mongo(self, query_params: SaveProspectsDataToMongo):
        prospects = query_params.prospects
        campaign_id = query_params.campaign_id
        company_name = query_params.company_name
        company_id = query_params.company_id

        await self.campaign_company_runs_dao.update_campaign_company_run(
            {"campaign_id": campaign_id,
             "company_id": company_id
            }, 
            {
                "$set": {
                    "company_status": True,
                    "metadata.updated_at": datetime.utcnow()
                }
            }
        )
        inserted_ids = []

        for prospect in prospects:
            linkedin_url = prospect.get("linkedin_profile", "")
            linkedin_url = linkedin_url.lower().rstrip('/')
            stored_contacts = await self.contacts_dao.get_contacts(
                {
                    "linkedin_data.linkedin_url": linkedin_url,
                    "company_id": company_id
                }
            )

            if len(stored_contacts) == 0:
                full_name = prospect.get("name", "")
                name_parts = full_name.split(" ", 1) if full_name else ["", ""]
                firstname = name_parts[0]
                lastname = name_parts[1] if len(name_parts) > 1 else ""
                emails = [prospect.get("email")] if prospect.get("email") else []
                phones = [prospect.get("phone_number")] if prospect.get("phone_number") else []
                contact_doc = {
                    "company_id": company_id,
                    "contact_data": {
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": emails,
                        "phone": phones,
                        "jobtitle": prospect.get("title", ""),
                        "company": prospect.get("company", company_name),
                        
                    },
                    "linkedin_data": {
                        "linkedin_url": linkedin_url,
                        "source": "AI-SDR"
                    },
                    "metadata": {
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
                contact_doc = ContactDocument(**contact_doc)
                await self.contact_service.create_contact(contact_doc, campaign_id)

            else:
                contact = stored_contacts[0]
                contact_id = contact.get("_id", "")
                inserted_ids.append(contact_id)
                logger.info(f"contact already exists, skipping: {contact_id}")

        for id in inserted_ids:
            campaign_contact_run_doc = {
                "campaign_id": campaign_id,
                "company_id": company_id,
                "contact_id": id,
                "contact_status": False,
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
            await self.contact_service.insert_campaign_contact_run(campaign_contact_run_doc)

        logger.info("prospects data saved to mongo")
        return {"message": "Prospects data saved to mongo"}


class ApolloContactEnrichmentHelper:

    def __init__(self):
        self.apollo_helper = ApolloHelper()
        self.kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][CONTACTS_ENRICHMENT]
        self.event_emitter = loaded_config.connection_manager.event_emitter
        # Use DAO factory for database-agnostic access
        self.company_dao = get_companies_dao(loaded_config.connection_manager)


    async def apollo_contact_enrichment(self, query_params: ApolloContactEnrichment):
        company_domains = query_params.company_domain
        interested_product = query_params.interested_product
        slack_metadata = query_params.slack_metadata

        if not interested_product:
            raise ApiException("Interested product is required")

        if not company_domains:
            raise ApiException("Company names are required")

        #============================================

        
        company_ids = []
        for company_domain in company_domains:
            company_doc = await self.company_dao.get_company_by_filters({"identifiers.source_domain": company_domain})
            if not company_doc:
                inserted_company_id = await self.company_dao.create_company({
                    "identifiers": {
                        "name": company_domain,
                        "source_domain": company_domain
                    },
                    "source": "apollo",
                    "webhook_sent": False,
                    "metadata": {
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                })
                company_ids.append(str(inserted_company_id))
            else:
                #update webhook_sent to False
                await self.company_dao.update_company(company_doc["_id"], {"webhook_sent": False, "metadata.updated_at": datetime.utcnow()})
                company_ids.append(str(company_doc["_id"]))

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_contacts_enrichment",
            "company_ids": company_ids, 
            "interested_product": interested_product,
            "slack_metadata": slack_metadata,
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "company_ids": company_ids, "interested_product": interested_product, "slack_metadata": slack_metadata}
        )

        logger.info(f"company_ids: {company_ids}")
        logger.info(f"📤 Company Domains {company_domains} queued for processing: {request_id}")

        return {"message": "All company contacts enriched", "company_ids": company_ids}


class CampaignsHelper:

    def __init__(self):
        self.campaign_service = CampaignService()
        # Use DAO factory for database-agnostic access (supports both MongoDB and PostgreSQL)
        self.campaign_dao = get_campaigns_dao(loaded_config.connection_manager)
        self.companies_dao = get_companies_dao(loaded_config.connection_manager)
        self.campaign_company_runs_dao = get_campaign_company_runs_dao(loaded_config.connection_manager)
        self.campaign_contact_runs_dao = get_campaign_contact_runs_dao(loaded_config.connection_manager)
        self.contacts_dao = get_contacts_dao(loaded_config.connection_manager)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.company_qualification_ai_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_COMPANY_QUALIFICATION_AI_PROCESSING]
        self.contact_qualification_ai_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_CONTACT_QUALIFICATION_AI_PROCESSING]
        self.apollo_contact_list_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_APOLLO_CONTACT_LIST_PROCESSING]
        self.hubspot_sync_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_HUBSPOT_SYNC_PROCESSING]

    async def get_campaigns(self, query_params: Campaigns):
        campaigns = await self.campaign_service.get_campaigns(query_params)
        #get company mappings counts for each campaign
        for campaign in campaigns.get("campaigns"):
            company_mappings_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign["_id"], "is_relevant": True})
            total_company_mappings_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign["_id"]})
            contact_runs_count = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count({"campaign_id": campaign["_id"]})

            campaign["relevant_company_mappings_count"] = company_mappings_count
            campaign["total_company_mappings_count"] = total_company_mappings_count
            campaign["contact_runs_count"] = contact_runs_count

        return campaigns

    async def get_prospecting_campaigns(self, page: int = 1, limit: int = 10, prospecting_cycle_status: str = None):
        """Get campaigns that have prospecting_cycle.status defined (for prospecting workflow)"""
        campaigns_data = await self.campaign_service.get_prospecting_campaigns(page, limit, prospecting_cycle_status)
        # Add company/contact counts for each campaign
        for campaign in campaigns_data.get("campaigns", []):
            company_mappings_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign["_id"], "is_relevant": True})
            total_company_mappings_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign["_id"]})
            contact_runs_count = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count({"campaign_id": campaign["_id"]})

            campaign["relevant_company_mappings_count"] = company_mappings_count
            campaign["total_company_mappings_count"] = total_company_mappings_count
            campaign["contact_runs_count"] = contact_runs_count

        return campaigns_data

    async def get_campaign_details_with_companies(self, query_params: CampaignDetailsWithCompanies):
        campaign = await self.campaign_service.get_campaign_details(query_params.campaign_id)
        query = {}
        query["campaign_id"] = query_params.campaign_id
        if query_params.company_status != None:
            query["is_relevant"] = query_params.company_status
        companies, pagination_info = await self.campaign_company_runs_dao.get_campaign_company_runs_paginated(query, query_params.page, query_params.limit)

        #

        # Attach basic company details for better UI rendering (avoid N+1 by bulk fetching).
        company_ids = [c.get("company_id") for c in companies if c.get("company_id")]
       
        company_map = {}
        if company_ids:
            company_docs = await self.companies_dao.find_many(
                {"_id": {"$in": company_ids}},
                projection={
                    "_id": 1,
                    "identifiers": 1,
                    "profile": 1,
                    "location": 1,
                    "source": 1,
                },
            )
            company_map = {doc.get("_id"): doc for doc in company_docs}
        for run in companies:
            # Override is_relevant if company_status filter was provided
            if query_params.company_status is not None:
                run["is_relevant"] = query_params.company_status
            # Attach company details
            cid = run.get("company_id")
            doc = company_map.get(cid)
            if doc:
                run["company"] = doc
            # sync_to_hubspot_status is already included if present in the document

        serialized_campaign = serialize_objectid(campaign)
        serialized_companies = serialize_objectid(companies)
        return {"campaign": serialized_campaign, "companies": serialized_companies, "pagination_info": pagination_info}

    async def get_company_qualification_progress(self, campaign_id: str):
        """
        Lightweight progress info for long-running AI company qualification.
        Falls back to computing counts from campaign_company_runs if progress isn't present.
        """
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")

        job = campaign.get("prospecting_cycle", {}).get("company_qualification_ai") or {}

        total = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign_id})
        remaining = await self.campaign_company_runs_dao.get_campaign_company_runs_count(
            {"campaign_id": campaign_id, "is_relevant": {"$exists": False}}
        )
        relevant = await self.campaign_company_runs_dao.get_campaign_company_runs_count(
            {"campaign_id": campaign_id, "is_relevant": True}
        )
        processed = max(total - remaining, 0)

        # Merge computed progress with stored job info
        progress = (job.get("progress") or {}).copy()
        progress["total"] = int(progress.get("total") or total)
        progress["processed"] = int(progress.get("processed") or processed)
        progress["relevant"] = int(progress.get("relevant") or relevant)

        return {
            "campaign_id": str(campaign.get("_id")),
            "status": job.get("status") or "not_started",
            "request_id": job.get("request_id"),
            "started_at": job.get("started_at"),
            "updated_at": job.get("updated_at"),
            "error": job.get("error"),
            "progress": progress,
        }

    async def manual_company_qualification(self, query_params: ManualCompanyQualification):
        campaign_id = query_params.campaign_id
        company_ids = query_params.company_ids
        is_relevant = query_params.is_relevant
        selection_type = query_params.selection_type

        if selection_type == "all":
            await self.campaign_company_runs_dao.update_campaign_company_run_by_campaign_id(campaign_id, {"$set": {"is_relevant": is_relevant}})
        else:
            chunk_size = 500
            for i in range(0, len(company_ids), chunk_size):
                chunk = company_ids[i:i + chunk_size]
                await self.campaign_company_runs_dao.update_campaign_company_runs(
                    {"campaign_id": campaign_id, "company_id": {"$in": chunk}},
                    {"$set": {"is_relevant": is_relevant}}
                )
        update_campaign = await self.campaign_dao.update_campaign(campaign_id, {"prospecting_cycle.status": "company_qualification"})
        return {"message": "Company qualification completed"}

    async def ai_company_qualification(self, query_params: AiCompanyQualification):
        campaign_id = query_params.campaign_id
        web_prompt = query_params.web_prompt

        if not web_prompt:
            raise ApiException("Web prompt is required")

        request_id = str(uuid.uuid4())

        # Initialize / update AI qualification job status + progress (non-blocking background job)
        total = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign_id})
        remaining = await self.campaign_company_runs_dao.get_campaign_company_runs_count(
            {"campaign_id": campaign_id, "is_relevant": {"$exists": False}}
        )
        relevant = await self.campaign_company_runs_dao.get_campaign_company_runs_count(
            {"campaign_id": campaign_id, "is_relevant": True}
        )
        processed = max(total - remaining, 0)

        update_campaign = await self.campaign_dao.update_campaign(
            campaign_id,
            {
                "prompts.web": web_prompt,
                "metadata.updated_at": datetime.utcnow(),
                "prospecting_cycle.company_qualification_ai": {
                    "status": "queued",
                    "request_id": request_id,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "error": None,
                    "progress": {
                        "total": int(total),
                        "processed": int(processed),
                        "relevant": int(relevant),
                    },
                },
            },
        )

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_company_qualification_ai",
            "campaign_id": campaign_id,
            "web_prompt": web_prompt,
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.company_qualification_ai_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": campaign_id, "web_prompt": web_prompt},
        )
        if not update_campaign:
            raise ApiException("Campaign not found")
        return {"message": "Campaign updated", "campaign_id": campaign_id}

    async def ai_contact_qualification(self, query_params: AiContactQualification):
        """
        Queue AI contact qualification job via Kafka.
        Similar pattern to ai_company_qualification but for contacts.
        """
        campaign_id = query_params.campaign_id
        contact_prompt = query_params.contact_prompt

        request_id = str(uuid.uuid4())

        # Get current contact counts for progress tracking
        total = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count({"campaign_id": campaign_id})
        remaining = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": campaign_id, "$or": [{"is_relevant":False }, {"is_relevant": {"$exists": False}}] }
        )
        relevant = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": campaign_id, "is_relevant": True}
        )
        processed = max(total - remaining, 0)

        # Update campaign with AI contact qualification job info
        update_campaign = await self.campaign_dao.update_campaign(
            campaign_id,
            {
                "prompts.contact": contact_prompt,
                "metadata.updated_at": datetime.utcnow(),
                "prospecting_cycle.contact_qualification_ai": {
                    "status": "queued",
                    "request_id": request_id,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "error": None,
                    "progress": {
                        "total": int(total),
                        "processed": int(processed),
                        "relevant": int(relevant),
                    },
                },
            },
        )

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_contact_qualification_ai",
            "campaign_id": campaign_id,
            "contact_prompt": contact_prompt,
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.contact_qualification_ai_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": campaign_id, "contact_prompt": contact_prompt},
        )

        if not update_campaign:
            raise ApiException("Campaign not found")
        return {"message": "AI contact qualification queued", "campaign_id": campaign_id, "request_id": request_id}

    async def get_contact_qualification_progress(self, campaign_id: str):
        """
        Lightweight progress info for long-running AI contact qualification.
        Uses relevance_reason field to determine if contact has been processed.
        """
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")

        job = campaign.get("prospecting_cycle", {}).get("contact_qualification_ai") or {}

        # Total contacts in this campaign
        total = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count({"campaign_id": campaign_id})
        
        # Processed = contacts that have relevance_reason field (AI qualification done)
        processed = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": campaign_id, "relevance_reason": {"$exists": True}}
        )
        
        # Relevant = contacts marked as relevant by AI
        relevant = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": campaign_id, "is_relevant": True}
        )

        # Merge computed progress with stored job info
        progress = (job.get("progress") or {}).copy()
        progress["total"] = int(progress.get("total") or total)
        progress["processed"] = int(progress.get("processed") or processed)
        progress["relevant"] = int(progress.get("relevant") or relevant)

        return {
            "campaign_id": str(campaign.get("_id")),
            "status": job.get("status") or "not_started",
            "request_id": job.get("request_id"),
            "started_at": job.get("started_at"),
            "updated_at": job.get("updated_at"),
            "error": job.get("error"),
            "progress": progress,
        }

    async def get_apollo_contact_list(self, query_params: ApolloContactList):
        enrichment_status = query_params.enrichment_status
        campaign_id = query_params.campaign_id
        # We just need to send the campaign_id to the kafka topic (consumer will expand to company_ids and call Apollo)
        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        

        event = {
            "request_id": request_id,
            "campaign_id": campaign_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        if enrichment_status:
            event["action"] = "enrich_apollo_contact_list"
        else:
            event["action"] = "get_apollo_contact_list"
        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.apollo_contact_list_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": campaign_id},
        )

        return {"message": "Apollo contact fetch queued", "request_id": request_id, "campaign_id": campaign_id}

    async def update_contact_relevance(self, query_params: UpdateApolloContactEnrichmentStatus):
        campaign_id = query_params.campaign_id
        contact_ids = query_params.contact_ids  if query_params.contact_ids else []
        is_relevant = query_params.is_relevant
        selection_type = query_params.selection_type
        relevance_reason = query_params.relevance_reason

        # Build update data
        update_data = {"is_relevant": is_relevant}
        if relevance_reason is not None:
            update_data["relevance_reason"] = relevance_reason

        if selection_type == "all":
            await self.campaign_contact_runs_dao.update_campaign_contact_runs({"campaign_id": campaign_id}, {"$set": update_data})
        else:
            chunk_size = 500
            for i in range(0, len(contact_ids), chunk_size):
                chunk = contact_ids[i:i + chunk_size]
                await self.campaign_contact_runs_dao.update_campaign_contact_runs(
                    {"campaign_id": campaign_id, "contact_id": {"$in": chunk}},
                    {"$set": update_data}
                )
        await self.campaign_dao.update_campaign(campaign_id, {"prospecting_cycle.status": "contact_qualification"})
        return {"message": "Contact relevance updated"}

    async def get_campaign_contact_list(self, query_params: GetCampaignContactList):
        campaign_id = query_params.campaign_id
        page = query_params.page
        limit = query_params.limit
        campaign = await self.campaign_service.get_campaign_details(query_params.campaign_id)
        contacts, pagination_info = await self.campaign_contact_runs_dao.get_campaign_contact_runs_paginated({"campaign_id": campaign_id}, page, limit)
        serialized_contacts = []
        serialized_campaign = serialize_objectid(campaign)
        for contact in contacts:
            contact_id = contact.get("contact_id")
            contact_doc = await self.contacts_dao.get_contact(contact_id)
            if contact_doc:
                contact["contact_data"] = contact_doc.get("contact_data")
                contact["linkedin_data"] = contact_doc.get("linkedin_data")
                enrichment_status = contact_doc.get("enrichment_status")
                contact["enrichment_status"] = enrichment_status
                serialized_contacts.append(serialize_objectid(contact))
        serialized_data = {
            "campaign": serialized_campaign,
            "contacts": serialized_contacts,
            "pagination_info": pagination_info
        }
        return serialized_data

    async def get_contact_list_minimal(self, campaign_id: str, page: int = 1, limit: int = 10):
        """
        OPTIMIZED API: Returns only minimal contact data needed for frontend display.
        Much faster than get_campaign_contact_list as it doesn't fetch full contact documents.
        
        Returns only:
        - contact_id, company_id, is_relevant
        - Basic display fields: firstname, lastname, email, phone, jobtitle, company
        - linkedin_url (if available)
        """
        # Get campaign status only (minimal fields)
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException(f"Campaign not found: {campaign_id}")
        
        campaign_status = {
            "prospecting_cycle": campaign.get("prospecting_cycle", {}),
            "campaign_id": str(campaign.get("_id")),
        }
        
        # Get contact runs with pagination
        contacts, pagination_info = await self.campaign_contact_runs_dao.get_campaign_contact_runs_paginated(
            {"campaign_id": campaign_id}, page, limit
        )
        
        # Build minimal contact list - only fetch needed fields from contacts collection
        minimal_contacts = []
        for contact_run in contacts:
            contact_id = contact_run.get("contact_id")
            
            # Fetch only needed fields from contact document
            contact_doc = await self.contacts_dao.get_contact(contact_id)
            if not contact_doc:
                continue
                
            contact_data = contact_doc.get("contact_data", {})
            linkedin_data = contact_doc.get("linkedin_data", {})
            
            # Build minimal response - only fields needed for UI
            minimal_contact = {
                "contact_id": str(contact_id),
                "company_id": str(contact_run.get("company_id", "")),
                "is_relevant": contact_run.get("is_relevant", False),
                "relevance_reason": contact_run.get("relevance_reason"),
                # Only essential display fields
                "firstname": contact_data.get("firstname", ""),
                "lastname": contact_data.get("lastname", ""),
                "email": contact_data.get("email", [None])[0] if contact_data.get("email") else None,
                "phone": contact_data.get("phone", [None])[0] if contact_data.get("phone") else None,
                "jobtitle": contact_data.get("jobtitle", ""),
                "company": contact_data.get("company", ""),
                "linkedin_url": linkedin_data.get("linkedin_url"),
            }
            minimal_contacts.append(minimal_contact)
        
        return {
            "campaign_status": campaign_status,
            "contacts": minimal_contacts,
            "pagination": pagination_info,
            "total_count": pagination_info.get("total_records", 0),
        }

    async def get_campaign_status_minimal(self, campaign_id: str):
        """
        OPTIMIZED API: Returns only campaign status - no contact data.
        Use this for polling campaign progress (Step1, Step2, Step3).
        """
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException(f"Campaign not found: {campaign_id}")
        
        prospecting_cycle = campaign.get("prospecting_cycle", {})
        lifecycle = campaign.get("lifecycle", {})
        csv_import = campaign.get("csv_import", {})
        single_company = campaign.get("single_company", {})

        #count company runs count
        company_runs_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id)})
        
        # Count contacts for progress display
        total_contacts = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": ObjectId(campaign_id)}
        )
        relevant_contacts = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count(
            {"campaign_id": ObjectId(campaign_id), "is_relevant": True}
        )
        
        return {
            "campaign_id": str(campaign.get("_id")),
            "status": prospecting_cycle.get("status"),
            "total_contacts": total_contacts,
            "relevant_contacts": relevant_contacts,
            "prospecting_cycle": prospecting_cycle,
            "lifecycle": lifecycle,
            "csv_import": csv_import,
            "single_company": single_company,
            "company_runs_count": company_runs_count,
        }

    async def get_company_list_minimal(self, campaign_id: str, page: int = 1, limit: int = 100, company_status: bool = None):
        """
        OPTIMIZED API: Returns only minimal company data needed for Company Qualification UI.
        Much faster than get_campaign_details_with_companies as it:
        1. Only returns essential campaign status (not full campaign)
        2. Only fetches needed company fields (not full company documents)
        
        Returns only:
        - campaign_status: { campaign_id, prospecting_cycle.status }
        - companies: [ { company_id, is_relevant, name, domain, industry, employee_count, location, revenue, relevance_reason } ]
        """
        # Get campaign status only (minimal fields)
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException(f"Campaign not found: {campaign_id}")
        
        campaign_status = {
            "campaign_id": str(campaign.get("_id")),
            "prospecting_cycle": {
                "status": campaign.get("prospecting_cycle", {}).get("status"),
            },
        }
        
        # Build query
        query = {"campaign_id": campaign_id}
        if company_status is not None:
            query["is_relevant"] = company_status
        
        # Get company runs with pagination
        company_runs, pagination_info = await self.campaign_company_runs_dao.get_campaign_company_runs_paginated(
            query, page, limit
        )
        
        # Get company IDs for bulk fetch
        company_ids = [c.get("company_id") for c in company_runs if c.get("company_id")]
        
        # Fetch only needed company fields (minimal projection)
        company_map = {}
        if company_ids:
            company_docs = await self.companies_dao.find_many(
                {"_id": {"$in": company_ids}},
                projection={
                    "_id": 1,
                    "identifiers.name": 1,
                    "identifiers.domain": 1,
                    "identifiers.source_domain": 1,
                    "profile.industry": 1,
                    "profile.employee_count": 1,
                    "profile.revenue_min": 1,
                    "profile.revenue_max": 1,
                    "location.name": 1,
                },
            )
            company_map = {str(doc.get("_id")): doc for doc in company_docs}
        
        # Build minimal company list
        minimal_companies = []
        for run in company_runs:
            company_id = str(run.get("company_id", ""))
            company_doc = company_map.get(company_id, {})
            identifiers = company_doc.get("identifiers", {})
            profile = company_doc.get("profile", {})
            location = company_doc.get("location", {})
            
            minimal_company = {
                "company_id": company_id,
                "is_relevant": run.get("is_relevant", False),
                # Essential display fields
                "name": identifiers.get("name") or identifiers.get("source_domain") or identifiers.get("domain") or company_id,
                "domain": identifiers.get("domain"),
                "source_domain": identifiers.get("source_domain"),
                "industry": profile.get("industry"),
                "employee_count": profile.get("employee_count"),
                "location": location.get("name"),
                "revenue_min": profile.get("revenue_min"),
                "revenue_max": profile.get("revenue_max"),
                # AI qualification reason
                "relevance_reason": run.get("metadata", {}).get("relevance_reason"),
            }
            minimal_companies.append(minimal_company)
        
        return {
            "campaign_status": campaign_status,
            "companies": minimal_companies,
            "pagination": pagination_info,
            "total_count": pagination_info.get("total_items", 0),
        }

    async def sync_to_hubspot(self, campaign_id: str):
        """
        Queue contacts for HubSpot sync via Kafka.
        This emits an event to the HubSpot sync processing topic.
        """
        if not campaign_id:
            raise ApiException("Campaign ID is required")

        # Verify campaign exists
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException(f"Campaign not found: {campaign_id}")

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "sync_to_hubspot",
            "campaign_id": campaign_id,
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.hubspot_sync_kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": campaign_id}
        )

        logger.info(f"📤 HubSpot sync queued for campaign {campaign_id}: {request_id}")

        return {
            "message": "HubSpot sync queued",
            "request_id": request_id,
            "campaign_id": campaign_id
        }
    async def sync_from_hubspot_webhook(self, query_params: Dict[str, Any]):
        """
        Sync contacts from HubSpot webhook.
        """
        webhook_data = query_params.get("webhook_data")
        campaign_id = webhook_data.get("campaign_id")
        company_id = webhook_data.get("company_id")
        if not company_id or not campaign_id:
            raise ApiException("Company ID and campaign ID are required")
        #here store whole query_params in metadata.sync_hubspot_webhook_received
        json_query_data = json.dumps(webhook_data)
        update_campaign = {
            "metadata.updated_at": datetime.utcnow(),
            "metadata.sync_hubspot_webhook_received": json_query_data
        }
        await self.campaign_company_runs_dao.update_campaign_company_run({"company_id": ObjectId(company_id), "campaign_id": ObjectId(campaign_id)}, {"$set": {"sync_to_hubspot_status": "synced", "metadata.updated_at": datetime.utcnow(),"metadata.sync_hubspot_webhook_received": json_query_data}})
        #total company runs count
        total_company_runs_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True, "sync_to_hubspot_status": {"$exists": True}})
        #total company runs count synced
        total_company_runs_count_synced = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True, "sync_to_hubspot_status": "synced"})

        if total_company_runs_count_synced == total_company_runs_count:
            update_campaign["prospecting_cycle.status"] = "hubspot_sync_completed"
        await self.campaign_dao.update_campaign(campaign_id, update_campaign)
        return {
            "message": "HubSpot sync completed",
            "company_id": company_id,
            "campaign_id": campaign_id
        }

    async def get_hubspot_synced_companies(self, campaign_id: str):
        """
        OPTIMIZED: Returns only minimal data needed for HubSpot sync progress polling.
        No longer returns full campaign object - just status and counts.
        """
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        
        if not campaign:
            raise ApiException("Campaign not found")
        synced_hubspot_companies_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True, "sync_to_hubspot_status": "synced"})
        total_hubspot_companies_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True, "sync_to_hubspot_status": {"$exists": True}})

        # OPTIMIZED: Only return fields needed for UI polling
        # No longer returning full campaign object (was causing excess data transfer)
        return {
            "_id": str(campaign.get("_id")),
            "campaign_id": campaign_id,
            "prospecting_cycle": {
                "status": campaign.get("prospecting_cycle", {}).get("status"),
            },
            "synced_hubspot_companies_count": synced_hubspot_companies_count,
            "total_hubspot_companies_count": total_hubspot_companies_count,
        }

    async def save_contact_personalization(self, campaign_id: str, contact_id: str, email_id: str, personalized_message: str, ai_generated_deck: str):
        """Save personalization data for a single contact"""
        from datetime import datetime
        
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")
        
        # Update the campaign_contact_run with personalization data
        update_data = {
            "$set": {
                "personalized_message": personalized_message,
                "ai_generated_deck": ai_generated_deck,
                "email_id": email_id,
                "personalization_status": "approved",
                "metadata.updated_at": datetime.utcnow()
            }
        }
        
        result = await self.campaign_contact_runs_dao.update_campaign_contact_run(
            {"campaign_id": ObjectId(campaign_id), "contact_id": ObjectId(contact_id)},
            update_data
        )
        
        return {
            "message": "Personalization saved successfully",
            "campaign_id": campaign_id,
            "contact_id": contact_id
        }

    async def bulk_save_contact_personalization(self, campaign_id: str, personalizations: list):
        """Save personalization data for multiple contacts"""
        from datetime import datetime
        
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")
        
        saved_count = 0
        for personalization in personalizations:
            contact_id = personalization.get("contact_id")
            email_id = personalization.get("email_id")
            personalized_message = personalization.get("personalized_message")
            ai_generated_deck = personalization.get("ai_generated_deck")
            
            if not all([contact_id, email_id, personalized_message, ai_generated_deck]):
                continue
            
            update_data = {
                "$set": {
                    "personalized_message": personalized_message,
                    "ai_generated_deck": ai_generated_deck,
                    "email_id": email_id,
                    "personalization_status": "approved",
                    "metadata.updated_at": datetime.utcnow()
                }
            }
            
            await self.campaign_contact_runs_dao.update_campaign_contact_run(
                {"campaign_id": ObjectId(campaign_id), "contact_id": ObjectId(contact_id)},
                update_data
            )
            saved_count += 1
        
        # Update campaign status to personalization_completed if needed
        if saved_count > 0:
            await self.campaign_dao.update_campaign(campaign_id, {
                "prospecting_cycle.status": "personalization_completed"
            })
        
        return {
            "message": f"Personalization saved for {saved_count} contacts",
            "campaign_id": campaign_id,
            "saved_count": saved_count
        }

    async def get_enrollment_contacts(self, campaign_id: str, page: int = 1, limit: int = 100):
        """Get full contact details with all metadata for sequence enrollment"""
        from datetime import datetime
        
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")
        
        # Get all campaign_contact_runs with personalization approved AND not already enrolled
        filter_query = {
            "campaign_id": ObjectId(campaign_id),
            "personalization_status": "approved",
            # Exclude contacts that are already enrolled in a Lemlist sequence
            "$or": [
                {"sequence_enrollment": {"$exists": False}},
                {"sequence_enrollment.status": {"$ne": "enrolled"}}
            ]
        }
        
        campaign_contact_runs, pagination_info = await self.campaign_contact_runs_dao.get_campaign_contact_runs_paginated(
            filter_query, page, limit
        )
        
        contacts_data = []
        for run in campaign_contact_runs:
            contact_id = run.get("contact_id")
            company_id = run.get("company_id")
            
            # Get full contact data from contacts collection
            contact = await self.contacts_dao.get_contact(str(contact_id))
            
            # Get company details
            company = await self.companies_dao.get_company(str(company_id)) if company_id else None
            
            # Build complete contact data with all metadata
            contact_data = {
                # Campaign contact run data
                "campaign_contact_run_id": str(run.get("_id")),
                "campaign_id": str(run.get("campaign_id")),
                "company_id": str(company_id) if company_id else None,
                "contact_id": str(contact_id) if contact_id else None,
                "is_relevant": run.get("is_relevant"),
                "enrichment_status": run.get("enrichment_status"),
                "personalization_status": run.get("personalization_status"),
                "personalized_message": run.get("personalized_message"),
                "ai_generated_deck": run.get("ai_generated_deck"),
                "email_id": run.get("email_id"),
                "campaign_contact_run_metadata": run.get("metadata"),
                
                # Contact data from contacts collection
                "contact_data": contact.get("contact_data") if contact else None,
                "linkedin_data": contact.get("linkedin_data") if contact else None,
                "contact_metadata": contact.get("metadata") if contact else None,
                
                # Company data
                "company_data": {
                    "name": company.get("name") if company else None,
                    "domain": company.get("domain") if company else None,
                    "website": company.get("website") if company else None,
                    "industry": company.get("industry") if company else None,
                    "employee_count": company.get("employee_count") if company else None,
                    "revenue": company.get("revenue") if company else None,
                    "location": company.get("location") if company else None,
                    "description": company.get("description") if company else None,
                    "company_metadata": company.get("metadata") if company else None,
                } if company else None,
            }
            
            contacts_data.append(contact_data)
        
        serialized_campaign = serialize_objectid(campaign)
        
        return {
            "campaign": serialized_campaign,
            "contacts": contacts_data,
            "pagination": pagination_info,
            "total_enrollment_ready": len(contacts_data)
        }

    async def enroll_contacts_to_sequence(self, campaign_id: str, sequence_id: str, sequence_name: str, contact_ids: list = None):
        """Enroll contacts to a Lemlist sequence - saves enrollment details and returns full contact data"""
        from datetime import datetime
        
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        if not campaign:
            raise ApiException("Campaign not found")
        
        # Build filter query
        filter_query = {
            "campaign_id": ObjectId(campaign_id),
            "personalization_status": "approved"
        }
        
        if contact_ids:
            filter_query["contact_id"] = {"$in": [ObjectId(cid) for cid in contact_ids]}
        
        # Get all matching contact runs
        campaign_contact_runs = await self.campaign_contact_runs_dao.get_campaign_contact_runs(filter_query)
        
        # Build contact payloads for Lemlist
        contacts_to_enroll = []
        for run in campaign_contact_runs:
            contact_id = run.get("contact_id")
            company_id = run.get("company_id")
            
            # Get full contact data
            contact = await self.contacts_dao.get_contact(str(contact_id))
            company = await self.companies_dao.get_company(str(company_id)) if company_id else None
            
            # Build complete contact data for external service (Lemlist)
            contact_payload = {
                # Internal IDs for tracking
                "campaign_contact_run_id": str(run.get("_id")),
                "contact_id": str(contact_id),
                "company_id": str(company_id) if company_id else None,
                
                # Basic contact info
                "email": run.get("email_id"),
                "first_name": contact.get("contact_data", {}).get("firstname") if contact else None,
                "last_name": contact.get("contact_data", {}).get("lastname") if contact else None,
                "job_title": contact.get("contact_data", {}).get("jobtitle") if contact else None,
                "phone": contact.get("contact_data", {}).get("phone", []) if contact else [],
                "linkedin_url": contact.get("linkedin_data", {}).get("linkedin_url") if contact else None,
                
                # Company info
                "company_name": company.get("name") if company else None,
                "company_domain": company.get("domain") if company else None,
                "company_website": company.get("website") if company else None,
                "company_industry": company.get("industry") if company else None,
                "company_size": company.get("employee_count") if company else None,
                "company_location": company.get("location") if company else None,
                
                # Personalization data
                "personalized_message": run.get("personalized_message"),
                "ai_generated_deck": run.get("ai_generated_deck"),
                
                # All metadata
                "campaign_contact_run_metadata": serialize_objectid(run.get("metadata")),
                "contact_metadata": serialize_objectid(contact.get("metadata")) if contact else None,
                "company_metadata": serialize_objectid(company.get("metadata")) if company else None,
                "contact_source_data": contact.get("contact_data") if contact else None,
                "linkedin_data": contact.get("linkedin_data") if contact else None,
            }
            
            contacts_to_enroll.append(contact_payload)
        
        # Send contacts to Lemlist API
        lemlist_response = await self._send_to_lemlist(
            sequence_id=sequence_id,
            sequence_name=sequence_name,
            contacts=contacts_to_enroll
        )
        
        # Update each contact run with enrollment status and Lemlist lead_id
        enrolled_leads = lemlist_response.get("enrolled_leads", [])
        enrolled_leads_map = {lead.get("email"): lead for lead in enrolled_leads}
        failed_emails = [e.get("email") for e in lemlist_response.get("errors", [])]
        
        enrolled_contacts = []
        for contact in contacts_to_enroll:
            email = contact.get("email")
            lead_info = enrolled_leads_map.get(email, {})
            lemlist_lead_id = lead_info.get("lead_id")  # May be None for alreadyExists
            
            # Determine enrollment status:
            # - "enrolled" if email is in enrolled_leads (includes newly added AND already existing)
            # - "failed" if email is in errors list
            if email in failed_emails:
                enrollment_status = "failed"
            elif email in enrolled_leads_map:
                enrollment_status = "enrolled"  # Success even if lead_id is None (alreadyExists case)
            else:
                enrollment_status = "failed"
            
            # Update contact run with enrollment info
            update_data = {
                "$set": {
                    "sequence_enrollment": {
                        "sequence_id": sequence_id,
                        "sequence_name": sequence_name,
                        "lemlist_lead_id": lemlist_lead_id,  # Store Lemlist lead ID
                        "enrolled_at": datetime.utcnow(),
                        "status": enrollment_status
                    },
                    "metadata.updated_at": datetime.utcnow()
                }
            }
            
            await self.campaign_contact_runs_dao.update_campaign_contact_run(
                {"_id": ObjectId(contact.get("campaign_contact_run_id"))},
                update_data
            )
            
            # Add to enrolled contacts list for response
            contact["lemlist_lead_id"] = lemlist_lead_id
            contact["enrollment_status"] = enrollment_status
            enrolled_contacts.append(contact)
        
        # Update campaign status
        await self.campaign_dao.update_campaign(campaign_id, {
            "prospecting_cycle.status": "enrolled_to_sequence",
            "sequence_enrollment": {
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "enrolled_at": datetime.utcnow(),
                "enrolled_count": len(enrolled_contacts),
                "lemlist_response": lemlist_response
            }
        })
        
        return {
            "message": f"Successfully enrolled {len(enrolled_contacts)} contacts to sequence '{sequence_name}'",
            "campaign_id": campaign_id,
            "sequence_id": sequence_id,
            "sequence_name": sequence_name,
            "enrolled_count": len(enrolled_contacts),
            "enrolled_contacts": enrolled_contacts,
            "lemlist_api_response": lemlist_response
        }

    async def _send_to_lemlist(self, sequence_id: str, sequence_name: str, contacts: list) -> dict:
        """
        Send contacts to Lemlist campaign via API.
        
        Uses the Lemlist API v2:
        POST https://api.lemlist.com/api/campaigns/{campaignId}/leads/?version=v2
        
        Lemlist API expects data like:
        {
            "email": "lead@company.com",
            "firstName": "First",
            "lastName": "Last",
            "companyName": "Company",
            "personalised_deck_link": "url_of_the_deck.pdf",
            "personalised_message": "Content of the personalised Message"
        }
        """
        from integrations.lemlist.lemlist_inbox_client import LemlistInboxClient
        
        logger.info(f"[LEMLIST API] Starting to send {len(contacts)} contacts to campaign '{sequence_name}' (ID: {sequence_id})")
        
        # Transform contacts to Lemlist format (v2 API)
        lemlist_leads = []
        for contact in contacts:
            lemlist_leads.append({
                "email": contact.get("email"),
                "first_name": contact.get("first_name"),
                "last_name": contact.get("last_name"),
                "company_name": contact.get("company_name"),
                "personalised_deck_link": contact.get("ai_generated_deck"),
                "personalised_message": contact.get("personalized_message"),
            })
        
        # Use Lemlist client to add leads in batch
        try:
            lemlist_client = LemlistInboxClient()
            result = await lemlist_client.add_leads_to_campaign_batch(
                campaign_id=sequence_id,
                leads=lemlist_leads,
                rate_limit_delay=0.2  # 200ms between API calls to respect rate limits
            )
            
            # Build response in expected format
            response = {
                "success": result.get("failed", 0) == 0,
                "message": f"Processed {result.get('total', 0)} contacts: {result.get('success', 0)} added, {result.get('failed', 0)} failed, {result.get('already_exists', 0)} already existed",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "leads_added": result.get("success", 0),
                "leads_failed": result.get("failed", 0),
                "leads_already_exists": result.get("already_exists", 0),
                "enrolled_leads": result.get("enrolled_leads", []),
                "errors": result.get("errors", [])
            }
            
            logger.info(
                f"[LEMLIST API] Completed enrollment",
                campaign_id=sequence_id,
                success=result.get("success", 0),
                failed=result.get("failed", 0),
                already_exists=result.get("already_exists", 0)
            )
            
            return response
            
        except Exception as e:
            logger.exception(f"[LEMLIST API] Error sending contacts to Lemlist: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending contacts to Lemlist: {str(e)}",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "leads_added": 0,
                "leads_failed": len(contacts),
                "errors": [str(e)]
            }


    async def webhook_from_deepsearch_research(self, query_params: Dict[str, Any]):
        """
        Webhook from Deepsearch Research.
        """
        webhook_data = query_params.get("webhook_data")
        campaign_id = webhook_data.get("campaign_id")
        company_id = webhook_data.get("company_id")
        deepsearch_research_data = webhook_data.get("deepsearch_research_data", {})
        if not company_id or not campaign_id or not deepsearch_research_data:
            raise ApiException("Company ID, campaign ID and deepsearch research data are required")
        #here store whole query_params in metadata.deepsearch_research_data
        json_query_data = json.dumps(webhook_data)
        update_campaign_company_run = {
            "deep_research": deepsearch_research_data,
            "metadata.updated_at": datetime.utcnow(),
            "metadata.deepsearch_research_data": json_query_data
        }
        await self.campaign_company_runs_dao.update_campaign_company_run({"company_id": ObjectId(company_id), "campaign_id": ObjectId(campaign_id)}, {"$set": update_campaign_company_run})
        update_campaign = {
            "metadata.updated_at": datetime.utcnow(),
        }
        await self.campaign_dao.update_campaign(campaign_id, update_campaign)
        return {
            "message": "deepsearch research data stored",
            "company_id": company_id,
            "campaign_id": campaign_id
        }

    async def webhook_for_legal_name_and_other_entities(self, query_params: Dict[str, Any]):
        """
        Webhook for legal name and other entities.
        """
        webhook_data = query_params.get("webhook_data")
        campaign_id = webhook_data.get("campaign_id")
        company_id = webhook_data.get("company_id")
        legal_name_and_other_entities_data = webhook_data.get("legal_name_and_other_entities_data", {})
        if not company_id or not campaign_id or not legal_name_and_other_entities_data:
            raise ApiException("Company ID, campaign ID and legal name and other entities data are required")
        #here store whole query_params in metadata.legal_name_and_other_entities_data
        json_query_data = json.dumps(webhook_data)
        update_campaign_company_run = {
            "legal_name_and_other_entities": legal_name_and_other_entities_data,
            "metadata.updated_at": datetime.utcnow(),
            "metadata.legal_name_and_other_entities_data": json_query_data
        }
        await self.campaign_company_runs_dao.update_campaign_company_run({"company_id": ObjectId(company_id), "campaign_id": ObjectId(campaign_id)}, {"$set": update_campaign_company_run})
        update_campaign = {
            "metadata.updated_at": datetime.utcnow(),
        }
        await self.campaign_dao.update_campaign(campaign_id, update_campaign)
        return {
            "message": "legal name and other entities data stored",
            "company_id": company_id,
            "campaign_id": campaign_id
        }

    async def webhook_for_personalization(self, query_params: Dict[str, Any]):
        """
        Webhook for personalization.
        """
        webhook_data = query_params.get("webhook_data")
        campaign_id = webhook_data.get("campaign_id")
        company_id = webhook_data.get("company_id")
        contact_id = webhook_data.get("contact_id")
        personalization_data = webhook_data.get("personalization_data", {})
        if not company_id or not campaign_id or not personalization_data or not contact_id:
            raise ApiException("Company ID, campaign ID and personalization data are required")
        #here store whole query_params in metadata.personalization_data
        json_query_data = json.dumps(webhook_data)
        update_campaign_contact_run = {
            "personalization": personalization_data,
            "metadata.updated_at": datetime.utcnow(),
            "metadata.personalization_data": json_query_data
        }
        await self.campaign_contact_runs_dao.update_campaign_contact_run({"campaign_id": ObjectId(campaign_id), "contact_id": ObjectId(contact_id)}, {"$set": update_campaign_contact_run})
        update_campaign = {
            "metadata.updated_at": datetime.utcnow(),
        }
        await self.campaign_dao.update_campaign(campaign_id, update_campaign)
        return {
            "message": "personalization data stored",
            "company_id": company_id,
            "contact_id": contact_id,
            "campaign_id": campaign_id
        }
class CompaniesHelper:

    def __init__(self):
        self.company_service = CompanyService()
        # Use DAO factory for database-agnostic access
        self.contact_dao = get_contacts_dao(loaded_config.connection_manager)
    async def get_companies_with_contact_counts(self, query_params: Companies):
        companies = await self.company_service.get_companies(query_params)
        for company in companies.get("companies"):
            contact_count = await self.contact_dao.get_contacts_count({"company_id": company["_id"]})
            company["contact_count"] = contact_count
        return companies

    async def get_company_details_with_contacts(self, query_params: CompanyContacts):
        company = await self.company_service.get_company_details(query_params.company_id)
        contacts, pagination_info = await self.contact_dao.get_paginated_contacts({"company_id": query_params.company_id}, query_params.page, query_params.limit)
        serialized_company = serialize_objectid(company)
        serialized_contacts = serialize_objectid(contacts)
        return {"company": serialized_company, "contacts": serialized_contacts, "pagination_info": pagination_info}