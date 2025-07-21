import os
import random
from datetime import datetime, timedelta
from chronos_client.client import SchedulerAPIClient

def get_eta_datetime(eta: int) -> str:
    """Calculate ETA in ISO format - copied from vector"""
    return (datetime.utcnow() + timedelta(minutes=eta)).isoformat(timespec="seconds")

def generate_default_cron_expression() -> str:
    """
    Generate a default cron expression for 2 hours from now
    Returns format: "minute hour * * *" (specific time today)
    """
    future_time = datetime.now() + timedelta(hours=2)
    minute = future_time.minute
    hour = future_time.hour
    
    # Format used is "minute hour * * *"
    cron_expression = f"{minute} {hour} * * *"
    
    print(f"Generated default cron: {cron_expression} (runs at {hour:02d}:{minute:02d})")
    return cron_expression

async def schedule_batch_processing(batch_id: str, cron_expression: str):
    """
    Schedule batch processing using cron expression with Chronos
    This will call /process-batch/{batch_id} at the scheduled time
    """
    chronos_url = os.getenv("CHRONOS_INTRNL_SVC")
    scheduler_client = SchedulerAPIClient(base_url=chronos_url)
    
    scheduler_payload = {
        "service_name": "linkedin_sdr",
        "topic": "linkedin-batch-processing",  
        "payload": {
            "batch_id": batch_id,
            "action": "process_batch"  
        },
        "cron_expression": cron_expression,  
        "partition_value": batch_id
    }
    
    try:
        print(f"Scheduling batch {batch_id} with cron: {cron_expression}")
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