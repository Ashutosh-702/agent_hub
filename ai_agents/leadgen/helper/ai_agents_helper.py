from ai_agents.leadgen.schemas.ai_agents import LushaContactEnrichment
from database.collection_dao.companies import CompaniesDao
from config.logging import logger
from config.loaded_config import loaded_config
from integrations.lusha.lusha_api import LushaAPIClient
from ai_agents.leadgen.services.ai_agents_service import CompanyService, ContactService
from ai_agents.leadgen.schemas.contact_models import ContactDocument
from datetime import datetime
from bson import ObjectId


class LushaContactEnrichmentHelper:
    def __init__(self):
        self.lusha_api_client = LushaAPIClient()
        self.company_service = CompanyService()
        self.contact_service = ContactService()
        self.companies_dao = CompaniesDao(
            loaded_config.connection_manager.mongo_client)

    async def lusha_get_contact_enrichment(self, query_params: LushaContactEnrichment):
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
                    linkedin_url = data.get(
                        "socialLinks", {}).get("linkedin", "")
                    email_addresses = [e["email"] for e in data.get(
                        "emailAddresses", []) if "email" in e]
                    phone_numbers = [p["number"] for p in data.get(
                        "phoneNumbers", []) if "number" in p]

                    contact_dao = self.contact_service.contacts_dao
                    db_contacts = await contact_dao.get_contacts(
                        {
                            "linkedin_data.linkedin_url": linkedin_url
                        }
                    )

                    if db_contacts:
                        db_contact = db_contacts[0]
                        await self.contact_service.update_one(
                            {"_id": db_contact["_id"]},
                            {
                                "$set": {
                                    "contact_data.email": email_addresses,
                                    "contact_data.phone": phone_numbers,
                                    "metadata.updated_at": datetime.utcnow()
                                }
                            }
                        )
                    else:
                        firstname = data["firstName"]
                        lastname = data["lastName"]
                        job_title = data["jobTitle"]

                        contact_company_id = company_source_id_name_mappings.get(
                            data["companyName"], "")

                        if not contact_company_id:
                            print(
                                f"Company name not found in company_source_id_name_mappings: {data['companyName']}")
                            continue

                        contact_doc = {
                            "contact_data": {
                                "firstname": firstname,
                                "lastname": lastname,
                                "email": email_addresses,
                                "phone": phone_numbers,
                                "jobtitle": job_title,
                                "company": data["companyName"],
                                "company_id": ObjectId(contact_company_id)
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
                        print(f"contact_doc: {contact_doc}")

                        

        return