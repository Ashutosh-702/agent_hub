import gspread
from ai_agents.core_sdr.src.api.lusha_api import lusha_collect_companies_from_search
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, List, OrderedDict
from pathlib import Path
import json

LUSHA_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "config" / "lusha_industry_config.json"
)
LUSHA_COMPANY_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "config" / "country_api_results.json"
)
LUSHA_REGION_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "config" / "region_country_mapping.json"
)

with open(LUSHA_COMPANY_CONFIG_PATH, "r", encoding="utf-8") as f:
    LUSHA_COMPANY_CONFIG = json.load(f)

with open(LUSHA_CONFIG_PATH, "r", encoding="utf-8") as f:
    LUSHA_CONFIG = json.load(f)

with open(LUSHA_REGION_CONFIG_PATH, "r", encoding="utf-8") as f:
    LUSHA_REGION_CONFIG = json.load(f)

LUSHA_LOOKUP = {}
for main in LUSHA_CONFIG:
    for sub in main["sub_industries"]:
        LUSHA_LOOKUP[sub["value"]] = sub["id"]

def get_industry_mapping() -> Dict[str, int]:
    """
    Fetch industry name to ID mapping from Google Sheets
    Returns: Dictionary mapping industry names to Lusha industry IDs
    """
    try:
        mapping = {"Sub": {}, "Main": {}}
        for name, id_val in LUSHA_LOOKUP.items():
            mapping["Sub"][name] = id_val
        return mapping
        
    except Exception as e:
        print(f"❌ Error loading industry mapping: {e}")
        return {}

def parse_employee_range(range_str: str) -> tuple:
    """
    Parse employee range strings like '11-50', '201+' to min/max values
    """
    range_str = range_str.strip()
    
    if '+' in range_str:
        min_val = int(range_str.replace('+', ''))
        return min_val, 150000000000
    elif '-' in range_str:
        parts = range_str.split('-')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    
    try:
        val = int(range_str)
        return val, val
    except:
        return 1, 10  

def convert_revenue_to_actual(revenue_millions: str, currency: str = "USD") -> int:
    """
    Convert revenue from millions to actual numbers
    """
    ## if curency is INR then conert to usd
    
    try:
        if currency == "INR":
            revenue_millions = float(revenue_millions) / 87.67
        revenue_float = float(revenue_millions)
        actual = int(revenue_float * 1000000)
        #TODO: Currency conversion logic 
        
        return actual
    except:
        return 0

def sheets_to_lusha_config(sheets_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert sheets configuration to Lusha API configuration
    """
    lusha_config = {
        "pages": {"page": 0, "size": 40} 
    }
    industry_names = sheets_data.get("segmentation", {}).get("industry", [])
    if not isinstance(industry_names, list):
        print("⚠️ Expected list for industry names, got:", type(industry_names))
        industry_names = []

    if industry_names:
        sub_ids = []
        for name in industry_names:
            if name in LUSHA_LOOKUP:
                sub_ids.append(LUSHA_LOOKUP[name])
            else:
                print(f"⚠️ Industry '{name}' not found in mapping")
        sub_ids = list(OrderedDict.fromkeys(sub_ids))
        if sub_ids:
            lusha_config["subIndustriesIds"] = sub_ids
    
    if sheets_data.get("target", "")['location']['names']:
        lusha_locations = []
        location_type = sheets_data['target']["location"]['type']
        locations = sheets_data['target']["location"]['names']
        if locations:
            if location_type == "region":
                lusha_countries = []
                for location in locations:
                    if location in LUSHA_REGION_CONFIG:
                        lusha_countries.extend(LUSHA_REGION_CONFIG[location])
                    else:
                        lusha_countries.append(location)
                locations = lusha_countries
            for location in locations:
                if location in LUSHA_COMPANY_CONFIG:
                    lusha_locations.append(
                        LUSHA_COMPANY_CONFIG[location].get("country",location)
                    )
                else:
                    lusha_locations.append(location)
            if lusha_locations:
                    lusha_config["locations"] = lusha_locations
        else:
            lusha_config["locations"] = locations
    
    revenue_min = sheets_data.get("target", "")['revenue_min']
    revenue_max = sheets_data.get("target", "")['revenue_max']
    currency = sheets_data.get("target", "")['currency']
    

    print(f"revenue_min_check: {revenue_min}, revenue_max_check: {revenue_max}, currency: {currency}")
    ## here value is coming in this way
    ## revenue_min_check: (1,), revenue_max_check: (2,), currency: ('USD',)
    if revenue_min and revenue_max:
        try:
            min_value = revenue_min[0] if isinstance(revenue_min, tuple) else revenue_min
            max_value = revenue_max[0] if isinstance(revenue_max, tuple) else revenue_max
            currency_value = currency[0] if isinstance(currency, tuple) else currency
        
            min_actual = convert_revenue_to_actual(min_value, currency_value)
            max_actual = convert_revenue_to_actual(max_value, currency_value)
            print(f"min_actual: {min_actual}, max_actual: {max_actual}")
            if min_actual > 0 or max_actual > 0:
                lusha_config["revenue"] = {
                    "min": min_actual if min_actual > 0 else 1,
                    "max": max_actual
                }
        except Exception as e:
            print(f"⚠️ Error processing revenue: {e}")
    
    if sheets_data.get("target", "")['employee_count']:
        employee_ranges = [range_str for range_str in sheets_data['target']["employee_count"] if range_str]
        if employee_ranges and employee_ranges[0] != "null":
            print(f"employee_ranges: {employee_ranges}")
            sizes =[]
            for range in employee_ranges:
                print(f"range_value: {range}")
                min_emp, max_emp = parse_employee_range(range)
                sizes.append({
                "min": min_emp,
                "max": max_emp
            })
            print(f"sizes: {sizes}")
            lusha_config["sizes"] = sizes
    lusha_config["campaign_id"] = sheets_data.get("_id")
    print(f"✅ Converted sheets config to Lusha config: {lusha_config}")
    return lusha_config

async def get_companies_from_lusha(config: Dict[str, Any], cached_data: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    """
    Main function to get companies from Lusha using sheets data
    """
    
    lusha_config = sheets_to_lusha_config(config)
    print("Lusha config:", lusha_config)
    if not lusha_config or len(lusha_config) <= 1: 
        print("❌ No valid Lusha configuration generated")
        return []
    
    try:
        companies = await lusha_collect_companies_from_search(lusha_config, cached_data, config)
        print(f"✅ Retrieved {len(companies)} companies from Lusha")
        return companies
        
    except Exception as e:
        print(f"❌ Error calling Lusha API: {e}")
        return []

def integrate_with_orchestrated_run(sheets_data: Dict[str, Any], companies: List[str]) -> Dict[str, Any]:
    """
    Prepare config for orchestrated/run API
    """
    search_query = sheets_data.get("web_prompt", "")
    target_executives = sheets_data.get("persona_prompt", "")
    
    company_list = ", ".join(companies[:10])  
    
    final_query = f"Companies from this list: {company_list}"
    
    orchestrated_config = {
        "query": final_query,
        "search_query": search_query,
        "target_executives": target_executives,
        "companies": companies,  # Include full list
        "original_sheets_data": sheets_data  # For reference
    }
    
    return orchestrated_config