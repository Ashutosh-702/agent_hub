from datetime import datetime

from ai_agents.leadgen.schemas.ai_agents import LushaContactEnrichment, LushaGetContactEnrichment
from database.collection_dao.companies import CompaniesDao
from config.logging import logger
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from ai_agents.leadgen.services.ai_agents_service import CompanyService, ContactService
from ai_agents.leadgen.schemas.contact_models import ContactDocument
from ai_agents.leadgen.schemas.ai_agents import SaveProspectsDataToMongo
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from database.collection_dao.contacts import ContactsDao


class LushaContactEnrichmentHelper:

    def __init__(self):
        self.lusha_api_client = LushaAPIClient()
        self.company_service = CompanyService()
        self.contact_service = ContactService()
        self.companies_dao = CompaniesDao(
            loaded_config.connection_manager.mongo_client)

    async def lusha_get_contact_enrichment(self, query_params: LushaGetContactEnrichment):
        campaign_id = query_params.campaign_id
        company_map_list = query_params.company_map_list
        page = query_params.page
        page_size = query_params.page_size
        departments = query_params.departments

        if not campaign_id:
            raise ValueError("Campaign Id is required")

        company_names = []
        company_source_id_name_mappings = {}

        if company_map_list:
            for companies in company_map_list[:10]:
                company_id = companies.get("company_id", "")
                company_doc = await self.companies_dao.get_company(company_id)

                if not company_doc:
                    logger.error(f"Company not found: {company_id}")
                    continue

                company_name = company_doc.get(
                    "identifiers", {}).get("name", "")
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
                                "company_id": db_contact["company_id"],
                                "contact_id": contact_id
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
                contact_doc = {
                    "company_id": company_id,
                    "contact_data": {
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": prospect.get("email", ""),
                        "phone": prospect.get("phone_number", ""),
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
