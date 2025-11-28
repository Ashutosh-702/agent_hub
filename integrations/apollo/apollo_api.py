from typing import List, Dict, Any, Optional
from urllib.parse import quote

from structlog.contextvars import bind_contextvars
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from config.loaded_config import loaded_config
from config.logging import logger
from global_utils.exceptions import ApiException
from global_utils.constants import APOLLO_BASE_URL
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
        self.timeout = 30

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