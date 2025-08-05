import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, List
from pathlib import Path
import requests

def prompt_fetcher() -> List[Dict[str, Any]]:
    """
    Fetch all prompts from a Google Sheet where status is FALSE.
    Do not update the sheet — another function handles status changes.
    Returns a list of dicts: [{prompt, row_index}]
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    base_dir = Path(__file__).resolve().parent.parent
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        f"{base_dir}/config/service_account.json", scope
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/13XUGl8aoElnlDVjd3iZKHzpENH8wZkX3l-N0WVFsZUo/edit#gid=0"
    )
    sheet = spreadsheet.sheet1
    records = sheet.get_all_records()

    prompts = []

    for i, row in enumerate(records):
        status = str(row.get("Status", "")).strip().lower()
        if status in ["false", "no", "0",""]:
            web_prompt = row.get("web_prompt", ""),
            persona_prompt = row.get("persona_prompt", ""),
            industry = row.get("industry", ""),
            employee_count = row.get("employee_count", ""),
            currency = row.get("currency", ""),
            revenue_min = row.get("revenue_min", ""),
            revenue_max = row.get("revenue_max", ""),
            location = row.get("location", ""),
            keywords = row.get("keywords", ""),
            categories = row.get("categories", ""),
            hubspot_email = row.get("hubspot_email", ""),
            product_name = row.get("product_name", ""),
            business_team = row.get("business_team", ""),
            row_index = i + 2  
            prompts.append({
                "web_prompt": web_prompt,
                "persona_prompt": persona_prompt,
                "industry": industry,
                "employee_count": employee_count,
                "currency": currency,
                "revenue_min": revenue_min,
                "revenue_max": revenue_max,
                "location": location,
                "keywords": keywords,
                "categories": categories,
                "hubspot_email": hubspot_email,
                "product_name": product_name,
                "business_team": business_team,
            })

    print(f"✅ Found {len(prompts)} prompts with status FALSE.",prompts)
    return prompts
def set_status_true(row_index: int):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    base_dir = Path(__file__).resolve().parent.parent
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        f"{base_dir}/config/service_account.json", scope
    )
    client = gspread.authorize(creds)

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/13XUGl8aoElnlDVjd3iZKHzpENH8wZkX3l-N0WVFsZUo/edit#gid=0").sheet1
    column_names = sheet.row_values(1)
    column_index = column_names.index('Status') + 1
    sheet.update_cell(row_index, column_index, "TRUE")
    print(f"📌 Marked row {row_index} as processed.")
def submit_company_data(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        base_dir = Path(__file__).resolve().parent.parent
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            f"{base_dir}/config/service_account.json", scope
        )
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/13XUGl8aoElnlDVjd3iZKHzpENH8wZkX3l-N0WVFsZUo/edit#gid=0"
        )
        sheet = spreadsheet.sheet1

        row = [
            config.get("web_prompt", ""),
            config.get("persona_prompt", ""),
            config.get("industry", ""),
            config.get("employee_count", ""),
            config.get("currency", ""),
            config.get("revenue_min", ""),
            config.get("revenue_max", ""),
            config.get("location", ""),
            config.get("keywords", ""),
            config.get("categories", ""),
            config.get("hubspot_email", ""),
            config.get("product_name", ""),
            config.get("business_team", ""),
            "False"     
        ]
        sheet.append_row(row)
        return {"status": "success", "message": "Data uploaded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}