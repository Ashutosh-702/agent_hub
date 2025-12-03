from typing import Dict, Any, List, Optional, OrderedDict

from structlog.contextvars import bind_contextvars

from integrations.apollo.apollo_api import ApolloAPIClient
from config.logging import logger
from ai_agents.core_sdr.src.api.people_relevance_check import PeopleRelevanceCheck
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.companies import CompaniesDao
from config.loaded_config import loaded_config
from datetime import datetime, timezone
from bson import ObjectId
from integrations.apollo.schema import ApolloResponseSchema
from integrations.apollo.schema import SearchEnrichPeopleSchema
from integrations.apollo.schema import SearchPeopleSchema
from integrations.config.constants import MAX_EMPLOYEES, DOLLAR_TO_INR_RATIO, MILLION_TO_ACTUAL


class ApolloHelper:
    def __init__(self):
        config = {}
        self.people_relevance_check = PeopleRelevanceCheck(config)
        self.contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)

    async def get_company_contacts(self, query_params: ApolloResponseSchema) -> Dict[str, Any]:
 
        bind_contextvars(
            operation="apollo_get_company_contacts",
            component="apollo_helper",
            event_type="apollo_get_company_contacts"
        )

        logger.info(f"Getting contacts for company: {query_params.company_name}")

        # Step 1: Search for company to get organization ID
        logger.info(f"Step 1: Searching for company '{query_params.company_name}'...")
        # check company exists in the database .  filter is identifiers.source_id this field should exist. 
        company_doc = await self.companies_dao.get_company_by_filters({"identifiers.source_domain": query_params.company_domain,"identifiers.source_id": {"$exists": True}})
        organization_ids = []

        if company_doc:
            organization_ids.append(str(company_doc["identifiers"]["source_id"]))
        else:
            company_search_response = await self.search_companies(query_params.company_domain)

            if company_search_response.get('status_code') != 200:
                logger.error(f"Company search failed: {company_search_response}")
                return {
                    "status": "error",
                    "message": f"Failed to find company: {query_params.company_name}",
                    "company_name": query_params.company_name,
                    "contacts": []
                }
            else:
                organization_ids = self.extract_organization_ids(company_search_response)

        # Step 2: Extract organization IDs and update company details to databse
        if not organization_ids:
            logger.warning(f"No organization IDs found for company: {query_params.company_name}")

            return {
                "status": "error",
                "message": f"No organization IDs found for company: {query_params.company_name}",
                "company_name": query_params.company_name,
                "contacts": []
            }

        
        if not company_doc:
            await self.update_company_details_from_apollo(
                company_search_response=company_search_response,
                company_id=query_params.company_id
            )

        logger.info(f"Found {len(organization_ids)} organization ID(s): {organization_ids}")

        # Step 3: Search for people/contacts using organization IDs
        logger.info("Step 2: Searching for contacts...")
        
        # Create SearchPeopleSchema object
        search_params = SearchPeopleSchema(
            person_seniorities=query_params.person_seniorities,
            contact_email_status=query_params.contact_email_status,
            organization_ids=organization_ids,
            page=1,  # Start from page 1
            per_page=query_params.per_page,
            additional_params=query_params.additional_params
        )
        
        first_page_response = await self.search_people(query_params=search_params)

        if first_page_response.get('status_code') != 200:
            logger.error(f"People search failed: {first_page_response}")
            return {
                "status": "error",
                "message": "Failed to search for contacts",
                "company_name": query_params.company_name,
                "organization_ids": organization_ids,
                "contacts": []
            }

        search_results = first_page_response.get('results', {})
        total_entries = search_results.get('total_entries', 0)
        
        if total_entries == 0:
            logger.info("No contacts found")
            return {
                "status": "success",
                "message": "No contacts found",
                "company_name": query_params.company_name,
                "organization_ids": organization_ids,
                "contacts": []
            }

        
        total_entries = total_entries if total_entries < 100 else 30
        per_page = query_params.per_page or 10
        total_pages = (total_entries + per_page - 1) // per_page  # Ceiling division
        
        logger.info(f"Total entries: {total_entries}, Total pages: {total_pages}, Per page: {per_page}")
        
        # Process first page
        first_page_result = await self.process_page_of_contacts(
            people_search_response=first_page_response,
            query_params=query_params,
            organization_ids=organization_ids
        )
        
        all_stored_contact_ids = len(first_page_result.get("stored_contact_ids", [])) or 0
        total_contacts_processed = first_page_result.get("contacts_count", 0)

        for page in range(2, total_pages + 1):
            try:
                logger.info(f"Processing page {page} of {total_pages}...")

                contacts_count = await self.contacts_dao.get_contacts_count({
                    "company_id": ObjectId(query_params.company_id),
                    "contact_data.email": {"$ne": []}
                })
                if contacts_count > 0:
                    logger.info(f"Contacts already exist for company: {query_params.company_name} so not searching further")
                    break
                
                page_search_params = SearchPeopleSchema(
                    person_seniorities=query_params.person_seniorities,
                    contact_email_status=query_params.contact_email_status,
                    organization_ids=organization_ids,
                    page=page,
                    per_page=per_page,
                    additional_params=query_params.additional_params
                )
                
                page_response = await self.search_people(query_params=page_search_params)
                
                page_result = await self.process_page_of_contacts(
                    people_search_response=page_response,
                    query_params=query_params,
                    organization_ids=organization_ids
                )
                
                all_stored_contact_ids += (len(page_result.get("stored_contact_ids", [])) or 0)
                total_contacts_processed += page_result.get("contacts_count", 0)
                
            except Exception as e:
                logger.error(f"Error processing page {page}: {str(e)}")
                # Continue with next page even if one fails
                continue
            
        logger.info(f"✅ Successfully processed {total_contacts_processed} contacts across {total_pages} pages")

        
        return {
            "status": "success",
            "message": f"Retrieved {total_contacts_processed} contacts",
            "company_name": query_params.company_name,
            "company_id": query_params.company_id,
            "organization_ids": organization_ids,
            "stored_contact_ids": all_stored_contact_ids,
            "total_contacts": total_contacts_processed,
            "pagination": {
                "total_entries": total_entries,
                "total_pages": total_pages,
                "per_page": per_page
            }
        }

    async def enrich_and_store_contacts(
        self,
        people: List[Dict[str, Any]],
        query_params: 'ApolloResponseSchema'
    ) -> Dict[str, Any]:
        contacts = []
        stored_contact_ids = []

        if query_params.enrich_contacts:
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
                        reveal_personal_emails=query_params.reveal_personal_emails,
                        reveal_phone_number=query_params.reveal_phone_number
                    )

                    if enrichment_response.get('status_code') == 200:
                        enriched_data = enrichment_response.get('results', {})

                        try:
                            # Check if contact already exists
                            existing_contact_id = await self._check_existing_contact(
                                enriched_data=enriched_data,
                                company_id=query_params.company_id
                            )
                            
                            if existing_contact_id:
                                # Contact already exists, use existing ID
                                logger.info(f"Contact {person.get('name', 'Unknown')} already exists with ID: {existing_contact_id}")
                                stored_contact_ids.append(existing_contact_id)
                                contacts.append({
                                    "contact_data": person,
                                    "enriched_data": enriched_data,
                                    "contact_id": existing_contact_id
                                })
                            else:
                                # Contact doesn't exist, create new one
                                contact_doc = self.transform_apollo_contact_to_db_format(
                                    person_data=person,
                                    enriched_data=enriched_data,
                                    company_id=query_params.company_id
                                )
                                contact_id = await self.contacts_dao.create_contact(contact_doc)
                                logger.info(f"Stored new contact {person.get('name', 'Unknown')} with ID: {contact_id}")
                                stored_contact_ids.append(str(contact_id))
                                contacts.append({
                                    "contact_data": person,
                                    "enriched_data": enriched_data,
                                    "contact_id": str(contact_id)
                                })
                            
                        except Exception as e:
                            logger.error(f"Error storing contact {person_id} in database: {str(e)}")
                            # Still add to contacts even if storage failed
                            contacts.append({
                                "contact_data": person,
                                "enriched_data": enriched_data
                            })
                            continue
                    else:
                        # Include contact even if enrichment failed
                        logger.error(f"Failed to enrich contact {person_id}: {enrichment_response.get('error', 'Unknown error')}")
                        contacts.append({
                            "contact_data": person,
                            "enriched_data": None
                        })

                except Exception as e:
                    logger.error(f"Error enriching contact {person_id}: {str(e)}")
        else:
            # Return contacts without enrichment
            contacts = [{"contact_data": person, "enriched_data": None} for person in people]

        logger.info(f"Successfully retrieved {len(contacts)} contacts for company: {query_params.company_name}")

        return {
            "contacts": contacts,
            "stored_contact_ids": stored_contact_ids
        }

    async def filter_relevant_people(
        self,
        people: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter people based on relevance check
        
        Args:
            people: List of person data from Apollo search
            
        Returns:
            List of relevant people
        """
        relevant_people = []
        total_count = len(people)
        relevant_people_count = 0
        for person in people:
            try:
                if relevant_people_count >= 1:
                    logger.info(f"Found 1 relevant people - stopping relevance check")
                    break
                relevance_result = await self.people_relevance_check.web_search_analysis(person)
                relevance_assessment = relevance_result.get('relevance_assessment', {})
                is_relevant = relevance_assessment.get('is_relevant', False)

                if is_relevant:
                    relevant_people_count += 1
                    relevant_people.append(person)
                    logger.info(f"Person {person.get('name', 'Unknown')} is relevant - keeping in list")
                else:
                    logger.info(f"Person {person.get('name', 'Unknown')} is not relevant - removing from list")

            except Exception as e:
                logger.error(f"Error checking relevance for person {person.get('name', 'Unknown')}: {str(e)}")
                continue

        logger.info(f"After relevance check: {len(relevant_people)} relevant contacts out of {total_count} total")
        return relevant_people

    async def search_companies(self, company_domain: str) -> Dict[str, Any]:
        bind_contextvars(
            operation="apollo_search_companies",
            component="apollo_helper",
            event_type="apollo_company_search"
        )

        logger.info(f"Searching for companies with domain: {company_domain}")

        try:
            apollo_client = ApolloAPIClient()
            response = await apollo_client.apollo_organization_enrich_api(domain=company_domain)
            return response

        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            return {
                "status_code": 500,
                "error": str(e)
            }

    def extract_organization_ids(self, company_search_response: Dict[str, Any]) -> List[str]:
        organization_ids = []

        if company_search_response.get('status_code') != 200:
            logger.warning("Company search failed, cannot extract organization IDs")
            return organization_ids

        results = company_search_response.get('results', {})
        organization = results.get('organization', {})

        org_id = organization.get('id')


        if org_id:
                organization_ids.append(str(org_id))
        else:
            logger.warning("No organizations found in search results")
            return []

        logger.info(f"Extracted {len(organization_ids)} organization IDs")
        return organization_ids

    def build_search_payload(self, query_params: SearchPeopleSchema) -> Dict[str, Any]:

        payload = {
            "page": query_params.page,
            "per_page": query_params.per_page
        }

        if query_params.person_seniorities:
            payload["person_seniorities"] = query_params.person_seniorities

        if query_params.contact_email_status:
            payload["contact_email_status"] = query_params.contact_email_status

        if query_params.organization_ids:
            payload["organization_ids"] = query_params.organization_ids

        if query_params.additional_params:
            payload["additional_params"] = query_params.additional_params

        return payload

    async def search_people(self, query_params: SearchPeopleSchema) -> Dict[str, Any]:
        bind_contextvars(
            operation="apollo_search_people",
            component="apollo_helper",
            event_type="apollo_people_search"
        )

        payload = self.build_search_payload(query_params=query_params)

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
    
    async def _check_existing_contact(
        self, 
        enriched_data: Optional[Dict[str, Any]],
        company_id: str
    ) -> Optional[str]:

        if not self.contacts_dao:
            return None
        
        try:
            # Extract emails only from enriched_data (email is not in person_data)
            emails = []
            
            # Get emails from enriched_data only
            if enriched_data and enriched_data.get('person', {}).get('email'):
                enriched_emails = enriched_data['person']['email']
                if isinstance(enriched_emails, list):
                    emails.extend([e.get('address', '') if isinstance(e, dict) else e for e in enriched_emails if e])
                else:
                    emails.append(enriched_emails)
            
            # Remove duplicates and empty strings
            emails = list(set([e for e in emails if e and e.strip()]))
            
            if not emails:
                logger.info("No email found in enriched_data for duplicate check")
                return None
            
            # Check for existing contact by email
            existing_contact = await self.contacts_dao.get_contacts({
                "company_id": ObjectId(company_id),
                "contact_data.email": {"$in": emails}
            })
            
            if existing_contact:
                logger.info(f"Found existing contact by email: {emails[0]}")
                return str(existing_contact[0]['_id'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for existing contact: {str(e)}")
            return None
    
    def transform_apollo_contact_to_db_format(
        self, 
        person_data: Dict[str, Any], 
        enriched_data: Optional[Dict[str, Any]], 
        company_id: str
    ) -> Dict[str, Any]:

        # Extract contact data
        first_name = person_data.get('first_name') or (person_data.get('name', '').split()[0] if person_data.get('name') else '')
        last_name = person_data.get('last_name_obfuscated') 

        
        
        # Extract emails (handle both list and single string)
        emails = []
        phones = []

        if person_data.get('phone_numbers'):
           if isinstance(person_data['phone_numbers'], list):
               phones = person_data['phone_numbers']
           else:
               phones = [person_data['phone_numbers']]

        if person_data.get('email'):
            if isinstance(person_data['email'], list):
                emails = person_data['email']
            else:
                emails = [person_data['email']]
        
        # Extract enriched emails if available
        if enriched_data:
            enriched_person = enriched_data.get('person', {})
            enriched_emails = enriched_person.get('email', [])
            last_name = enriched_person.get('last_name', '')
            enriched_phones = enriched_person.get('phone_numbers', [])

            if enriched_emails:
                if isinstance(enriched_emails, list):
                    emails.extend([e.get('address', '') if isinstance(e, dict) else e for e in enriched_emails if e])
                else:
                    emails.append(enriched_emails)

            if enriched_phones:
                if isinstance(enriched_phones, list):
                    phones.extend([p.get('raw_number', '') or p.get('sanitized_number', '') if isinstance(p, dict) else p for p in enriched_phones if p])
                else:
                    phones.append(enriched_phones)
        
        # Remove duplicates and empty strings
        emails = list(set([e for e in emails if e]))
        
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
                "company": person_data.get('organization',{}).get('name'),
                "source_id": person_data.get('id') or (enriched_data.get('person', {}).get('id') if enriched_data else None),
            },
            "linkedin_data": {
                "linkedin_url": person_data.get('linkedin_url') or (enriched_data.get('person', {}).get('linkedin_url') if enriched_data else None),
                "source": "APOLLO-ENRICHER"
            },
            "webhook_sent": False,
            "metadata": {
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "raw_data": enriched_data
            }
        }
        
        return contact_doc

    def _transform_apollo_company_to_db_format(
        self,
        apollo_organization_data: Dict[str, Any],
        company_id: str
    ) -> Dict[str, Any]:

        # Extract organization details
        org_id = apollo_organization_data.get('id', '')
        org_name = apollo_organization_data.get('name', '')
        
        # Extract industry - handle both single and list formats
        industry = apollo_organization_data.get('industry', '')
        industries = apollo_organization_data.get('industries', [])
        if industries:
            industry = industries  # Use list if available
        elif industry:
            industry = [industry]  # Convert to list
        else:
            industry = []
        
        # Extract location/country
        country = apollo_organization_data.get('country', '')
        city = apollo_organization_data.get('city', '')
        state = apollo_organization_data.get('state', '')
        website = apollo_organization_data.get('website_url', '')
        
        # Build location name array
        location_names = []
        if country:
            location_names.append(country)
        
        # Extract revenue
        revenue = apollo_organization_data.get('annual_revenue') or apollo_organization_data.get('organization_revenue')
        revenue_min = None
        revenue_max = None
        if revenue:
            # Convert to millions for min/max
            revenue_millions = revenue / 1000000
            if revenue_millions < 50:
                revenue_min = "0"
                revenue_max = "50"
            elif revenue_millions < 100:
                revenue_min = "50"
                revenue_max = "100"
            elif revenue_millions < 500:
                revenue_min = "100"
                revenue_max = "500"
            else:
                revenue_min = "500"
                revenue_max = "1000"
        
        # Extract employee count
        estimated_employees = apollo_organization_data.get('estimated_num_employees', 0)
        employee_count = []
        if estimated_employees:
            if estimated_employees <= 10:
                employee_count = ["1-10"]
            elif estimated_employees <= 50:
                employee_count = ["11-50"]
            elif estimated_employees <= 200:
                employee_count = ["51-200"]
            elif estimated_employees <= 500:
                employee_count = ["201-500"]
            elif estimated_employees <= 1000:
                employee_count = ["501-1000"]
            else:
                employee_count = ["1001-5000"]
        
        # Build update document
        update_doc = {
            "$set": {
                "identifiers.source_id": str(org_id),
                "identifiers.name": org_name,
                "identifiers.website_url": website,
                "profile.industry": industry,
                "location.type": "country",
                "location.name": country,
                "source": "apollo",
                "metadata.updated_at": datetime.now(timezone.utc),
                "metadata.api_response": apollo_organization_data
            }
        }
        
        # Add revenue if available
        if revenue_min and revenue_max:
            update_doc["$set"]["profile.revenue_min"] = revenue_min
            update_doc["$set"]["profile.revenue_max"] = revenue_max
        
        # Add employee count if available
        if employee_count:
            update_doc["$set"]["profile.employee_count"] = employee_count
        
        return update_doc

    async def update_company_details_from_apollo(
        self,
        company_search_response: Dict[str, Any],
        company_id: str
    ) -> bool:

        if not self.companies_dao:
            logger.warning("CompaniesDao not initialized - cannot update company")
            return False
        
        try:
            if company_search_response.get('status_code') != 200:
                logger.warning("Company search failed, cannot update company details")
                return False
            
            results = company_search_response.get('results', {})
            organization = results.get('organization', {})
            
            if not organization or not organization.get('id'):
                logger.warning("No organization found in Apollo response")
                return False
            
            # Transform to database format
            update_doc = self._transform_apollo_company_to_db_format(
                apollo_organization_data=organization,
                company_id=company_id
            )
            
            # Update company in database
            result = await self.companies_dao.update_one(
                {"_id": ObjectId(company_id)},
                update_doc
            )
            
            if result > 0:
                logger.info(f"✅ Updated company details for company_id: {company_id} with Apollo organization data")
                return True
            else:
                logger.warning(f"⚠️ No company found with company_id: {company_id} to update")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating company details: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def process_page_of_contacts(
        self,
        people_search_response: Dict[str, Any],
        query_params: 'ApolloResponseSchema',
        organization_ids: List[str]
    ) -> Dict[str, Any]:
        if people_search_response.get('status_code') != 200:
            logger.error(f"People search failed: {people_search_response}")
            return {
                "status": "error",
                "message": "Failed to search for contacts",
                "contacts_count": 0,
                "stored_contact_ids": []
            }

        # Extract contacts from search results
        search_results = people_search_response.get('results', {})
        people = search_results.get('people', [])

        if not people:
            logger.info("No contacts found in this page")
            return {
                "status": "success",
                "message": "No contacts found",
                "contacts_count": 0,
                "stored_contact_ids": []
            }

        logger.info(f"Found {len(people)} contacts in this page")

        # Filter people based on relevance check
        people = await self.filter_relevant_people(people)

        # Enrich and store contacts
        enrichment_result = await self.enrich_and_store_contacts(people, query_params)
        contacts = enrichment_result["contacts"]
        stored_contact_ids = enrichment_result["stored_contact_ids"]

        return {
            "status": "success",
            "contacts_count": len(contacts),
            "stored_contact_ids": stored_contact_ids
        }

    

    





    def parse_employee_range(self, range_str: str) -> tuple:
        """
        Parse employee range strings like '11-50', '201+' to min/max values
        Returns tuple of (min, max) where max can be None for open-ended ranges
        """
        range_str = range_str.strip()

        if '+' in range_str:
            min_val = int(range_str.replace('+', '')) + 1
            return min_val, None

        elif '-' in range_str:
            parts = range_str.split('-')

            if len(parts) == 2:
                return int(parts[0]), int(parts[1])

        try:
            val = int(range_str)
            return val, val

        except:
            return 1, 10

    def convert_revenue_to_actual(self, revenue_millions: str, currency: str = "USD") -> int:
        """
        Convert revenue from millions to actual numbers
        """
        try:
            if currency == "INR":
                revenue_millions = float(revenue_millions) / DOLLAR_TO_INR_RATIO

            revenue_float = float(revenue_millions)
            actual = int(revenue_float * MILLION_TO_ACTUAL)

            return actual
        except:
            return 0

    def sheets_to_apollo_config(self, sheets_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert sheets configuration to Apollo API configuration
        """
        apollo_config = {
            "per_page": 25  # Default page size
        }

        # Employee ranges
        if sheets_data.get("target", {}).get("employee_count"):
            employee_ranges = [
                range_str for range_str in sheets_data['target']["employee_count"] if range_str
            ]

            if employee_ranges and employee_ranges[0] != "null":
                logger.info(f"employee_ranges: {employee_ranges}")
                org_employee_ranges = []

                for range_str in employee_ranges:
                    logger.info(f"range_value: {range_str}")
                    min_emp, max_emp = self.parse_employee_range(range_str)
                    range_dict = {"min": min_emp}
                    
                    if max_emp:
                        range_dict["max"] = max_emp
                    
                    # Format as "min,max" string for Apollo
                    range_str_formatted = f"{min_emp},{max_emp}" if max_emp else f"{min_emp},"
                    org_employee_ranges.append(range_str_formatted)

                logger.info(f"organization_num_employees_ranges: {org_employee_ranges}")
                apollo_config["organization_num_employees_ranges"] = org_employee_ranges

        # Locations (include)
        if sheets_data.get("target", {}).get("location", {}).get("names"):
            locations = sheets_data['target']["location"]['names']
            apollo_locations = []
            
            for location in locations:
                # Apollo expects location names as-is (e.g., "newyork", "tokyo")
                # Convert to lowercase and remove spaces for consistency
                location_clean = location.lower().replace(" ", "")
                apollo_locations.append(location_clean)

            if apollo_locations:
                apollo_config["organization_locations"] = apollo_locations

        # Revenue range
        revenue_min = sheets_data.get("target", {}).get("revenue_min")
        revenue_max = sheets_data.get("target", {}).get("revenue_max")
        currency = sheets_data.get("target", {}).get("currency")

        logger.info(f"revenue_min_check: {revenue_min}, revenue_max_check: {revenue_max}, currency: {currency}")
        
        if revenue_min and revenue_max:
            try:
                min_value = self._clean_tuple_value(revenue_min) 
                max_value = self._clean_tuple_value(revenue_max) 
                currency_value = self._clean_tuple_value(currency) 
                min_actual = self.convert_revenue_to_actual(min_value, currency_value)
                max_actual = self.convert_revenue_to_actual(max_value, currency_value)
                logger.info(f"min_actual: {min_actual}, max_actual: {max_actual}")

                if min_actual > 0 or max_actual > 0:
                    apollo_config["revenue_range"] = {
                        "min": min_actual if min_actual > 0 else 1,
                        "max": max_actual
                    }

            except Exception as e:
                logger.info(f"⚠️ Error processing revenue: {e}")

        # Keyword tags (from industry or other keywords)
        industry_names = sheets_data.get("segmentation", {}).get("industry", [])
        if industry_names:
            if not isinstance(industry_names, list):
                industry_names = [industry_names]
            
            # Convert industry names to keyword tags (lowercase, no spaces)
            keyword_tags = [name.lower().replace(" ", "") for name in industry_names if name]
            if keyword_tags:
                apollo_config["q_organization_keyword_tags"] = keyword_tags

        apollo_config["campaign_id"] = sheets_data.get("_id")
        logger.info(f"✅ Converted sheets config to Apollo config: {apollo_config}")

        return apollo_config

    async def get_companies_from_apollo(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main function to get companies from Apollo using sheets data
        """
        bind_contextvars(operation="get_companies_from_apollo", component="apollo_helper", event_type="apollo_company_search")
        apollo_config = self.sheets_to_apollo_config(config)
        logger.info(f"Apollo config: {apollo_config}")

        if not apollo_config or len(apollo_config) <= 1:
            logger.warning("❌ No valid Apollo configuration generated")
            return []

        try:
            apollo_api_client = ApolloAPIClient()
            companies = await apollo_api_client.apollo_collect_companies_from_search(apollo_config, config)
            logger.info(f"✅ Retrieved {companies} companies from Apollo")
            return companies

        except Exception as e:
            logger.error(f"❌ Error calling Apollo API: {e}")
            return []

    def _clean_tuple_value(self, value):
        """Clean tuple values from sheets data"""
        if value and isinstance(value, tuple) and len(value) > 0:
            return value[0]
            
        return value

