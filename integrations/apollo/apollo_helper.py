from typing import Dict, Any, List, Optional

from structlog.contextvars import bind_contextvars

from integrations.apollo.apollo_api import ApolloAPIClient
from config.logging import logger
from ai_agents.core_sdr.src.api.people_relevance_check import PeopleRelevanceCheck
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.companies import CompaniesDao
from config.loaded_config import loaded_config
from datetime import datetime, timezone
from bson import ObjectId


class ApolloHelper:
    def __init__(self):
        config = {}
        self.people_relevance_check = PeopleRelevanceCheck(config)
        self.contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)

    async def get_company_contacts(
        self,
        company_name: str,
        company_id: str,
        person_seniorities: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 10,
        enrich_contacts: bool = False,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
 
        bind_contextvars(
            operation="apollo_get_company_contacts",
            component="apollo_helper",
            event_type="apollo_get_company_contacts"
        )

        logger.info(f"Getting contacts for company: {company_name}")

        # Step 1: Search for company to get organization ID
        logger.info(f"Step 1: Searching for company '{company_name}'...")
        company_search_response = await self.search_companies(company_name)

        if company_search_response.get('status_code') != 200:
            logger.error(f"Company search failed: {company_search_response}")
            return {
                "status": "error",
                "message": f"Failed to find company: {company_name}",
                "company_name": company_name,
                "contacts": []
            }

        # Step 2: Extract organization IDs
        organization_ids = self.extract_organization_ids(company_search_response)

        if not organization_ids:
            logger.warning(f"No organization IDs found for company: {company_name}")
            return {
                "status": "error",
                "message": f"No organization IDs found for company: {company_name}",
                "company_name": company_name,
                "contacts": []
            }

        logger.info(f"Found {len(organization_ids)} organization ID(s): {organization_ids}")

        # Step 3: Search for people/contacts using organization IDs
        logger.info("Step 2: Searching for contacts...")
        people_search_response = await self.search_people(
            person_seniorities=person_seniorities,
            contact_email_status=contact_email_status,
            organization_ids=organization_ids,
            page=page,
            per_page=per_page,
            additional_params=additional_params
        )

        if people_search_response.get('status_code') != 200:
            logger.error(f"People search failed: {people_search_response}")
            return {
                "status": "error",
                "message": "Failed to search for contacts",
                "company_name": company_name,
                "organization_ids": organization_ids,
                "contacts": []
            }

        # Step 4: Extract contacts from search results
        search_results = people_search_response.get('results', {})
        people = search_results.get('people', [])

        if not people:
            logger.info("No contacts found")
            return {
                "status": "success",
                "message": "No contacts found",
                "company_name": company_name,
                "organization_ids": organization_ids,
                "contacts": []
            }

        logger.info(f"Found {len(people)} contacts")


        #relevance check for each contact if false remove that  person from the list
        relevant_people = []
        for person in people:
            try:
                relevance_result = await self.people_relevance_check.web_search_analysis(person)
                relevance_assessment = relevance_result.get('relevance_assessment', {})
                is_relevant = relevance_assessment.get('is_relevant', False)
                if not is_relevant:
                    relevant_people.append(person)
                    logger.info(f"Person {person.get('name', 'Unknown')} is relevant - keeping in list")
                else:
                    logger.info(f"Person {person.get('name', 'Unknown')} is not relevant - removing from list")
            except Exception as e:
                logger.error(f"Error checking relevance for person {person.get('name', 'Unknown')}: {str(e)}")
                continue

        people = relevant_people
        logger.info(f"After relevance check: {len(people)} relevant contacts out of {len(people) + (len(people) - len(relevant_people))} total")

        # Step 6: Optionally enrich contacts
        contacts = []
        stored_contact_ids = []
        if enrich_contacts:
            logger.info("Step 3: Enriching contacts...")
            apollo_client = ApolloAPIClient()

            for person in people:
                person_id = person.get('id')
                if not person_id:
                    # Include contact even if no ID for enrichment
                    contacts.append({
                        "contact_data": person,
                        "enriched_data": None
                    })
                    continue

                try:
                    enrichment_response = await apollo_client.apollo_people_enrichment_api(
                        person_id=str(person_id),
                        reveal_personal_emails=reveal_personal_emails,
                        reveal_phone_number=reveal_phone_number
                    )

                    if enrichment_response.get('status_code') == 200:
                        enriched_data = enrichment_response.get('results', {})

                        try:
                            contact_doc = self.transform_apollo_contact_to_db_format(
                                    person_data=person,
                                    enriched_data=enriched_data,
                                    company_id=company_id
                                )
                            contact_id = await self.contacts_dao.create_contact(contact_doc)
                            logger.info(f"Stored contact {person.get('name', 'Unknown')} with ID: {contact_id}")
                            stored_contact_ids.append(str(contact_id))
                        except Exception as e:
                            logger.error(f"Error storing contact {person_id} in database: {str(e)}")
                            continue
                    else:
                        # Include contact even if enrichment failed
                        logger.error(f"Failed to enrich contact {person_id}: {enrichment_response.get('error', 'Unknown error')}")

                except Exception as e:
                    logger.error(f"Error enriching contact {person_id}: {str(e)}")
                    logger.error(f"Failed to enrich contact {person_id}: {str(e)}")
        else:
            # Return contacts without enrichment
            contacts = [{"contact_data": person, "enriched_data": None} for person in people]

        logger.info(f"Successfully retrieved {len(contacts)} contacts for company: {company_name}")

        return {
            "status": "success",
            "message": f"Retrieved {len(contacts)} contacts",
            "company_name": company_name,
            "organization_ids": organization_ids,
            "stored_contact_ids": stored_contact_ids,
            "total_contacts": len(contacts),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": search_results.get('pagination', {}).get('total_pages', 1)
            }
        }

    async def search_companies(
        self,
        organization_name: str
    ) -> Dict[str, Any]:
        """
        Search for companies by organization name
        Args:
            organization_name: Name of the organization to search for
        Returns: Search results with company data including organization IDs
        """
        bind_contextvars(
            operation="apollo_search_companies",
            component="apollo_helper",
            event_type="apollo_company_search"
        )

        logger.info(f"Searching for companies with name: {organization_name}")

        try:
            apollo_client = ApolloAPIClient()
            response = await apollo_client.apollo_company_search_api(
                organization_name=organization_name
            )
            return response

        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            return {
                "status_code": 500,
                "error": str(e)
            }

    def extract_organization_ids(
        self,
        company_search_response: Dict[str, Any]
    ) -> List[str]:
        """
        Extract organization IDs from company search results
        Args:
            company_search_response: Response from company search API
        Returns: List of organization IDs
        """
        organization_ids = []

        if company_search_response.get('status_code') != 200:
            logger.warning("Company search failed, cannot extract organization IDs")
            return organization_ids

        results = company_search_response.get('results', {})
        organizations = results.get('organizations', [])
        #only take the first organization
        org_id = organizations[0].get('id')
        if org_id:
            organization_ids.append(str(org_id))

        logger.info(f"Extracted {len(organization_ids)} organization IDs")
        return organization_ids

    async def search_companies_and_get_organization_ids(
        self,
        organization_names: List[str]
    ) -> List[str]:

        all_organization_ids = []

        for org_name in organization_names:
            try:
                search_response = await self.search_companies(org_name)
                org_ids = self.extract_organization_ids(search_response)
                all_organization_ids.extend(org_ids)
            except Exception as e:
                logger.error(f"Error processing organization {org_name}: {e}")
                continue

        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(all_organization_ids))
        logger.info(f"Found {len(unique_ids)} unique organization IDs from {len(organization_names)} searches")
        return unique_ids

    def build_search_payload(
        self,
        person_seniorities: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        organization_ids: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 10,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        payload = {
            "page": page,
            "per_page": per_page
        }

        if person_seniorities:
            payload["person_seniorities"] = person_seniorities

        if contact_email_status:
            payload["contact_email_status"] = contact_email_status

        if organization_ids:
            payload["organization_ids"] = organization_ids

        if additional_params:
            payload["additional_params"] = additional_params

        return payload

    async def search_people(
        self,
        person_seniorities: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        organization_ids: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 10,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        bind_contextvars(
            operation="apollo_search_people",
            component="apollo_helper",
            event_type="apollo_people_search"
        )

        payload = self.build_search_payload(
            person_seniorities=person_seniorities,
            contact_email_status=contact_email_status,
            organization_ids=organization_ids,
            page=page,
            per_page=per_page,
            additional_params=additional_params
        )

        logger.info(f"Searching people with payload: {payload}")

        try:
            apollo_client = ApolloAPIClient(payload_values=payload)
            response = await apollo_client.apollo_people_search_api()
            return response

        except Exception as e:
            logger.error(f"Error searching people: {e}")
            return {
                "status_code": 500,
                "error": str(e)
            }

    async def enrich_person(
        self,
        person_id: str,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False
    ) -> Dict[str, Any]:

        bind_contextvars(
            operation="apollo_enrich_person",
            component="apollo_helper",
            event_type="apollo_people_enrichment"
        )

        logger.info(f"Enriching person with ID: {person_id}")

        try:
            apollo_client = ApolloAPIClient()
            response = await apollo_client.apollo_people_enrichment_api(
                person_id=person_id,
                reveal_personal_emails=reveal_personal_emails,
                reveal_phone_number=reveal_phone_number
            )
            return response

        except Exception as e:
            logger.error(f"Error enriching person: {e}")
            return {
                "status_code": 500,
                "error": str(e)
            }

    async def search_and_enrich_people(
        self,
        person_seniorities: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        organization_ids: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 10,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
       
        bind_contextvars(
            operation="apollo_search_and_enrich",
            component="apollo_helper",
            event_type="apollo_search_and_enrich"
        )

        # Step 1: Search for people
        search_response = await self.search_people(
            person_seniorities=person_seniorities,
            contact_email_status=contact_email_status,
            organization_ids=organization_ids,
            page=page,
            per_page=per_page,
            additional_params=additional_params
        )

        if search_response.get('status_code') != 200:
            logger.warning(f"Search failed: {search_response}")
            return {
                "search_response": search_response,
                "enriched_results": []
            }

        # Step 2: Extract person IDs from search results
        search_results = search_response.get('results', {})
        people = search_results.get('people', [])

        if not people:
            logger.info("No people found in search results")
            return {
                "search_response": search_response,
                "enriched_results": []
            }

        # Step 3: Enrich each person
        person_ids = []
        for person in people:
            person_id = person.get('id')
            if person_id:
                person_ids.append(str(person_id))

        logger.info(f"Found {len(person_ids)} people to enrich")

        enriched_results = []
        apollo_client = ApolloAPIClient()

        for person_id in person_ids:
            try:
                enrichment_response = await apollo_client.apollo_people_enrichment_api(
                    person_id=person_id,
                    reveal_personal_emails=reveal_personal_emails,
                    reveal_phone_number=reveal_phone_number
                )

                if enrichment_response.get('status_code') == 200:
                    enriched_results.append(enrichment_response.get('results', {}))
                else:
                    logger.warning(f"Failed to enrich person {person_id}")

            except Exception as e:
                logger.error(f"Error enriching person {person_id}: {str(e)}")
                continue

        return {
            "search_response": search_response,
            "enriched_results": enriched_results,
            "total_found": len(people),
            "total_enriched": len(enriched_results)
        }

    async def complete_apollo_workflow(
        self,
        organization_names: List[str],
        person_seniorities: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 10,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        bind_contextvars(
            operation="apollo_complete_workflow",
            component="apollo_helper",
            event_type="apollo_complete_workflow"
        )

        logger.info(f"Starting complete Apollo workflow for organizations: {organization_names}")

        # Step 1: Search for companies and get organization IDs
        logger.info("Step 1: Searching for companies...")
        organization_ids = await self.search_companies_and_get_organization_ids(organization_names)

        if not organization_ids:
            logger.warning("No organization IDs found. Cannot proceed with people search.")
            return {
                "status": "error",
                "message": "No organization IDs found from company search",
                "organization_ids": [],
                "search_response": None,
                "enriched_results": []
            }

        logger.info(f"Found {len(organization_ids)} organization IDs: {organization_ids}")

        # Step 2: Search for people using organization IDs
        logger.info("Step 2: Searching for people...")
        search_response = await self.search_people(
            person_seniorities=person_seniorities,
            contact_email_status=contact_email_status,
            organization_ids=organization_ids,
            page=page,
            per_page=per_page,
            additional_params=additional_params
        )

        if search_response.get('status_code') != 200:
            logger.warning(f"People search failed: {search_response}")
            return {
                "status": "error",
                "message": "People search failed",
                "organization_ids": organization_ids,
                "search_response": search_response,
                "enriched_results": []
            }

        # Step 3: Extract person IDs and enrich them
        logger.info("Step 3: Enriching people...")
        search_results = search_response.get('results', {})
        people = search_results.get('people', [])

        if not people:
            logger.info("No people found in search results")
            return {
                "status": "success",
                "message": "No people found",
                "organization_ids": organization_ids,
                "search_response": search_response,
                "enriched_results": []
            }

        # Extract person IDs
        person_ids = []
        for person in people:
            person_id = person.get('id')
            if person_id:
                person_ids.append(str(person_id))

        logger.info(f"Found {len(person_ids)} people to enrich")

        # Enrich each person
        enriched_results = []
        apollo_client = ApolloAPIClient()

        for person_id in person_ids:
            try:
                enrichment_response = await apollo_client.apollo_people_enrichment_api(
                    person_id=person_id,
                    reveal_personal_emails=reveal_personal_emails,
                    reveal_phone_number=reveal_phone_number
                )

                if enrichment_response.get('status_code') == 200:
                    enriched_results.append(enrichment_response.get('results', {}))
                else:
                    logger.warning(f"Failed to enrich person {person_id}")

            except Exception as e:
                logger.error(f"Error enriching person {person_id}: {str(e)}")
                continue

        logger.info(f"Workflow completed. Enriched {len(enriched_results)} out of {len(person_ids)} people")

        return {
            "status": "success",
            "message": "Complete workflow executed successfully",
            "organization_ids": organization_ids,
            "search_response": search_response,
            "enriched_results": enriched_results,
            "total_organizations_found": len(organization_ids),
            "total_people_found": len(people),
            "total_enriched": len(enriched_results)
        }

    def transform_apollo_contact_to_db_format(
        self, 
        person_data: Dict[str, Any], 
        enriched_data: Optional[Dict[str, Any]], 
        company_id: str
    ) -> Dict[str, Any]:

        # Extract contact data
        first_name = person_data.get('first_name') or (person_data.get('name', '').split()[0] if person_data.get('name') else '')
        last_name = person_data.get('last_name') or (' '.join(person_data.get('name', '').split()[1:]) if person_data.get('name') and len(person_data.get('name', '').split()) > 1 else '')
        
        # Extract emails (handle both list and single string)
        emails = []
        if person_data.get('email'):
            if isinstance(person_data['email'], list):
                emails = person_data['email']
            else:
                emails = [person_data['email']]
        
        # Extract enriched emails if available
        if enriched_data:
            enriched_person = enriched_data.get('person', {})
            enriched_emails = enriched_person.get('email', [])
            if enriched_emails:
                if isinstance(enriched_emails, list):
                    emails.extend([e.get('address', '') if isinstance(e, dict) else e for e in enriched_emails if e])
                else:
                    emails.append(enriched_emails)
        
        # Remove duplicates and empty strings
        emails = list(set([e for e in emails if e]))
        
        # Extract phone numbers
        phones = []
        if person_data.get('phone_numbers'):
            if isinstance(person_data['phone_numbers'], list):
                phones = person_data['phone_numbers']
            else:
                phones = [person_data['phone_numbers']]
        
        # Extract enriched phone numbers if available
        if enriched_data:
            enriched_person = enriched_data.get('person', {})
            enriched_phones = enriched_person.get('phone_numbers', [])
            if enriched_phones:
                if isinstance(enriched_phones, list):
                    phones.extend([p.get('raw_number', '') or p.get('sanitized_number', '') if isinstance(p, dict) else p for p in enriched_phones if p])
                else:
                    phones.append(enriched_phones)
        
        # Remove duplicates and empty strings
        phones = list(set([p for p in phones if p]))
        
        # Build contact document
        contact_doc = {
            "company_id": ObjectId(company_id),
            "contact_data": {
                "firstname": first_name,
                "lastname": last_name,
                "email": emails,
                "phone": phones,
                "jobtitle": person_data.get('title') or (enriched_data.get('person', {}).get('title') if enriched_data else None),
                "company": person_data.get('organization_name') or person_data.get('source_organization_name') or ''
            },
            "linkedin_data": {
                "linkedin_url": person_data.get('linkedin_url') or (enriched_data.get('person', {}).get('linkedin_url') if enriched_data else None),
                "source": "APOLLO-ENRICHER"
            },
            "metadata": {
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "raw_data": enriched_data.get('person', {})
            }
        }
        
        return contact_doc

    

