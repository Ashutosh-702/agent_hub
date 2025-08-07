import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, List
from pathlib import Path
from config.loaded_config import loaded_config
# from models.campaign_details import add_campaign
from database.collection_dao.campaigns import CampaignsDao
async def prompt_fetcher() -> List[Dict[str, Any]]:
    """
    Fetch all prompts from a Google Sheet where status is FALSE.
    Do not update the sheet — another function handles status changes.
    Returns a list of dicts: [{prompt, row_index}]
    """
    campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
    prompts = await campaign_dao.get_campaigns({"status": "active"})
    # pass
    return prompts
async def change_status():
    pass
async def submit_company_data(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        config["status"] = "active"
        campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        await campaign_dao.create_campaign(config)
        return {"status": "success", "message": "Data uploaded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}