from datetime import datetime

from ai_agents.leadgen.schemas.ai_agents import LushaContactEnrichment, LushaGetContactEnrichment
from database.collection_dao.companies import CompaniesDao
from config.logging import logger
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from ai_agents.leadgen.services.ai_agents_service import CompanyService, ContactService
from ai_agents.leadgen.schemas.contact_models import ContactDocument
from ai_agents.leadgen.schemas.ai_agents import SaveProspectsDataToMongo, ApolloContactEnrichment
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from database.collection_dao.contacts import ContactsDao
from global_utils.exceptions import ApiException
from integrations.apollo.apollo_helper import ApolloHelper
from kafkautils.constants import KAFKA_SERVICE_CONFIG_MAPPING, LeadgenServices, CONTACTS_ENRICHMENT
from kafkautils.producer.event_helpers import emit_event_helper
import uuid
import asyncio
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
        company_names = query_params.company_name
        person_seniorities = query_params.person_seniorities
        number_of_contacts_per_company = query_params.number_of_contacts_per_company
        company_id = "692439c9bbc59b1ac4d235bd"
        interested_product = query_params.interested_product

        if not company_id:
            raise ApiException("Company id is required")

        if not interested_product:
            raise ApiException("Interested product is required")

        if not company_names:
            raise ApiException("Company names are required")

        if not person_seniorities:
            raise ApiException("Person seniorities are required")

        if not number_of_contacts_per_company:
            raise ApiException("Number of contacts per company is required")
        contact_data = {}
        enriched_data = {}

        #============================================

        
        company_ids = []
        for company_name in company_names:
            company_doc = await self.company_dao.get_company_by_filters({"identifiers.source_name": company_name})
            if not company_doc:
                inserted_company_id = await self.company_dao.create_company({
                    "identifiers": {
                        "name": company_name,
                        "source_name": company_name
                    },
                    "source": "apollo",
                    "metadata": {
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                })
                company_ids.append(str(inserted_company_id))
            else:
                company_ids.append(str(company_doc["_id"]))

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_contacts_enrichment",
            "company_ids": company_ids, 
            "interested_product": interested_product,
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.kafka_config["topics"],
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "company_ids": company_ids, "interested_product": interested_product}
        )

        logger.info(f"company_ids: {company_ids}")
        logger.info(f"📤 Company Name {company_names} queued for processing: {request_id}")


        # for company_name in company_names:
        #     response = await self.apollo_helper.get_company_contacts(company_name, person_seniorities, page=1, per_page=number_of_contacts_per_company, enrich_contacts=True)
        #     if response.get('contacts'):
        #         contacts = response.get('contacts', [])
        #         for contact in contacts:
        #             contact_data = contact.get('contact_data')
        #             enriched_data = contact.get('enriched_data')
        #         return {contact_data: contact_data, enriched_data: enriched_data}
        #     else:
        #         raise ApiException(response.get('message'))

        return {"message": "All company contacts enriched", "company_ids": company_ids}