from typing import Dict, Any, List
from config.loaded_config import loaded_config
from database.collection_dao.campaigns import CampaignsDao

async def prompt_fetcher() -> List[Dict[str, Any]]:
    """
    Fetch all prompts from a Db where status is active.
    Returns a list of dicts: [{prompt}]
    """
    try:
        campaign_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        prompts = await campaign_dao.get_campaigns({"status": "active"})
    except Exception as e:
        raise Exception(f"Error fetching data from db: {str(e)}")
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