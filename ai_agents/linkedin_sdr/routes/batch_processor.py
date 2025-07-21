from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..models.batch import get_batch, update_batch_completion, get_all_batches
from ..models.batch_value import find_pending_batches, update_status, get_all_batch_values
from ..models.leads import get_lead, get_provider_id, add_lead
from ..unipile_service import send_connection_request
from typing import Optional

router = APIRouter()

async def process_batch_with_limit(batch_id: str, limit: Optional[int] = None):
    """
    Process LinkedIn connections with optional limit - CORE PROCESSING LOGIC ONLY
    
    Args:
        batch_id: The batch to process
        limit: Maximum number of LinkedIn URLs to process (None = process all)
    
    Returns:
        Dict with basic processing results: {processed, successful, failed, batch_completed}
    """
    batch = await get_batch(batch_id)
    if not batch:
        raise Exception("Batch not found")
    
    if batch["is_completed"]:
        return {"processed": 0, "successful": 0, "failed": 0, "batch_completed": True, "message": "Batch already completed"}
    
    # OPTIMIZATION: Only fetch the number of records we need to process
    pending_batch_values = await find_pending_batches(batch_id, limit=limit)
    
    if not pending_batch_values:
        return {"processed": 0, "successful": 0, "failed": 0, "batch_completed": False, "message": "No pending items to process"}
    
    # CORE PROCESSING LOGIC
    processed = 0
    successful = 0
    failed = 0
    
    for batch_value in pending_batch_values:
        try:
            if batch_value["data"].get("task") != "connection":
                continue
                
            linkedin_url = batch_value["data"]["url"]
            account_id = batch["account_id"]
            
            existing_lead = await get_lead(linkedin_url)
            
            if not existing_lead:
                provider_id = await get_provider_id(linkedin_url, account_id)
                if provider_id:
                    await add_lead(linkedin_url, account_id, provider_id)
                else:
                    print(f"Failed to get provider_id for {linkedin_url}")
                    failed += 1
                    processed += 1
                    continue
            else:
                provider_id = existing_lead["provider_id"]
            
            connection_sent = await send_connection_request(provider_id, account_id)
            
            if connection_sent:
                await update_status(batch_id, linkedin_url, True)
                successful += 1
            else:
                failed += 1
            
            processed += 1
            
        except Exception as e:
            print(f"Error processing {linkedin_url}: {e}")
            failed += 1
            processed += 1
    
    # Check if batch is completed
    remaining_pending = await find_pending_batches(batch_id)  # Get all remaining to check completion
    batch_completed = len(remaining_pending) == 0
    
    if batch_completed:
        await update_batch_completion(batch_id, True)
    
    return {
        "processed": processed,
        "successful": successful,
        "failed": failed,
        "batch_completed": batch_completed
    }

@router.post("/process-batch/{batch_id}")
async def process_batch(batch_id: str):
    """
    Process batch connections - API 2  
    PROCESSES CONNECTIONS IMMEDIATELY (ORIGINAL WORKING VERSION)
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
        
        # Call the core processing function with no limit (process all URLs)
        processing_result = await process_batch_with_limit(batch_id, limit=None)
        
        # Get all batches to return to frontend
        all_batches_raw = await get_all_batches()
        
        # Format batches for frontend
        formatted_batches = []
        for batch in all_batches_raw:
            # Get batch values to count leads and determine status
            batch_values = await get_all_batch_values(batch["batch_id"])
            total_leads = len(batch_values)
            completed_leads = len([bv for bv in batch_values if bv.get("status", False)])
            
            # Determine status
            if batch.get("is_completed", False):
                status = "completed"
            elif batch["batch_id"] == batch_id and processing_result["batch_completed"]:
                status = "completed"  # This batch was just completed
            elif batch["batch_id"] == batch_id:
                status = "processing"  # This batch was just started
            elif completed_leads > 0:
                status = "processing"
            else:
                status = "ready"
            
            # Safe creation time extraction
            creation_time = "unknown"
            if batch.get("_id") and hasattr(batch["_id"], "generation_time"):
                try:
                    creation_time = batch["_id"].generation_time.isoformat()
                except:
                    creation_time = datetime.now().isoformat()
            else:
                creation_time = datetime.now().isoformat()
            
            formatted_batch = {
                "id": batch["batch_id"],
                "account_id": batch["account_id"],
                "status": status,
                "lead_count": total_leads,
                "created_at": creation_time,
                "progress": {
                    "total": total_leads,
                    "completed": completed_leads
                } if status == "processing" else None
            }
            formatted_batches.append(formatted_batch)

        return {
            "batch_id": batch_id,
            "processed": processing_result["processed"],
            "successful": processing_result["successful"],
            "failed": processing_result["failed"],
            "batch_completed": processing_result["batch_completed"],
            "message": "Batch processing completed",
            "all_batches": formatted_batches  # Frontend can use this to show the new batch
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")


