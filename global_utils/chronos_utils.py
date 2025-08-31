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
    """
    Generate a default ETA for 10 seconds from now in chronos_client format (for SIT testing)
    Returns format: '%Y-%m-%dT%H:%M:%S' (no timezone)
    """
    future_time = (datetime.utcnow() + timedelta(seconds=10)).isoformat(timespec="seconds")
    # Return in format expected by chronos_client: '%Y-%m-%dT%H:%M:%S' (no timezone)
    return future_time
    # return future_time.strftime('%Y-%m-%dT%H:%M:%S')

# Store original methods at module level
_original_fetch = AsyncHTTPClient.fetch
_original_post = AsyncHTTPClient.post

async def _patched_fetch(self, method, url, **kwargs):
    """Patched fetch method that properly serializes datetime objects"""
    print(f"🔧 FETCH PATCH CALLED: method={method}, url={url}")
    print(f"🔧 kwargs keys: {list(kwargs.keys())}")
    
    if 'json' in kwargs:
        # Serialize the JSON data ourselves with our enhanced converter
        json_data = kwargs.pop('json')
        print(f"🔧 Original JSON data type: {type(json_data)}")
        print(f"🔧 ETA in original data: {json_data.get('eta')} (type: {type(json_data.get('eta'))})")
        
        serialized_data = serialize_for_json(json_data)
        print(f"🔧 ETA after serialization: {serialized_data.get('eta')} (type: {type(serialized_data.get('eta'))})")
        
        kwargs['data'] = json.dumps(serialized_data)
        kwargs['headers'] = {'Content-Type': 'application/json'}
        print(f"🔧 Patched HTTP call - serialized datetime objects in payload")
    
    return await _original_fetch(self, method, url, **kwargs)

async def _patched_post(self, url, **kwargs):
    """Patched post method that properly serializes datetime objects"""
    print(f"🔧 POST PATCH CALLED: url={url}")
    print(f"🔧 kwargs keys: {list(kwargs.keys())}")
    
    if 'json' in kwargs:
        # Serialize the JSON data ourselves with our enhanced converter
        json_data = kwargs['json']
        print(f"🔧 Original JSON data type: {type(json_data)}")
        print(f"🔧 ETA in original data: {json_data.get('eta')} (type: {type(json_data.get('eta'))})")
        
        serialized_data = serialize_for_json(json_data)
        print(f"🔧 ETA after serialization: {serialized_data.get('eta')} (type: {type(serialized_data.get('eta'))})")
        
        kwargs['json'] = serialized_data
        print(f"🔧 Patched POST call - serialized datetime objects in payload")
    
    return await _original_post(self, url, **kwargs)

def _enable_datetime_serialization_patch():
    """Enable the datetime serialization patch"""
    print(f"🔧 ENABLING PATCH: Original fetch = {_original_fetch}")
    print(f"🔧 ENABLING PATCH: Original post = {_original_post}")
    AsyncHTTPClient.fetch = _patched_fetch
    AsyncHTTPClient.post = _patched_post
    print(f"🔧 PATCH ENABLED: New fetch = {AsyncHTTPClient.fetch}")
    print(f"🔧 PATCH ENABLED: New post = {AsyncHTTPClient.post}")

def _disable_datetime_serialization_patch():
    """Disable the datetime serialization patch"""
    AsyncHTTPClient.fetch = _original_fetch
    AsyncHTTPClient.post = _original_post

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
    
    # Enable datetime serialization patch
    _enable_datetime_serialization_patch()
    
    try:
        print(f"Scheduling lusha company collection {campaign_details.get('campaign_id')} with eta: {eta}")
        scheduler_response = await scheduler_client.create_scheduler(scheduler_data=scheduler_payload)
        if scheduler_response.get("status") != 200:
            raise Exception("Error while scheduling batch processing")
        return scheduler_response
    except Exception as e:
        print(f"Error scheduling batch: {e}")
        raise Exception("Error while scheduling batch processing")
    finally:
        # Disable the patch
        _disable_datetime_serialization_patch()

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