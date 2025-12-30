from datetime import datetime
from bson import ObjectId
from typing import Dict, Any
import json
from ai_agents.leadgen.schemas.ai_agents import LushaContactEnrichment, LushaGetContactEnrichment
from database.collection_dao.companies import CompaniesDao
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
from ai_agents.leadgen.schemas.ai_agents import AiCompanyQualification, ApolloContactList, UpdateApolloContactEnrichmentStatus, GetCampaignContactList, CampaignContactList
class LushaContactEnrichmentHelper:

    def __init__(self):
        self.lusha_api_client = LushaAPIClient()
        self.company_service = CompanyService()
        self.contact_service = ContactService()
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)

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
        self.campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        self.contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)

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
        self.company_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)


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
        self.campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        self.campaign_contact_runs_dao = CampaignContactRunsDao(loaded_config.connection_manager.mongo_client)
        self.contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.company_qualification_ai_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_COMPANY_QUALIFICATION_AI_PROCESSING]
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

        if selection_type == "all":
            await self.campaign_contact_runs_dao.update_campaign_contact_runs({"campaign_id": campaign_id}, {"$set": {"is_relevant": is_relevant}})
        else:
            chunk_size = 500
            for i in range(0, len(contact_ids), chunk_size):
                chunk = contact_ids[i:i + chunk_size]
                await self.campaign_contact_runs_dao.update_campaign_contact_runs(
                    {"campaign_id": campaign_id, "contact_id": {"$in": chunk}},
                    {"$set": {"is_relevant": is_relevant}}
                )
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
        total_company_runs_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True})
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
        campaign = await self.campaign_dao.get_campaign(campaign_id)
        
        if not campaign:
            raise ApiException("Campaign not found")
        synced_hubspot_companies_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True, "sync_to_hubspot_status": "synced"})
        total_hubspot_companies_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id), "is_relevant": True})


        serialized_campaign = serialize_objectid(campaign)
        return {
            "campaign": serialized_campaign,
            "synced_hubspot_companies_count": synced_hubspot_companies_count,
            "total_hubspot_companies_count": total_hubspot_companies_count,
            "campaign_id": campaign_id
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
        
        # Get all campaign_contact_runs with personalization approved
        filter_query = {
            "campaign_id": ObjectId(campaign_id),
            "personalization_status": "approved"
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
        
        enrolled_contacts = []
        for run in campaign_contact_runs:
            contact_id = run.get("contact_id")
            company_id = run.get("company_id")
            
            # Update contact run with enrollment info
            update_data = {
                "$set": {
                    "sequence_enrollment": {
                        "sequence_id": sequence_id,
                        "sequence_name": sequence_name,
                        "enrolled_at": datetime.utcnow(),
                        "status": "enrolled"
                    },
                    "metadata.updated_at": datetime.utcnow()
                }
            }
            
            await self.campaign_contact_runs_dao.update_campaign_contact_run(
                {"_id": run.get("_id")},
                update_data
            )
            
            # Get full contact data
            contact = await self.contacts_dao.get_contact(str(contact_id))
            company = await self.companies_dao.get_company(str(company_id)) if company_id else None
            
            # Build complete contact data for external service (Lemlist)
            contact_payload = {
                # Basic contact info
                "contact_id": str(contact_id),
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
            
            enrolled_contacts.append(contact_payload)
        
        # Update campaign status
        await self.campaign_dao.update_campaign(campaign_id, {
            "prospecting_cycle.status": "enrolled_to_sequence",
            "sequence_enrollment": {
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "enrolled_at": datetime.utcnow(),
                "enrolled_count": len(enrolled_contacts)
            }
        })
        
        return {
            "message": f"Successfully enrolled {len(enrolled_contacts)} contacts to sequence '{sequence_name}'",
            "campaign_id": campaign_id,
            "sequence_id": sequence_id,
            "sequence_name": sequence_name,
            "enrolled_count": len(enrolled_contacts),
            "enrolled_contacts": enrolled_contacts
        }


class CompaniesHelper:

    def __init__(self):
        self.company_service = CompanyService()
        self.contact_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
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