import os
import requests
from fastapi import APIRouter, HTTPException
from ..models.batch import get_batch, update_batch_completion
from ..models.batch_value import find_pending_batches, update_status
#from ..models.leads import get_lead, get_provider_id, add_lead
from ..chronos_utils import schedule_connection_processing

router = APIRouter()

@router.post("/process-batch/{batch_id}")
async def process_batch(batch_id: str):
    """
    Process batch connections - API 2
    SCHEDULES CONNECTIONS VIA CHRONOS INSTEAD OF IMMEDIATE PROCESSING
    """
    try:
        batch = await get_batch(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if batch["is_completed"]:
            return {"message": "Batch already completed", "batch_id": batch_id}
        
        pending_batch_values = await find_pending_batches(batch_id)
        
        if not pending_batch_values:
            return {"message": "No pending items to process", "batch_id": batch_id}
        
        # COMMENTED OUT: ORIGINAL IMMEDIATE PROCESSING
        # processed = 0
        # successful = 0
        # failed = 0
        # 
        # for batch_value in pending_batch_values:
        #     try:
        #         if batch_value["data"].get("task") != "connection":
        #             continue
        #             
        #         linkedin_url = batch_value["data"]["url"]
        #         account_id = batch["account_id"]
        #         
        #         existing_lead = await get_lead(linkedin_url)
        #         
        #         if not existing_lead:
        #             provider_id = await get_provider_id(linkedin_url)
        #             if provider_id:
        #                 await add_lead(linkedin_url, account_id, provider_id)
        #             else:
        #                 print(f"Failed to get provider_id for {linkedin_url}")
        #                 failed += 1
        #                 continue
        #         else:
        #             provider_id = existing_lead["provider_id"]
        #         
        #         connection_sent = send_connection_request(provider_id, account_id)
        #         
        #         if connection_sent:
        #             await update_status(batch_id, linkedin_url, True)
        #             successful += 1
        #         else:
        #             failed += 1
        #         
        #         processed += 1
        #         
        #     except Exception as e:
        #         print(f"Error processing {linkedin_url}: {e}")
        #         failed += 1
        #         processed += 1
        # 
        # remaining_pending = await find_pending_batches(batch_id)
        # batch_completed = len(remaining_pending) == 0
        # 
        # if batch_completed:
        #     await update_batch_completion(batch_id, True)
        # 
        # return {
        #     "batch_id": batch_id,
        #     "processed": processed,
        #     "successful": successful,
        #     "failed": failed,
        #     "batch_completed": batch_completed,
        #     "message": "Batch processing completed"
        # }

        # NEW: CHRONOS SCHEDULING LOGIC
        scheduled_count = 0
        failed_to_schedule = 0
        
        for batch_value in pending_batch_values:
            try:
                if batch_value["data"].get("task") != "connection":
                    continue
                    
                linkedin_url = batch_value["data"]["url"]
                
                # Schedule this connection for later processing via Chronos
                await schedule_connection_processing(batch_id, linkedin_url)
                scheduled_count += 1
                
            except Exception as e:
                print(f"Error scheduling {linkedin_url}: {e}")
                failed_to_schedule += 1
        
        return {
            "batch_id": batch_id,
            "scheduled": scheduled_count,
            "failed_to_schedule": failed_to_schedule,
            "message": f"Scheduled {scheduled_count} connections for processing with random delays (5-35 mins each)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling batch: {str(e)}")

# def send_connection_request(provider_id: str, account_id: str) -> bool:
#     """
#     Send LinkedIn connection request via Unipile API
#     Returns True if successful, False otherwise
#     """
#     try:
#         api_token = os.getenv("UNIPILE_API_TOKEN")
#         base_url = os.getenv("UNIPILE_API_URL")
        
#         url = f"{base_url}/users/invite"
#         headers = {
#             "X-API-KEY": api_token,
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             "provider_id": provider_id,
#             "account_id": account_id,
#             "message": "I'd like to connect with you on LinkedIn."
#         }
        
#         response = requests.post(url, headers=headers, json=payload)
        
#         if response.status_code == 201:
#             print(f"Connection request sent successfully to provider_id: {provider_id}")
#             return True
#         else:
#             print(f"Failed to send connection to provider_id {provider_id}: {response.status_code}, {response.text}")
#             return False
            
#     except Exception as e:
#         print(f"Error sending connection request to provider_id {provider_id}: {e}")
#         return False



