from typing import List, Dict, Any, Optional

from urllib.parse import quote
import urllib3

from structlog.contextvars import bind_contextvars
from urllib3.exceptions import InsecureRequestWarning

from config.loaded_config import loaded_config
from integrations.lusha.company_saver import CompanySaver
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from global_utils.constants import APOLLO_BASE_URL
from config.logging import logger
from global_utils.exceptions import ApiException

urllib3.disable_warnings(InsecureRequestWarning)


def format_apollo_query_params(params: Dict[str, Any]) -> str:
    """
    Format query parameters in Apollo's expected format with [] for arrays
    Example: person_seniorities[]=owner&person_seniorities[]=founder
    """
    query_parts = []
    
    for key, value in params.items():
        if isinstance(value, list):
            # Format arrays as key[]=value1&key[]=value2
            for item in value:
                query_parts.append(f"{key}[]={quote(str(item), safe='')}")
        else:
            query_parts.append(f"{key}={quote(str(value), safe='')}")
    
    return "&".join(query_parts)


class ApolloAPIClient:
    def __init__(self, payload_values: Optional[Dict[str, Any]] = None):
        self.api_key = loaded_config.apollo_api_key
        self.http_session = loaded_config.http_session
        self.headers = {
            'accept': 'application/json',
            'x-api-key': f"{self.api_key}",
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }
        self.payload_values = payload_values
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        self.company_saver = CompanySaver(self.companies_dao, self.campaign_company_runs_dao)
        self.timeout = 30

    async def apollo_search_api(self, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        """
        Search companies using Apollo API.
        
        Args:
            page: Page number (default: 1)
            per_page: Results per page (default: 25, max: 100)
        
        Returns:
            dict: Response data with status_code and results
        """
        # logger.info(f"Payload_values:", payload=self.payload_values)

        # Build query parameters
        query_params = self.build_query_params(page=page, per_page=per_page)
        # logger.info(f"Query Params:", payload=query_params)
        print(f"Query Params:", query_params)
        

        url = f"{APOLLO_BASE_URL}/mixed_companies/search"
        headers = self.headers

        # Apollo uses GET with query parameters, but the curl shows POST
        # Let's use POST as shown in the curl example
        response = await self.http_session.post(
            url, params=query_params, headers=headers, timeout=self.timeout
        )

        result = await response.json()
        response_data = {}
        response_data['status_code'] = response.status

        if response.status == 200:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Rate limit handling
            response_headers = dict(response.headers)
            response_data['rate_limit'] = True
            logger.warning(f"Rate limit exhausted for Apollo API")
            return response_data
            
        else:
            error_text = await response.text()
            logger.warning(f"Apollo Search API failed: {response.status} - {error_text}")

        return response_data

    def build_query_params(
        self,
        page: int = 1,
        per_page: int = 25
    ) -> Dict[str, Any]:
        """
        Build query parameters for Apollo API from payload values.
        
        Args:
            page: Page number
            per_page: Results per page
        
        Returns:
            dict: Query parameters dictionary
        """
        if not self.payload_values:
            return {"page": page, "per_page": per_page}

        query_params = {
            "page": page,
            "per_page": min(per_page, 100)  # Apollo max is 100
        }

        # Employee ranges
        employee_ranges = self.payload_values.get("organization_num_employees_ranges", [])
        if employee_ranges:
            for emp_range in employee_ranges:
                if isinstance(emp_range, dict) and "min" in emp_range and "max" in emp_range:
                    range_str = f"{emp_range['min']},{emp_range['max']}"
                    if "organization_num_employees_ranges[]" not in query_params:
                        query_params["organization_num_employees_ranges[]"] = []
                    query_params["organization_num_employees_ranges[]"].append(range_str)
                elif isinstance(emp_range, str):
                    if "organization_num_employees_ranges[]" not in query_params:
                        query_params["organization_num_employees_ranges[]"] = []
                    query_params["organization_num_employees_ranges[]"].append(emp_range)

        # Locations (include)
        locations = self.payload_values.get("organization_locations", [])
        if locations:
            for location in locations:
                if "organization_locations[]" not in query_params:
                    query_params["organization_locations[]"] = []
                query_params["organization_locations[]"].append(location)

        # Not locations (exclude)
        not_locations = self.payload_values.get("organization_not_locations", [])
        if not_locations:
            for location in not_locations:
                if "organization_not_locations[]" not in query_params:
                    query_params["organization_not_locations[]"] = []
                query_params["organization_not_locations[]"].append(location)

        # Revenue range
        revenue_range = self.payload_values.get("revenue_range", {})
        if revenue_range:
            if "min" in revenue_range:
                query_params["revenue_range[min]"] = revenue_range["min"]
            if "max" in revenue_range and revenue_range["max"] > 0:
                query_params["revenue_range[max]"] = revenue_range["max"]

        # Technology UIDs
        technology_uids = self.payload_values.get("currently_using_any_of_technology_uids", [])
        if technology_uids:
            for tech_uid in technology_uids:
                if "currently_using_any_of_technology_uids[]" not in query_params:
                    query_params["currently_using_any_of_technology_uids[]"] = []
                query_params["currently_using_any_of_technology_uids[]"].append(tech_uid)

        # Keyword tags
        keyword_tags = self.payload_values.get("q_organization_keyword_tags", [])
        if keyword_tags:
            for tag in keyword_tags:
                if "q_organization_keyword_tags[]" not in query_params:
                    query_params["q_organization_keyword_tags[]"] = []
                query_params["q_organization_keyword_tags[]"].append(tag)

        logger.info(f"Built query params: {query_params}")
        return query_params

    async def apollo_collect_companies_from_search(
        self,
        payload_values: Dict[str, Any],
        config: Dict[str, Any],
    ) -> int:
        """
        Collect companies from Apollo search API with pagination.
        
        Args:
            payload_values: Search parameters
            config: Campaign configuration
        
        Returns:
            int: Total number of companies inserted
        """
        total_inserted = 0
        self.payload_values = payload_values
        try:
            per_page = min(self.payload_values.get("per_page", 10), 100)
            per_page = 10
            rate_limit_hit = False

            # Step 1: Get first page to determine total results
            bind_contextvars(operation="apollo_company_search",
                             component="apollo_api_client", event_type="apollo_company_search")

            first_response = await self.apollo_search_api(page=1, per_page=per_page)

            if first_response.get('rate_limit'):
                logger.warning("First API call hit rate limit. Returning empty results.")
                return 0
                
            if first_response['status_code'] != 200 or "results" not in first_response:
                logger.warning("No data in first response. Returning empty results.")
                return 0

            # Process first page data
            page_companies = []
            results = first_response.get("results", {})
            organizations = results.get("organizations", [])

            for org in organizations:
                page_companies.append({
                    "id": str(org.get("id", "")),
                    "name": org.get("name", ""),
                    "api_response_metadata": org
                })

            # Insert first page
            if page_companies:
                inserted_count = await self.company_saver.insert_companies_batch_to_db(
                    page_companies, config, "apollo"
                )
                mappings_created = await self.company_saver.create_campaign_company_mappings_batch(
                    inserted_count['company_ids'], config.get("_id")
                )
                total_inserted += len(inserted_count['inserted_ids'])
                logger.info(f"📊 Page 1: Inserted {len(inserted_count['inserted_ids'])} companies")

            # Step 2: Calculate total pages needed
            pagination = results.get("pagination", {})
            total_results = pagination.get("total_entries", 0)
            # total_pages = pagination.get("total_pages", 1)

            total_pages = 1
            
            logger.info(f"Total pages: {total_pages}")

            # Step 3: Fetch remaining pages
            for page_num in range(2, total_pages + 1):
                logger.info(f"Fetching page {page_num} of {total_pages}")

                page_response = await self.apollo_search_api(page=page_num, per_page=per_page)

                if page_response.get('rate_limit'):
                    logger.info(f"Rate limit hit on page {page_num}.")
                    rate_limit_hit = True
                    break

                if page_response['status_code'] != 200 or "results" not in page_response:
                    logger.info(f"Failed to fetch page {page_num}")
                    break

                # Process page data
                page_results = page_response.get("results", {})
                page_organizations = page_results.get("organizations", [])
                page_companies = []

                for org in page_organizations:
                    page_companies.append({
                        "id": str(org.get("id", "")),
                        "name": org.get("name", ""),
                        "api_response_metadata": org
                    })

                # Insert page data
                if page_companies:
                    inserted_count = await self.company_saver.insert_companies_batch_to_db(
                        page_companies, config, "apollo"
                    )
                    total_inserted += len(inserted_count['inserted_ids'])

                    mappings_created = await self.company_saver.create_campaign_company_mappings_batch(
                        inserted_count['company_ids'], config.get("_id")
                    )
                    logger.info(f"📊 Page {page_num}: Inserted {len(inserted_count['inserted_ids'])} companies")

            if rate_limit_hit:
                logger.info(f"Collection completed with rate limiting. "
                            f"Collected {total_inserted} companies out of {total_results} total available.")
            else:
                logger.info(
                    f"Collection completed successfully. "
                    f"Collected {total_inserted} companies from {total_pages} pages.")

        except Exception as e:
            logger.error(f"Error searching companies: {str(e)}")
            raise Exception(f"Error searching companies: {str(e)}")
        finally:
            logger.info(f"Returning {total_inserted} companies")
            return total_inserted

    async def get_company_details(self, company_id: str) -> dict:
        """
        Get company details by ID.
        
        Args:
            company_id: Apollo company ID
        
        Returns:
            dict: Company details
        """
        url = f"{APOLLO_BASE_URL}/companies/{company_id}"
        headers = self.headers
        response = await self.http_session.get(url, headers=headers, timeout=self.timeout)
        
        if response.status != 200:
            raise ApiException(f"Failed to get company details: {response.status}")
        
        return await response.json()
    
    async def get_company_details_by_name(self, company_name: str) -> dict:
        """
        Search company by name.
        
        Args:
            company_name: Company name to search
        
        Returns:
            dict: Search results
        """
        url = f"{APOLLO_BASE_URL}/mixed_companies/search"
        headers = self.headers
        params = {
            "q_keywords": company_name,
            "page": 1,
            "per_page": 10
        }
        
        response = await self.http_session.post(url, params=params, headers=headers, timeout=self.timeout)
        
        if response.status != 200:
            raise ApiException(f"Failed to search company: {response.status}")
        
        return await response.json()

    async def apollo_company_search_api(
        self,
        organization_name: str
    ) -> Dict[str, Any]:
        """
        Search for companies by organization name using Apollo API
        Args:
            organization_name: Name of the organization to search for
        Returns: Response data with status code and results
        """
        bind_contextvars(
            operation="apollo_company_search",
            component="apollo_api_client",
            event_type="apollo_company_search"
        )
        logger.info(f"Searching for company: {organization_name}")

        # Build query parameters
        query_params = {
            "q_organization_name": organization_name
        }

        url = f"{APOLLO_BASE_URL}/mixed_companies/search?{format_apollo_query_params(query_params)}"

        response = await self.http_session.post(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = await response.json()
        response_data = {
            'status_code': response.status
        }

        if response.status == 200:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Rate limit hit
            response_headers = dict(response.headers)
            response_data['rate_limit_info'] = response_headers
            logger.warning(f"Rate limit exhausted: {response.status}")
            return response_data

        else:
            error_text = await response.text()
            logger.warning(f"Company search API failed: {response.status} - {error_text}")
            response_data['error'] = error_text
            return response_data

    async def apollo_people_search_api(self) -> Dict[str, Any]:
        """
        Search for people using Apollo API
        Returns: Response data with status code and results
        """
        bind_contextvars(
            operation="apollo_people_search",
            component="apollo_api_client",
            event_type="apollo_people_search"
        )
        logger.info(f"Payload_values:", payload=self.payload_values)

        # Build query parameters from payload
        query_params = self.build_search_query_params(
            payload_values=self.payload_values,
        )
        logger.info(f"Query params:", payload=query_params)

        # Construct URL with query parameters
        url = f"{APOLLO_BASE_URL}/mixed_people/api_search"
        if query_params:
            url = f"{url}?{format_apollo_query_params(query_params)}"

        response = await self.http_session.post(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = await response.json()
        response_data = {
            'status_code': response.status
        }

        if response.status == 200:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Rate limit hit
            response_headers = dict(response.headers)
            response_data['rate_limit_info'] = response_headers
            logger.warning(f"Rate limit exhausted: {response.status}")
            return response_data

        else:
            error_text = await response.text()
            logger.warning(f"People search API failed: {response.status} - {error_text}")
            response_data['error'] = error_text
            return response_data

    def build_search_query_params(
        self,
        payload_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        query_params = {}

        # Handle person_seniorities
        person_seniorities = payload_values.get("person_seniorities", [])
        if person_seniorities:
            query_params["person_seniorities"] = person_seniorities

        # Handle contact_email_status
        contact_email_status = payload_values.get("contact_email_status", [])
        if contact_email_status:
            query_params["contact_email_status"] = contact_email_status

        # Handle organization_ids
        organization_ids = payload_values.get("organization_ids", [])
        if organization_ids:
            query_params["organization_ids"] = organization_ids

        # Handle pagination
        page = payload_values.get("page", 1)
        per_page = payload_values.get("per_page", 10)
        query_params["page"] = page
        query_params["per_page"] = per_page

        # Add any additional query parameters from payload
        additional_params = payload_values.get("additional_params", {})

        for key, value in additional_params.items():
            query_params[key] = value

        return query_params

    async def apollo_people_enrichment_api(
        self,
        person_id: str,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False
    ) -> Dict[str, Any]:
        bind_contextvars(
            operation="apollo_people_enrichment",
            component="apollo_api_client",
            event_type="apollo_people_enrichment"
        )
        logger.info(f"Enriching person with ID: {person_id}")

        # Build query parameters
        query_params = {
            "id": person_id,
            "reveal_personal_emails": str(reveal_personal_emails).lower(),
            "reveal_phone_number": str(reveal_phone_number).lower()
        }

        url = f"{APOLLO_BASE_URL}/people/match?{format_apollo_query_params(query_params)}"

        response = await self.http_session.post(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = await response.json()
        response_data = {
            'status_code': response.status
        }

        if response.status == 200:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Rate limit hit
            response_headers = dict(response.headers)
            response_data['rate_limit_info'] = response_headers
            logger.warning(f"Rate limit exhausted: {response.status}")
            return response_data

        else:
            error_text = await response.text()
            logger.warning(f"People enrichment API failed: {response.status} - {error_text}")
            response_data['error'] = error_text
            return response_data

    async def apollo_organization_enrich_api(
        self,
        domain: str
    ) -> Dict[str, Any]:
        """
        Enrich organization by domain using Apollo API
        Args:
            domain: Domain name of the organization (e.g., 'superdry.in')
        Returns: Response data with status code and organization data
        """
        bind_contextvars(
            operation="apollo_organization_enrich",
            component="apollo_api_client",
            event_type="apollo_organization_enrich"
        )
        logger.info(f"Enriching organization by domain: {domain}")

        # Build query parameters
        query_params = {
            "domain": domain
        }

        url = f"{APOLLO_BASE_URL}/organizations/enrich?{format_apollo_query_params(query_params)}"

        # Use GET instead of POST
        response = await self.http_session.get(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = await response.json()
        response_data = {
            'status_code': response.status
        }

        if response.status == 200:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Rate limit hit
            response_headers = dict(response.headers)
            response_data['rate_limit_info'] = response_headers
            logger.warning(f"Rate limit exhausted: {response.status}")
            return response_data

        else:
            error_text = await response.text()
            logger.warning(f"Organization enrich API failed: {response.status} - {error_text}")
            response_data['error'] = error_text
            return response_data