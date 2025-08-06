import requests
import json
import os
import re
from typing import List, Dict, Any

LUSHA_API_KEY = os.getenv("LUSHA_API_KEY")
def lusha_search_api(payload_values: Dict[str, Any]) -> List[int]:
    payload_query =  build_payload(payload_values=payload_values)
    print(f"Payload Query: {json.dumps(payload_query, indent=2)}")
    url = f"https://api.lusha.com/prospecting/company/search"
    headers = {
        'accept': 'application/json',
        "api_key": f"{os.getenv('LUSHA_API_KEY')}",
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=payload_query)
    if response.status_code == 201:
       return response.json()
    else:
        raise Exception(f"Search API failed: {response.status_code} - {response.text}")
def build_payload(payload_values: Dict[str, Any]) -> Dict[str, Any]:
    """Build the API payload from input values."""
    # payload_values = {industry: [12,23,23], location: india, revenue: {min:100000, max: 1000000}, size: {min: 10, max: 100}}

    payload_query = {
        "pages": {
            "page": 0,
            "size": 1  # Default size
        },
        "filters": {
            "companies": {
                "include": {},
                "exclude": {}
            }
        }
    }
    if "page_size" in payload_values and payload_values["page_size"]:
        payload_query["pages"]["size"] = payload_values["page_size"]
    if "mainIndustriesIds" in payload_values and payload_values["mainIndustriesIds"]:
        payload_query["filters"]["companies"]["include"]["mainIndustriesIds"] = payload_values["mainIndustriesIds"]
    
    if "subIndustriesIds" in payload_values and payload_values["subIndustriesIds"]:
        payload_query["filters"]["companies"]["include"]["subIndustriesIds"] = payload_values["subIndustriesIds"]
    if "locations" in payload_values and isinstance(payload_values["locations"], list):
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
    # if "size" in payload_values and payload_values["size"]:
    #     size = payload_values["size"]
    #     if "min" in size and "max" in size:
    #         payload_query["filters"]["companies"]["include"]["sizes"] = [
    #             {
    #                 "min": size["min"],
    #                 "max": size["max"]
    #             }
    #         ]
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

def lusha_collect_companies_from_search(payload_values: Dict[str, Any]) -> List[int]:
    try:
        print("working propoer")
        all_companies = []
        page_size = payload_values.get("pages", {}).get("size", 20)

        initial_payload = payload_values.copy()
        initial_payload["pages"] = {"page": 0, "size": page_size}
        first_response = lusha_search_api(payload_values=initial_payload)
        if not first_response or "data" not in first_response:
            return []
        for company in first_response["data"]:
            all_companies.append(company["name"])

        # Step 2: Calculate total pages needed
        total_results = first_response.get("totalResults", 0)
        total_pages = (total_results + page_size - 1) // page_size  # Ceiling division
        
        print(f"Total results: {total_results}, Total pages: {total_pages}")
        total_pages  = 3 if total_pages > 3 else total_pages
        for page_num in range(1, total_pages):
            print(f"Fetching page {page_num + 1} of {total_pages}")
            
            # Update payload for current page
            page_payload = payload_values.copy()
            page_payload["pages"] = {"page": page_num, "size": page_size}
            
            page_response = lusha_search_api(payload_values=page_payload)
            
            if page_response and "data" in page_response:
                # Extract companies from this page
                for company in page_response["data"]:
                    all_companies.append(company["name"])
            else:
                print(f"Failed to fetch page {page_num}")
                break
        
        print(f"Collected {len(all_companies)} companies from {total_pages} pages")
        print(f"all_companies: {all_companies}")
        return all_companies
    except Exception as e:
        raise Exception(f"Error searching companies: {str(e)}")
