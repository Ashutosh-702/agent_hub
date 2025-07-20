import os
import random
from datetime import datetime, timedelta
from chronos_client.client import SchedulerAPIClient

def get_eta_datetime(eta: int) -> str:
    """Calculate ETA in ISO format - copied from vector"""
    return (datetime.utcnow() + timedelta(minutes=eta)).isoformat(timespec="seconds")

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