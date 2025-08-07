import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, List
from pathlib import Path
from config.loaded_config import loaded_config
# from models.campaign_details import add_campaign
from database.collection_dao.campaigns import CampaignsDao
def prompt_fetcher() -> List[Dict[str, Any]]:
    """
    Fetch all prompts from a Google Sheet where status is FALSE.
    Do not update the sheet — another function handles status changes.
    Returns a list of dicts: [{prompt, row_index}]
    """
    pass
    # return prompts
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
async def submit_company_data(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        config["status"] = "active"
        campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        await campaign_dao.create_campaign(config)
        return {"status": "success", "message": "Data uploaded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}