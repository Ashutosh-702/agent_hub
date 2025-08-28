import os
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from chronos_client.client import SchedulerAPIClient


env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

def get_eta_datetime(eta: int) -> str:
    """Calculate ETA in ISO format - copied from vector add 10 seconds"""
    return (datetime.now(timezone.utc) + timedelta(minutes=eta) + timedelta(seconds=10)).isoformat(timespec="seconds")

def generate_default_eta_expression() -> str:
    """
    Generate a default cron expression for 2 hours from now
    Returns format: "minute hour * * *" (specific time today)
    """
    # eta is in minutes
    
    future_time = datetime.now() + timedelta(hours=1)
    minute = future_time.minute
    hour = future_time.hour
    DEFAULT_TIMESPEC = 'seconds'
    future_time = future_time.isoformat(timespec=DEFAULT_TIMESPEC)
    return future_time

async def schedule_lusha_company_collection(campaign_details: str, eta: str):
    """
    Schedule batch processing using cron expression with Chronos
    This will call /process-batch/{batch_id} at the scheduled time
    """
    chronos_url = os.getenv("CHRONOS_INTRNL_SVC")
    scheduler_client = SchedulerAPIClient(base_url=chronos_url)
    
    scheduler_payload = {
        "service_name": "linkedin_sdr",
        "topic": "lusha-company-collection",  
        "payload": {
            "campaign_details": campaign_details,
            "action": "process_lusha_company_collection"  
        },
        "eta": eta,  
        "partition_value": str(campaign_details.get("campaign_id"))
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