from datetime import datetime

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
)
from kafkautils.producer.event_helpers import emit_event_helper
import uuid
import asyncio
from ai_agents.leadgen.schemas.ai_agents import Campaigns, Companies, CompanyContacts, ManualCompanyQualification
from ai_agents.leadgen.services.ai_agents_service import CampaignService
from ai_agents.leadgen.utils import serialize_objectid
from ai_agents.leadgen.schemas.ai_agents import CampaignDetailsWithCompanies
from database.collection_dao.campaigns import CampaignsDao
from ai_agents.leadgen.schemas.ai_agents import AiCompanyQualification, ApolloContactList, UpdateApolloContactEnrichmentStatus
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
        self.campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        self.campaign_contact_runs_dao = CampaignContactRunsDao(loaded_config.connection_manager.mongo_client)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.company_qualification_ai_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_COMPANY_QUALIFICATION_AI_PROCESSING]
        self.apollo_contact_list_kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_APOLLO_CONTACT_LIST_PROCESSING]

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

    async def get_campaign_details_with_companies(self, query_params: CampaignDetailsWithCompanies):
        campaign = await self.campaign_service.get_campaign_details(query_params.campaign_id)
        query = {}
        query["campaign_id"] = query_params.campaign_id
        if query_params.company_status != None:
            query["is_relevant"] = query_params.company_status
        companies, pagination_info = await self.campaign_company_runs_dao.get_campaign_company_runs_paginated(query, query_params.page, query_params.limit)
        serialized_campaign = serialize_objectid(campaign)
        serialized_companies = serialize_objectid(companies)
        return {"campaign": serialized_campaign, "companies": serialized_companies, "pagination_info": pagination_info}

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
        update_campaign = await self.campaign_dao.update_campaign(campaign_id, {"$set": {"prospecting_cycle.status": "company_qualification"}})
        if not update_campaign:
            raise ApiException("Campaign not found")
        return {"message": "Company qualification completed"}

    async def ai_company_qualification(self, query_params: AiCompanyQualification):
        campaign_id = query_params.campaign_id
        web_prompt = query_params.web_prompt

        if not web_prompt:
            raise ApiException("Web prompt is required")

        update_campaign = await self.campaign_dao.update_campaign(
            campaign_id,
            {"prompts.web": web_prompt, "metadata.updated_at": datetime.utcnow()},
        )
        request_id = str(uuid.uuid4())

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