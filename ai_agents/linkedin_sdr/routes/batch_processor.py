"""
API 2: Batch Processor - Process LinkedIn connections for a batch

WORKFLOW:
1. Input: batch_id
2. Get batch from database using batch_id
3. Check if batch.is_completed == True -> if yes, return "already completed"
4. If batch.is_completed == False:
   a. Find all pending batch_values (status=False) for this batch_id
   b. For each pending batch_value:
      - Extract linkedin_url from data.url
      - Check if lead exists in leads collection for this linkedin_url
      - If lead doesn't exist:
        * Call get_provider_id(linkedin_url) -> fetches from Unipile API
        * Call add_lead(linkedin_url, account_id, provider_id)
      - Send LinkedIn connection request via Unipile API
      - If connection request is successful (status 200):
        * Update batch_value status to True using update_status()
      - If connection request fails:
        * Log error, keep status as False
5. After processing all batch_values:
   - Check if all batch_values have status=True
   - If yes, update batch.is_completed = True
6. Return summary: {processed: X, successful: Y, failed: Z, batch_completed: bool}
"""

import os
import requests
from fastapi import APIRouter, HTTPException
from ..models.batch import get_batch, update_batch_completion
from ..models.batch_value import find_pending_batches, update_status
from ..models.leads import get_lead, get_provider_id, add_lead

router = APIRouter()

@router.post("/process-batch/{batch_id}")
async def process_batch(batch_id: str):
    """
    Process batch connections - API 2
    """
    try:
        # Step 1: Get batch and check if completed
        batch = get_batch(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if batch["is_completed"]:
            return {"message": "Batch already completed", "batch_id": batch_id}
        
        # Step 2: Get all pending batch values (status=False)
        pending_batch_values = find_pending_batches(batch_id)
        
        if not pending_batch_values:
            return {"message": "No pending items to process", "batch_id": batch_id}
        
        # Step 3: Process each pending batch value
        processed = 0
        successful = 0
        failed = 0
        
        for batch_value in pending_batch_values:
            try:
                linkedin_url = batch_value["data"]["url"]
                account_id = batch["account_id"]
                
                # Check if lead exists in leads collection
                existing_lead = get_lead(linkedin_url)
                
                if not existing_lead:
                    # Fetch provider_id and store in LEADS collection
                    provider_id = get_provider_id(linkedin_url)
                    if provider_id:
                        add_lead(linkedin_url, account_id, provider_id)
                    else:
                        print(f"Failed to get provider_id for {linkedin_url}")
                        failed += 1
                        continue
                else:
                    provider_id = existing_lead["provider_id"]
                
                # Send connection request
                connection_sent = send_connection_request(linkedin_url, account_id)
                
                if connection_sent:
                    # Update batch_value status to True
                    update_status(batch_id, linkedin_url, True)
                    successful += 1
                else:
                    failed += 1
                
                processed += 1
                
            except Exception as e:
                print(f"Error processing {linkedin_url}: {e}")
                failed += 1
                processed += 1
        
        # Step 4: Check if all batch_values are now completed
        remaining_pending = find_pending_batches(batch_id)
        batch_completed = len(remaining_pending) == 0
        
        if batch_completed:
            update_batch_completion(batch_id, True)
        
        return {
            "batch_id": batch_id,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "batch_completed": batch_completed,
            "message": "Batch processing completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

def send_connection_request(linkedin_url: str, account_id: str) -> bool:
    """
    Send LinkedIn connection request via Unipile API
    Returns True if successful, False otherwise
    """
    try:
        # TODO: Replace with actual Unipile connection API endpoint
        api_token = os.getenv("UNIPILE_API_TOKEN")
        base_url = os.getenv("UNIPILE_API_URL")
        
        url = f"{base_url}/api/v1/connections"
        headers = {
            "X-API-KEY": api_token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "account_id": account_id,
            "linkedin_url": linkedin_url,
            "action": "connect"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"Connection request sent successfully to {linkedin_url}")
            return True
        else:
            print(f"Failed to send connection to {linkedin_url}: {response.status_code}, {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending connection request to {linkedin_url}: {e}")
        return False



