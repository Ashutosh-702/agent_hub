import gspread
from ai_agents.core_sdr.src.api.lusha_api import lusha_collect_companies_from_search
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, List
from pathlib import Path

def get_industry_mapping() -> Dict[str, int]:
    """
    Fetch industry name to ID mapping from Google Sheets
    Returns: Dictionary mapping industry names to Lusha industry IDs
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        base_dir = Path(__file__).resolve().parent.parent.parent
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            f"{base_dir}/config/service_account.json", scope
        )
        client = gspread.authorize(creds)
        mapping_sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1YlSkziIIWoQd8S6DCC4fiX4uU0R96y_d7qEtfEADZWk/edit?gid=1348584716#gid=1348584716"
        ).worksheet("Combined Mapping")
        expected_headers = [ 'subIndustry', 'mainIndustry', 'Lusha subIndustry id', 'mainIndustryId', 'coresignalIndustries']
        # headers = mapping_sheet.row_values(1)
        # print("Detected headers:", headers)

        records = mapping_sheet.get_all_records(expected_headers=expected_headers)
        # print("records: ",records)
        mapping = {}
        
        for record in records:
            sub_industry = record.get("subIndustry", "")
            main_industry = record.get("mainIndustry", "")
            sub_industry_id = record.get("Lusha subIndustry id", "")
            main_industry_id = record.get("mainIndustryId", "")
            if sub_industry and sub_industry_id:
                try:
                    mapping[sub_industry] = int(sub_industry_id)
                except ValueError:
                    print(f"⚠️ Invalid subIndustry ID for '{sub_industry}': {sub_industry_id}")
            
            if main_industry and main_industry_id and main_industry not in mapping:
                try:
                    mapping[main_industry] = int(main_industry_id)
                except ValueError:
                    print(f"⚠️ Invalid mainIndustry ID for '{main_industry}': {main_industry_id}")
        
        print(f"✅ Loaded {len(mapping)} industry mappings")
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
        return min_val, 10000
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
        "pages": {"page": 0, "size": 20} 
    }
    
    if sheets_data.get("industry"):
        industry_mapping = get_industry_mapping()
        print("WORKING TILL HERE - 1")
        # print("industry mapping:",industry_mapping)

        industry_names = [name for name in sheets_data["industry"][0].split(',') if name]
        print("industry_names",industry_names)
        print("WORKING TILL HERE - 2")
        industry_ids = []
        
        for name in industry_names:
            if name in industry_mapping:
                industry_ids.append(industry_mapping[name])
            else:
                print(f"⚠️ Industry '{name}' not found in mapping")
        
        if industry_ids:
            lusha_config["mainIndustriesIds"] = industry_ids
    
    if sheets_data.get("location"):
        locations = [loc for loc in sheets_data["location"][0].split(',') if loc]
        if locations:
            lusha_config["locations"] = locations
    
    revenue_min = sheets_data.get("revenue_min")
    revenue_max = sheets_data.get("revenue_max") 
    currency = sheets_data.get("currency", "USD")
    
    if revenue_min and revenue_max:
        try:
            min_actual = convert_revenue_to_actual(revenue_min, currency)
            max_actual = convert_revenue_to_actual(revenue_max, currency)
            
            if min_actual > 0 and max_actual > 0:
                lusha_config["revenue"] = {
                    "min": min_actual,
                    "max": max_actual
                }
        except Exception as e:
            print(f"⚠️ Error processing revenue: {e}")
    
    if sheets_data.get("employee_count"):
        employee_ranges = [range_str for range_str in sheets_data["employee_count"][0].split(',') if range_str]
        if employee_ranges and employee_ranges[0] != "null":
            print(f"employee_ranges: {employee_ranges}")
            sizes =[]
            for range in employee_ranges:
                min_emp, max_emp = parse_employee_range(range)
                sizes.append({
                "min": min_emp,
                "max": max_emp
            })
            lusha_config["sizes"] = sizes
    
    print(f"✅ Converted sheets config to Lusha config: {lusha_config}")
    return lusha_config

def get_companies_from_lusha(sheets_data: Dict[str, Any]) -> List[str]:
    """
    Main function to get companies from Lusha using sheets data
    """
    
    lusha_config = sheets_to_lusha_config(sheets_data)
    print("Lusha config:", lusha_config)
    if not lusha_config or len(lusha_config) <= 1: 
        print("❌ No valid Lusha configuration generated")
        return []
    
    try:
        companies = lusha_collect_companies_from_search(lusha_config)
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