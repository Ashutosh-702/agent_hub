import requests
import json
import os
import re
from typing import List, Dict, Any

def search_api(dsl_query: Dict[str, Any]) -> List[int]:
    items_per_page = 1
    
    url = f"https://api.coresignal.com/cdapi/v2/company_clean/search/es_dsl?items_per_page={items_per_page}"
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
    url = f"https://api.coresignal.com/cdapi/v2/company_clean/collect/{company_id}"
    
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

def collect_companies_from_search(config: Dict[str, Any], exclude_company_list: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    try:
        dsl_query = build_payload(config,exclude_company_list)
        company_ids = search_api(dsl_query)
    except Exception as e:
        raise Exception(f"Error searching companies in coresignal api: {str(e)}")
    companies = []
    try:
        for company_id in company_ids:
            company_data = collect_api(company_id)
            if company_data:
                companies.append({"id":company_data["id"],"name":company_data["name"]})
    except Exception as e:
        raise Exception(f"Error collecting company data: {str(e)}")
    return companies


def build_payload(config: Dict[str,Any], exclude_company_list: List[str]):
    industries = config['segmentation']["industry"]
    locations = config['target']["location"]['names']
    location_type = config['target']["location"]['type']
    query = {
        "query": {
            "bool": {
                "must": [],
                "must_not": []
            }
        }
    }

    must_clauses = query["query"]["bool"]["must"]
    must_not_clauses = query["query"]["bool"]["must_not"]
    if exclude_company_list is not None:
        for company_found in exclude_company_list:
            must_not_clauses.append({
                "match":{
                    "name": company_found["name"]
                }
            })
    if industries:
        industry_should = [
            {"match": {"industry": {"query": industry}}}
            for industry in industries
        ]
        must_clauses.append({
            "bool": {
                "should": industry_should,
                "minimum_should_match": 1
            }
        })

    sizes = []
    if config.get("target", {}).get("employee_count", ""):
        employee_ranges = [range_str for range_str in config['target']["employee_count"].split(',') if range_str and range_str != "null"]
        for range_str in employee_ranges:
            if '+' in range_str:
                min_val = int(range_str.replace('+', ''))
                max_val = 1500
            elif '-' in range_str:
                parts = range_str.split('-')
                if len(parts) == 2:
                    min_val = int(parts[0])
                    max_val = int(parts[1])
            else:
                continue
            sizes.append({"min": min_val, "max": max_val})

    if sizes:
        employee_should = []
        for size in sizes:
            clause = {
                "range": {
                    "size_employees_count": {
                        "gte": size["min"],
                        "lte": size["max"]
                    }
                }
            }
            employee_should.append(clause)

        must_clauses.append({
            "bool": {
                "should": employee_should,
                "minimum_should_match": 1
            }
        })

    if locations and location_type=="country":
        location_should = [
            {"match": {"location_hq_country": loc.strip()}}
            for loc in locations
            if loc.strip()
        ]
        must_clauses.append({
            "bool": {
                "should": location_should,
                "minimum_should_match": 1
            }
        })
    elif locations and location_type=="region":
        location_should = [
            {"match": {"location_hq_regions": loc.strip()}}
            for loc in locations
            if loc.strip()
        ]
        must_clauses.append({
            "bool": {
                "should": location_should,
                "minimum_should_match": 1
            }
        })
    print("QUERY: ", query)
    return query