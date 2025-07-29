import requests
import json
import os
import re
from typing import List, Dict, Any

def search_api(dsl_query: Dict[str, Any], user_query: str) -> List[int]:
    items_per_page = 1
    match = re.search(r'\b(\d+)\b', user_query)
    if match:
        items_per_page = int(match.group(1))
    
    url = f"https://api.coresignal.com/cdapi/v2/company_multi_source/search/es_dsl?items_per_page={items_per_page}"
    if isinstance(dsl_query, str):
        payload = dsl_query
    else:
        payload = json.dumps(dsl_query)
    headers = {
        'Content-Type': 'application/json',
        'apikey': os.getenv('CORESIGNAL_API_KEY'),
        'accept': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        company_ids = [int(item) for item in data]
        return company_ids
    else:
        raise Exception(f"Search API failed: {response.status_code} - {response.text}")

def collect_api(company_id: int) -> Dict[str, Any]:
    url = f"https://api.coresignal.com/cdapi/v2/company_multi_source/collect/{company_id}"
    
    headers = {
        'accept': 'application/json',
        'apikey': os.getenv('CORESIGNAL_API_KEY'),
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Collect API failed: {response.status_code} - {response.text}")

def collect_companies_from_search(dsl_query: Dict[str, Any], user_query: str) -> List[str]:
    try:
        company_ids = search_api(dsl_query, user_query)
    except Exception as e:
        raise Exception(f"Error searching companies: {str(e)}")
    companies = []
    try:
        for company_id in company_ids:
            company_data = collect_api(company_id)
            companies.append(company_data["company_name"])
            print(type(company_data))
    except Exception as e:
        raise Exception(f"Error collecting company data: {str(e)}")
    return companies