from typing import List, Dict, Any, Optional

from structlog.contextvars import bind_contextvars
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from config.loaded_config import loaded_config
from global_utils.chronos_utils import (
    schedule_lusha_company_collection,
    generate_default_eta_expression
)
from ai_agents.core_sdr.src.parsers.constants import COMPANY_GROUPINGS
from integrations.lusha.company_saver import CompanySaver
from database.factory import (
    get_companies_dao,
    get_campaign_company_runs_dao,
)
from integrations.config.lusha_department_mapper import DEPARTMENT_TO_CATEGORY
from global_utils.constants import LUSHA_BASE_URL
from config.logging import logger
from global_utils.exceptions import ApiException

urllib3.disable_warnings(InsecureRequestWarning)


class LushaAPIClient:
    def __init__(self, payload_values: Optional[Dict[str, Any]] = None):
        self.api_key = loaded_config.lusha_api_key
        self.http_session = loaded_config.http_session
        self.headers = {
            'accept': 'application/json',
            "api_key": f"{self.api_key}",
            'Content-Type': 'application/json'
        }
        self.payload_values = payload_values
        # Use DAO factory for database-agnostic access (supports both MongoDB and PostgreSQL)
        self.companies_dao = get_companies_dao(loaded_config.connection_manager)
        self.campaign_company_runs_dao = get_campaign_company_runs_dao(loaded_config.connection_manager)
        self.company_saver = CompanySaver(self.companies_dao, self.campaign_company_runs_dao)
        self.timeout = 30

    async def lusha_search_api(self) -> List[int]:
        logger.info(f"Payload_values:", payload=self.payload_values)

        payload_query = self.build_payload(
            payload_values=self.payload_values,
        )
        logger.info(f"Payload Query:", payload=payload_query)

        url = f"{LUSHA_BASE_URL}/prospecting/company/search"
        headers = self.headers

        response = await self.http_session.post(
            url,  json=payload_query, headers=headers, 
            timeout=self.timeout
        )

        result = await response.json()
        response_data = {}
        response_data['status_code'] = response.status

        if response.status == 201:
            response_data['results'] = result
            return response_data

        elif response.status == 429:
            # Return None to indicate rate limit exhaustion rather than raising exception
            response_headers = dict(response.headers)
            response_data['daily_left'] = response_headers.get('x-daily-requests-left', None)
            response_data['hourly_left'] = response_headers.get('x-hourly-requests-left', None)
            response_data['minute_left'] = response_headers.get('x-minute-requests-left', None)

            logger.info(f"Daily left: {response_data['daily_left']}, "
                        f"Hourly left: {response_data['hourly_left']}, "
                        f"Minute left: {response_data['minute_left']}")
            logger.warning(f"Rate limit exhausted")

            return response_data
            
        else:
            error_text = await response.text()
            logger.warning(f"Search API failed: {response.status} - {error_text}")

        return None

    def build_payload(
        self,
        payload_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the API payload from input values."""
        pages = payload_values.get("pages", {})
        page = pages.get("page", 0)
        page_size = pages.get("size", payload_values.get("page_size", 40))
        main_industries = payload_values.get("mainIndustriesIds", [])
        sub_industries = payload_values.get("subIndustriesIds", [])
        locations = payload_values.get("locations", [])
        location_type = payload_values.get("location_type", "")
        revenue = payload_values.get("revenue", {})
        sizes = payload_values.get("sizes", [])

        payload_query = {
            "pages": {
                "page": page,
                "size": page_size
            },
            "filters": {
                "companies": {
                    "include": {},
                    "exclude": {}
                }
            }
        }
        include_data = payload_query["filters"]["companies"]["include"]
        exclude_data = payload_query["filters"]["companies"]["exclude"]

        logger.info(f"payload_values: {payload_values}")

        # if cached_data:
        #     exclude_data["names"] = [company['name'] for company in cached_data]

        if main_industries:
            include_data["mainIndustriesIds"] = main_industries

        if sub_industries:
            include_data["subIndustriesIds"] = sub_industries

        if locations:

            if location_type == "region":
                include_data["locations"] = []

                for region in locations:
                    if region in COMPANY_GROUPINGS:
                        include_data["locations"].append(
                            {"country_grouping": COMPANY_GROUPINGS[region]})

                    else:
                        include_data["locations"].append({"continent": region})

            else:
                include_data["locations"] = [
                    {"country": country} for country in locations]

        if revenue:
            if "min" in revenue and "max" in revenue:
                include_data["revenues"] = [
                    {
                        "min": revenue["min"],
                        "max": revenue["max"]
                    }
                ]

        if sizes:
            include_data["sizes"] = sizes

        return payload_query

    async def lusha_collect_companies_from_search(
        self,
        payload_values: Dict[str, Any],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        total_inserted = 0
        self.payload_values = payload_values
        try:

            page_size = self.payload_values.get("pages", {}).get("size", 20)
            rate_limit_hit = False

            # Step 1: Get first page to determine total results
            initial_payload = self.payload_values.copy()
            initial_payload["pages"] = {"page": 0, "size": page_size}
            bind_contextvars(operation="lusha_company_search",
                             component="lusha_api_client", event_type="lusha_company_search")

            first_response = await self.lusha_search_api()

            if first_response['status_code'] == 429:
                logger.warning("First API call failed or hit rate limit. Returning empty results.")
                self.payload_values['raw_config'] = config
                eta = generate_default_eta_expression(
                    daily_left=first_response['daily_left'],
                    hourly_left=first_response['hourly_left'],
                    minute_left=first_response['minute_left']
                )

                scheduler_response = await schedule_lusha_company_collection(
                    self.payload_values,
                    eta
                )

                logger.info(f"Scheduler response: {scheduler_response}")

                return []
                
            elif (first_response['status_code'] == 201
                  and "data" not in first_response['results']
                  or first_response['status_code'] != 201):
                logger.warning("No data in first response. Returning empty results.")
                return []

            # Process first page data
            page_companies = []

            for company in first_response["results"]["data"]:
                page_companies.append({
                    "id": company["id"],
                    "name": company["name"],
                    "api_response_metadata": company
                })

            # ✅ IMMEDIATE DATABASE INSERTION
            inserted_count = await self.company_saver.insert_companies_batch_to_db(page_companies, config, "lusha")
            # Step 2: Create campaign mappings
            mappings_created = await self.company_saver.create_campaign_company_mappings_batch(
                inserted_count['company_ids'], config.get("_id")
            )
            total_inserted += len(inserted_count['inserted_ids'])
            logger.info(f"📊 Page 1: Inserted {len(inserted_count['inserted_ids'])} companies")

            # Step 2: Calculate total pages needed
            total_results = first_response.get("results", {}).get("totalResults", 0)
            logger.info(f"Total results for this search: {total_results}")
            total_pages = (total_results + page_size - 1) // page_size  # Ceiling division

            logger.info(f"Total results: {total_results}, Total pages: {total_pages}")

            for page_num in range(1, total_pages):
                logger.info(f"Fetching page {page_num + 1} of {total_pages}")

                # Update payload for current page
                page_payload = self.payload_values.copy()
                page_payload["pages"] = {"page": page_num, "size": page_size}
                page_payload["total_results"] = total_results

                self.payload_values = page_payload
                page_response = await self.lusha_search_api()

                if page_response['status_code'] == 429:
                    # Rate limit hit and retries exhausted
                    logger.info(f"Rate limit hit on page {page_num + 1}. ")
                    rate_limit_hit = True
                    self.payload_values['raw_config'] = config

                    eta = generate_default_eta_expression(
                        daily_left=page_response['daily_left'],
                        hourly_left=page_response['hourly_left'],
                        minute_left=page_response['minute_left']
                    )
                    scheduler_response = await schedule_lusha_company_collection(self.payload_values, eta)
                    logger.info(f"Scheduler response: {scheduler_response}")
                    break

                elif (page_response['status_code'] == 201
                      and "data" in page_response['results']):
                    # Successfully got data from this page
                    page_companies = []

                    for company in page_response["results"]["data"]:
                        page_companies.append({
                            "id": company["id"],
                            "name": company["name"],
                            "api_response_metadata": company
                        })

                    # ✅ IMMEDIATE DATABASE INSERTION
                    inserted_count = await self.company_saver.insert_companies_batch_to_db(
                        page_companies, config,
                        "lusha"
                    )
                    total_inserted += len(inserted_count['inserted_ids'])

                    mappings_created = await self.company_saver.create_campaign_company_mappings_batch(
                        inserted_count['company_ids'], config.get("_id")
                    )
                    logger.info(f"📊 Page {page_num + 1}: Inserted {len(inserted_count['inserted_ids'])} companies")

                else:
                    logger.info(f"Failed to fetch page {page_num}")
                    break

            if rate_limit_hit:
                logger.info(f"Collection completed with rate limiting. "
                            f"Collected {total_inserted} companies out of {total_results} total available.")

            else:
                logger.info(
                    f"Collection completed successfully. "
                    f"Collected {total_inserted} companies from {total_pages} pages.")

        except Exception as e:
            raise Exception(f"Error searching companies: {str(e)}")
        finally:
            logger.info(f"Returning {total_inserted} companies")

            return total_inserted

    async def lusha_contact_search_api(self, payload_values_for_contact: Dict[str, Any],) -> Dict[str, Any]:
        bind_contextvars(operation="lusha_search_api", component="lusha_api_client", event_type="lusha_contact_search")
        logger.info(f"Payload_values_for_contact:", payload=payload_values_for_contact)

        payload_query = self.build_payload_for_contact(
            payload_values_for_contact=payload_values_for_contact
        )

        logger.info(f"Payload Query:", payload=payload_query)
        url = f"{LUSHA_BASE_URL}/prospecting/contact/search"
        headers = self.headers

        response = await self.http_session.post(url, json=payload_query, headers=headers, timeout=self.timeout)
        result = await response.json()

        if response.status  != 201:
            raise Exception(f"Search API failed: {response.status}")
            
        return result

    def build_payload_for_contact(self, payload_values_for_contact: Dict[str, Any]) -> Dict[str, Any]:
        page = payload_values_for_contact.get("page", 0)
        page_size = payload_values_for_contact.get("page_size", 50)
        company_names = payload_values_for_contact.get("company_names", [])
        departments = [DEPARTMENT_TO_CATEGORY[department]
                       for department in payload_values_for_contact.get("departments", [])]

        payload_query_for_contact = {
            "pages": {
                "page": page,
                "size": page_size
            },
            "filters": {
                "companies": {
                    "include": {
                        "names": company_names
                    }
                }
            }
        }
        logger.info(f"payload_values:", payload=payload_values_for_contact)

        if departments:
            payload_query_for_contact["filters"]["contacts"] = {
                "include": {
                    "departments": departments
                }
            }

        return payload_query_for_contact

    async def lusha_contact_enrich_api(self, request_id: str, contact_id_list: List[str]) -> Dict[str, Any]:

        url = f"{LUSHA_BASE_URL}/prospecting/contact/enrich"
        headers = self.headers

        payload = {
            "requestId": request_id,
            "contactIds": [id for id in contact_id_list]
        }

        response = await self.http_session.post(url, json=payload, headers=headers, timeout=self.timeout)
        result = await response.json()

        if response.status != 201:
           raise ApiException(f"Search API failed: {response.status}")
        
        return result

    async def lusha_get_linkedin_contact_details(self, linkedin_url: str = ""):

        if not linkedin_url:
            logger.info("No linkedin URL provided")
            return []

        url = f"{LUSHA_BASE_URL}/v2/person?linkedinUrl={linkedin_url}"
        headers = self.headers
        response = await self.http_session.get(url, headers=headers, timeout=self.timeout)
        result = await response.json()

        if response.status != 200:
            raise ApiException(f"linkedin API failed: {response.status}")
        
        return result
