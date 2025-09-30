from pathlib import Path
import requests
import json
import os
from typing import List, Dict, Any, OrderedDict
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from config.loaded_config import loaded_config

urllib3.disable_warnings(InsecureRequestWarning)

LUSHA_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "lusha_industry_config.json"
with open(LUSHA_CONFIG_PATH, "r", encoding="utf-8") as f:
    LUSHA_CONFIG = json.load(f)
    
    
async def search_api(dsl_query: Dict[str, Any]) -> List[int]:
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
    
    response = await loaded_config.http_session.post(url, json=payload, headers=headers)
    result = await response.json()

    if response.status == 200:
        company_ids = [int(item) for item in result]
        return company_ids
    else:
        raise Exception(f"Search API failed: {response.status} - {response.text}")

async def collect_api(company_id: int) -> Dict[str, Any]:
    url = f"https://api.coresignal.com/cdapi/v2/company_clean/collect/{company_id}"
    
    headers = {
        'accept': 'application/json',
        'apikey': os.getenv('CORESIGNAL_API_KEY'),
        'Content-Type': 'application/json'
    }
    
    response = await loaded_config.http_session.get(url, headers=headers)
    result = await response.json()
    
    if response.status == 200:
        return result
    else:
        raise Exception(f"Collect API failed: {response.status} - {response.text}")

async def collect_companies_from_search(config: Dict[str, Any], exclude_company_list: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    companies = []
    try:
        dsl_query = build_payload(config,exclude_company_list)
        company_ids = await search_api(dsl_query)
        for company_id in company_ids:
            company_data = await collect_api(company_id)
            if company_data:
                companies.append({"id":company_data["id"],"name":company_data["name"],"api_response_metadata": company_data})
    except Exception as e:
        print(f"Error collecting company data: {str(e)}")
    finally:
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
    coresignal_lookup = {}
    for main in LUSHA_CONFIG:
        for sub in main["sub_industries"]:
            coresignal_lookup[sub["value"]] = sub.get("coresignal", [])

    mapped_industries = []
    for name in industries:
        if name in coresignal_lookup:
            mapped_industries.extend(coresignal_lookup[name])
        else:
            print(f"⚠️ No CoreSignal mapping found for '{name}'")
    industries = list(OrderedDict.fromkeys(mapped_industries))
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
        employee_ranges = [range_str for range_str in config['target']["employee_count"] if range_str and range_str != "null"]
        for range_str in employee_ranges:
            if '+' in range_str:
                min_val = int(range_str.replace('+', ''))
                max_val = 150000000000
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