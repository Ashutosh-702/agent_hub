from fastapi import APIRouter, Form, HTTPException, UploadFile
from ..models.accounts import get_account_id, validate_credentials, create_new_account
from ..models.batch import create_batch
from ..models.batch_value import add_batch
from ..chronos_utils import generate_default_cron_expression, schedule_batch_processing
import csv
import io
from datetime import datetime
from typing import Optional
router = APIRouter()

@router.post('/upload-leads')
async def upload_leads(email: str = Form(...),
                       password: str = Form(...),
                       csv_file: UploadFile = Form(...),
                       cron_expression: Optional[str] = Form(None)) -> dict:
    account_id = await get_account_id(email, password)
    if not account_id:
        account_id = await create_new_account(email, password)
        if not account_id:
            raise HTTPException(status_code=500, detail="ERROR: Failed to create account with Unipile || upload_leads")
    is_valid = await validate_credentials(email, password)
    if not is_valid:
        raise HTTPException(status_code=401, detail=f"ERROR: Invalid credentials || upload_leads")
    
    try:
        batch_id = await create_batch(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ERROR: Failed to create batch || upload_leads: {str(e)}")
    
    try:
        contents = await csv_file.read()
        decoded = contents.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded))

        if not csv_reader.fieldnames or "linkedin_url" not in csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="ERROR: CSV must contain 'linkedin_url' column || upload_leads")
        
        if "task" not in csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="ERROR: CSV must contain 'task' column || upload_leads")

        count = 0
        for row in csv_reader:
            linkedin_url = row.get("linkedin_url")
            task = row.get("task", "connection")
            if linkedin_url:
                await add_batch(batch_id, linkedin_url, task=task)
                count += 1

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ERROR: CSV processing failed || upload_leads: {e}")

    # Handle cron scheduling
    try:
        # If user didn't provide cron expression, will generate default here
        if not cron_expression or cron_expression.strip() == "":
            cron_expression = generate_default_cron_expression()
            print(f"No cron expression provided, using default: {cron_expression}")
        else:
            print(f"User provided cron expression: {cron_expression}")
        
        # Schedule batch processing with Chronos
        scheduler_response = await schedule_batch_processing(batch_id, cron_expression)
        print(f"Successfully scheduled batch {batch_id} with Chronos")
        
    except Exception as e:
        print(f"ERROR: Failed to schedule batch with Chronos: {e}")
        raise HTTPException(status_code=500, detail=f"ERROR: Failed to schedule batch processing || upload_leads: {str(e)}")

    # Return batch details for frontend
    batch_details = {
        "id": batch_id,
        "account_id": email,  # Use email as account identifier  
        "status": "scheduled",    # NEW: Status is now 'scheduled' instead of 'ready'
        "lead_count": count,
        "created_at": datetime.now().isoformat(),
        "scheduled_cron": cron_expression,  # NEW: Show when it's scheduled to run
        "is_completed": False
    }

    return {
        "status": "success",
        "batch_id": batch_id,
        "leads_added": count,
        "scheduled_for": cron_expression,  # Tell user when it will run
        "message": f"Batch scheduled successfully with cron: {cron_expression}",  # Confirmation message
        "batch_details": batch_details  # Frontend can use this to show the new batch
    }