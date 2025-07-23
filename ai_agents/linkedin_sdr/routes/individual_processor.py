from fastapi import APIRouter
from linkedin_sdr.models.batch import get_batch, update_batch_completion
from linkedin_sdr.models.batch_value import find_pending_batches, update_status, get_batch_value_by_url
from linkedin_sdr.models.leads import get_lead, get_provider_id, add_lead
from linkedin_sdr.unipile_service import send_connection_request

router = APIRouter()

@router.post("/process-individual-connection")
async def process_individual_connection(batch_id: str, linkedin_url: str):
    """
    Process a single connection - triggered by Chronos scheduling
    This contains the ORIGINAL connection logic from batch_processor (commented out section)
    """
    try:
        # Get batch info
        batch = await get_batch(batch_id)
        if not batch:
            print(f"Batch {batch_id} not found")
            return {"error": "Batch not found"}
        
        account_id = batch["account_id"]
        
        # Check if this batch_value still needs processing
        batch_value = await get_batch_value_by_url(batch_id, linkedin_url)
        if not batch_value:
            print(f"Batch value not found for {linkedin_url}")
            return {"error": "Batch value not found"}
            
        if batch_value.get("status"):  # status = True means completed
            print(f"Connection already processed for {linkedin_url}")
            return {"message": "Already processed"}
        
        # Only process if task is "connection"
        if batch_value["data"].get("task") != "connection":
            print(f"Skipping non-connection task for {linkedin_url}")
            return {"message": "Non-connection task skipped"}
        
        # ORIGINAL PROCESSING LOGIC (from commented section in batch_processor)
        existing_lead = await get_lead(linkedin_url)
        
        if not existing_lead:
            # Fetch provider_id and store in LEADS collection
            provider_id = await get_provider_id(linkedin_url)
            if provider_id:
                await add_lead(linkedin_url, account_id, provider_id)
            else:
                print(f"Failed to get provider_id for {linkedin_url}")
                return {"error": "Failed to get provider_id"}
        else:
            provider_id = existing_lead["provider_id"]
        
        # Send connection request (using updated unipile_service)
        connection_response = await send_connection_request(provider_id, account_id)
        
        if connection_response:  # connection_response is now a dict, not boolean
            await update_status(batch_id, linkedin_url, True)
            print(f"Connection sent successfully to {linkedin_url}")
            
            # Check if batch is completed (from original logic)
            remaining_pending = await find_pending_batches(batch_id)
            if len(remaining_pending) == 0:
                await update_batch_completion(batch_id, True)
                print(f"Batch {batch_id} completed")
            
            return {
                "message": "Connection sent successfully", 
                "linkedin_url": linkedin_url,
                "provider_id": provider_id,
                "batch_id": batch_id
            }
        else:
            print(f"Failed to send connection to {linkedin_url}")
            return {"error": "Failed to send connection"}
            
    except Exception as e:
        print(f"Error processing individual connection for {linkedin_url}: {e}")
        return {"error": str(e)} 