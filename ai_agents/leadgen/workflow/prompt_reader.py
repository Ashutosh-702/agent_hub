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
            prompt = row.get("Prompt", "")
            industry = row.get("Industry", "")
            is_b2b = row.get("is_B2B", "")
            hq = row.get("Headquarters", "")
            employee_count = row.get("Employee Count", "")
            row_index = i + 2  
            prompts.append({
                "prompt": prompt,
                "industry": industry,
                "is_b2b": is_b2b,
                "employee_count": employee_count,
                "hq": hq,
                "row_index": row_index
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
            config.get("prompt", ""),          
            config.get("industry", ""),        
            config.get("is_b2b", ""),  
            config.get("employee_count", ""),  
            config.get("hq", ""),
            # config.get("",""),
            "False"     
        ]
        sheet.append_row(row)
        return {"status": "success", "message": "Data uploaded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}