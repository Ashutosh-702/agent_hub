import os
import random
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date
from chronos_client.client import SchedulerAPIClient
from bson import ObjectId


env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

def serialize_for_json(obj):
    """Convert ObjectIds and datetime objects to strings for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, timezone):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def get_eta_datetime(eta: int) -> str:
    """Calculate ETA in ISO format that works with MongoDB"""
    eta_datetime = datetime.now(timezone.utc) + timedelta(minutes=eta) + timedelta(seconds=10)
    # Return in ISO format with timezone - MongoDB can handle this
    return eta_datetime.isoformat()

def generate_default_eta_expression() -> str:
    """
    Generate a default ETA for 10 seconds from now in ISO format (for SIT testing)
    Returns ISO format that MongoDB can handle directly
    """
    future_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    # Return in ISO format with timezone - MongoDB can handle this
    return future_time.isoformat()

async def schedule_lusha_company_collection(campaign_details: dict, eta):
    """
    Schedule batch processing using cron expression with Chronos
    This will call /process-batch/{batch_id} at the scheduled time
    """
    chronos_url = os.getenv("CHRONOS_INTRNL_SVC")
    scheduler_client = SchedulerAPIClient(base_url=chronos_url)
    
    # Serialize ObjectIds and datetime objects to avoid JSON serialization errors
    serialized_campaign_details = serialize_for_json(campaign_details)
    
    scheduler_payload = {
        "service_name": "linkedin_sdr",
        "topic": "lusha-company-collection",  
        "payload": {
            "campaign_details": json.dumps(serialized_campaign_details),
            "action": "process_lusha_company_collection"  
        },
        "eta": eta,  # eta is now properly formatted from get_eta_datetime()
        "partition_value": str(campaign_details.get("campaign_id", ""))
    }
    
    try:
        print(f"Scheduling lusha company collection {campaign_details.get('campaign_id')} with eta: {eta}")
        scheduler_response = await scheduler_client.create_scheduler(scheduler_data=scheduler_payload)
        if scheduler_response.get("status") != 200:
            raise Exception("Error while scheduling batch processing")
        return scheduler_response
    except Exception as e:
        print(f"Error scheduling batch: {e}")
        raise Exception("Error while scheduling batch processing")

async def schedule_connection_processing(batch_id: str, linkedin_url: str):
    """
    Schedule individual connection processing with random delay
    Simple approach without kafka complexity
    """
    chronos_url = os.getenv("CHRONOS_INTRNL_SVC")
    scheduler_client = SchedulerAPIClient(base_url=chronos_url)
    
    # 5 mins + random (0-30 mins) delay
    base_delay = 5
    random_delay = random.randint(0, 30)
    total_delay = base_delay + random_delay
    
    scheduler_payload = {
        "service_name": "linkedin_sdr",
        "topic": "linkedin-connection-processing",
        "payload": {
            "batch_id": batch_id,
            "linkedin_url": linkedin_url
        },
        "eta": get_eta_datetime(eta=total_delay),
        "partition_value": batch_id
    }
    
    try:
        scheduler_response = await scheduler_client.create_scheduler(scheduler_data=scheduler_payload)
        if scheduler_response.get("status") != 200:
            raise Exception("Error while scheduling connection processing")
        return scheduler_response
    except Exception as e:
        print(f"Error scheduling connection: {e}")
        raise Exception("Error while scheduling connection processing") 