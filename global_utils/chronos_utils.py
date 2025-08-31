import os
import random
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date
from chronos_client.client import SchedulerAPIClient
from chronos_client.https import AsyncHTTPClient
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
    """Calculate ETA in chronos_client expected format: '%Y-%m-%dT%H:%M:%S'"""
    eta_datetime = datetime.now(timezone.utc) + timedelta(minutes=eta) + timedelta(seconds=10)
    # Return in format expected by chronos_client: '%Y-%m-%dT%H:%M:%S' (no timezone)
    return eta_datetime.strftime('%Y-%m-%dT%H:%M:%S')

def generate_default_eta_expression() -> str:
    future_time = (datetime.utcnow() + timedelta(seconds=10)).isoformat(timespec="seconds")
    # Return in format expected by chronos_client: '%Y-%m-%dT%H:%M:%S' (no timezone)
    return future_time
    # return future_time.strftime('%Y-%m-%dT%H:%M:%S')

async def schedule_lusha_company_collection(campaign_details: dict, eta):
    chronos_url = os.getenv("CHRONOS_INTRNL_SVC")
    print(f"Chronos URL: {chronos_url}")
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