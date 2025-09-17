from eventbridge.logic.async_kafka_consumer import orjson
import requests
import json
import os
from typing import List, Dict, Any, Optional

import urllib3
from urllib3.exceptions import InsecureRequestWarning

from config.loaded_config import loaded_config
from global_utils.chronos_utils import (
    schedule_lusha_company_collection,
    generate_default_eta_expression
)
from ai_agents.core_sdr.src.parsers.constants import COMPANY_GROUPINGS

urllib3.disable_warnings(InsecureRequestWarning)


async def lusha_search_api(
    payload_values: Dict[str, Any],
    cached_data: Optional[List[Dict[str, Any]]] = None,
) -> List[int]:
    print(f"Payload_values: {payload_values}")

    payload_query = build_payload(
        payload_values=payload_values, 
        cached_data=cached_data,
    )
    print(f"Payload Query: {json.dumps(payload_query, indent=2)}")

    url = f"https://api.lusha.com/prospecting/company/search"
    headers = {
        'accept': 'application/json',
        "api_key": f"{loaded_config.lusha_api_key}",
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        url, headers=headers, json=payload_query, verify=False, timeout=30,
    )

    response_data = {}
    response_data['status_code'] = response.status_code

    if response.status_code == 201:
        response_data['results'] = response.json()
        return response_data
    elif response.status_code == 429:
        # Return None to indicate rate limit exhaustion rather than raising exception
        response_headers = dict(response.headers)
        response_data['daily_left'] = response_headers.get(
            'x-daily-requests-left', None)

        response_data['hourly_left'] = response_headers.get(
            'x-hourly-requests-left', None)

        response_data['minute_left'] = response_headers.get(
            'x-minute-requests-left', None)

        print(f"Daily left: {response_data['daily_left']}, "
              f"Hourly left: {response_data['hourly_left']}, "
              f"Minute left: {response_data['minute_left']}")

        print(f"Rate limit exhausted")
        return response_data
    else:
        print(f"Search API failed: {response.status_code} - {response.text}")
        return None


def build_payload(
    payload_values: Dict[str, Any],
    cached_data: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Build the API payload from input values."""

    payload_query = {
        "pages": {
            "page": 0,
            "size": 40
        },
        "filters": {
            "companies": {
                "include": {},
                "exclude": {}
            }
        }
    }

    print(f"payload_values: {payload_values}")

    # if cached_data:
    #     payload_query["filters"]["companies"]["exclude"]["names"] = [company['name'] for company in cached_data]

    if "page_size" in payload_values and payload_values["page_size"]:
        payload_query["pages"]["size"] = payload_values["page_size"]

    if "mainIndustriesIds" in payload_values and payload_values["mainIndustriesIds"]:
        payload_query["filters"]["companies"]["include"]["mainIndustriesIds"] = payload_values["mainIndustriesIds"]
    
    if "subIndustriesIds" in payload_values and payload_values["subIndustriesIds"]:
        payload_query["filters"]["companies"]["include"]["subIndustriesIds"] = payload_values["subIndustriesIds"]

    if "locations" in payload_values and isinstance(payload_values["locations"], list):

        if "location_type" in payload_values and payload_values["location_type"] == "region":
            payload_query["filters"]["companies"]["include"]["locations"] = []

            for region in payload_values["locations"]:
                if region in COMPANY_GROUPINGS:
                    payload_query["filters"]["companies"]["include"]["locations"].append({"country_grouping": COMPANY_GROUPINGS[region]})
                else:
                    payload_query["filters"]["companies"]["include"]["locations"].append({"continent": region})
        else:
            payload_query["filters"]["companies"]["include"]["locations"] = [{"country": country} for country in payload_values["locations"]]

    if "revenue" in payload_values and payload_values["revenue"]:
        revenue = payload_values["revenue"]

        if "min" in revenue and "max" in revenue:
            payload_query["filters"]["companies"]["include"]["revenues"] = [
                {
                    "min": revenue["min"],
                    "max": revenue["max"]
                }
            ]

    if "sizes" in payload_values and payload_values["sizes"]:
        sizes = payload_values["sizes"]

        if isinstance(sizes, list) and len(sizes) > 0:
            payload_query["filters"]["companies"]["include"]["sizes"] = sizes  # First size only

    if "pages" in payload_values:
        pages = payload_values["pages"]

        if "page" in pages:
            payload_query["pages"]["page"] = pages["page"]

        if "size" in pages:
            payload_query["pages"]["size"] = pages["size"]
    
    return payload_query


async def lusha_collect_companies_from_search(
    payload_values: Dict[str, Any],
    cached_data: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    all_companies = []

    try:
        print("working propoer")
        
        page_size = payload_values.get("pages", {}).get("size", 20)
        rate_limit_hit = False

        # Step 1: Get first page to determine total results
        initial_payload = payload_values.copy()
        initial_payload["pages"] = {"page": 0, "size": page_size}
        
        first_response = await lusha_search_api(
            payload_values=initial_payload, 
            cached_data=cached_data
        )

        if first_response['status_code'] == 429:
            print("First API call failed or hit rate limit. Returning empty results.")
            payload_values['raw_config'] = config
            eta = generate_default_eta_expression(
                daily_left=first_response['daily_left'],
                hourly_left=first_response['hourly_left'],
                minute_left=first_response['minute_left']
            )

            scheduler_response = await schedule_lusha_company_collection(
                payload_values, 
                eta
            )

            print(f"Scheduler response: {scheduler_response}")
            return []
        elif (first_response['status_code'] == 201
              and "data" not in first_response['results']
              or first_response['status_code'] != 201):
            print("No data in first response. Returning empty results.")
            return []
            
        # Process first page data
        for company in first_response["results"]["data"]:
            all_companies.append({
                "id": company["id"], 
                "name": company["name"],
                "api_response_metadata": company
            })

        # Step 2: Calculate total pages needed
        total_results = first_response.get("results", {}).get("totalResults", 0)
        print(f"Total results for this search: {total_results}")
        total_pages = (total_results + page_size - 1) // page_size  # Ceiling division
        
        print(f"Total results: {total_results}, Total pages: {total_pages}")

        #temp code
        # total_pages  = 2 if total_pages > 2 else total_pages

        for page_num in range(1, total_pages):
            print(f"Fetching page {page_num + 1} of {total_pages}")
            
            # Update payload for current page
            page_payload = payload_values.copy()
            page_payload["pages"] = {"page": page_num, "size": page_size}
            page_payload["total_results"] = total_results

            page_response = await lusha_search_api(
                payload_values=page_payload, 
                cached_data=cached_data
            )
            
            if page_response['status_code'] == 429:
                # Rate limit hit and retries exhausted
                print(f"Rate limit hit on page {page_num + 1}. "
                      f"Returning {len(all_companies)} companies collected so far.")
                rate_limit_hit = True
                page_payload['raw_config'] = config

                eta = generate_default_eta_expression(
                    daily_left=page_response['daily_left'], 
                    hourly_left=page_response['hourly_left'], 
                    minute_left=page_response['minute_left']
                )

                scheduler_response = await schedule_lusha_company_collection(
                    page_payload, eta
                )

                print(f"Scheduler response: {scheduler_response}")
                break

            elif (page_response['status_code'] == 201
                  and "data" in page_response['results']):
                # Successfully got data from this page
                page_companies = 0
                
                for company in page_response["results"]["data"]:
                    all_companies.append({
                        "id": company["id"], 
                        "name": company["name"],
                        "api_response_metadata": company
                    })
                    page_companies += 1
                print(f"Collected {page_companies} companies from page {page_num + 1}")
            else:
                print(f"Failed to fetch page {page_num}")
                break
        
        if rate_limit_hit:
            print(f"Collection completed with rate limiting. "
                  f"Collected {len(all_companies)} companies out of {total_results} total available.")
        else:
            print(f"Collection completed successfully. Collected {len(all_companies)} companies from {total_pages} pages.")
        
        
    except Exception as e:
            raise Exception(f"Error searching companies: {str(e)}")
    finally:
        print(f"Returning {len(all_companies)} companies")
        return all_companies


def lusha_contact_search_api(payload_values_for_contact: Dict[str, Any]) -> Dict[str, Any]:
    print("Payload_values_for_contact:",
          json.dumps(payload_values_for_contact, indent=2))

    payload_query = build_payload_for_contact(
        payload_values_for_contact=payload_values_for_contact
    )

    print(f"Payload Query: {json.dumps(payload_query, indent=2)}")
    url = f"https://api.lusha.com/prospecting/contact/search"
    headers = {
        'accept': 'application/json',
        "api_key": f"{os.getenv('LUSHA_API_KEY')}",
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=payload_query, verify=False, timeout=30)

    if response.status_code == 201:
       return response.json()
    else:
        raise Exception(f"Search API failed: {response.status_code} - {response.text}")


def build_payload_for_contact(payload_values_for_contact: Dict[str, Any]) -> Dict[str, Any]:
    payload_query_for_contact = {
        "pages": {
            "page": 0,
            "size": 40
        },
        "filters": {
            "companies": {
                "include": {}
            }
        }
    }
    print(f"payload_values: {payload_values_for_contact}")

    if "page_size" in payload_values_for_contact and payload_values_for_contact["page_size"]:
        payload_query_for_contact["pages"]["size"] = payload_values_for_contact["page_size"]

    if "company_names" in payload_values_for_contact and payload_values_for_contact["company_names"]:
        payload_query_for_contact["filters"]["companies"]["include"]['names'] = [
            name for name in payload_values_for_contact["company_names"]
        ]

    return payload_query_for_contact


def lusha_contact_enrich_api(request_id: str, contact_id_list: List[str]) -> Dict[str, Any]:
    
    url = f"https://api.lusha.com/prospecting/contact/enrich"
    headers = {
        'accept': 'application/json',
        "api_key": f"{os.getenv('LUSHA_API_KEY')}",
        'Content-Type': 'application/json'
    }

    payload = {
        "requestId": request_id,
        "contactIds": [id for id in contact_id_list]
    }

    response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
    
    if response.status_code == 201:
       return response.json()
    else:
        raise Exception(f"Search API failed: {response.status_code} - {response.text}")
