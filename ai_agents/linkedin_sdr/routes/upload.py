from fastapi import APIRouter, Form, HTTPException, UploadFile
from ..models.accounts import get_account_id, validate_credentials, create_new_account
from ..models.batch import create_batch
from ..models.batch_value import add_batch
import csv
import io
router = APIRouter()

@router.post('/upload-leads')
async def upload_leads(email: str = Form(...),
                       password: str = Form(...),
                       csv_file: UploadFile = Form(...)) -> dict:
    is_valid, message = await validate_credentials(email, password)
    if not is_valid:
        print(f"Account not found, creating new account for {email}")
        account_id = await create_new_account(email, password)
        if not account_id:
            raise HTTPException(status_code=500, detail="Failed to create account with Unipile")
    else:
        account_id = await get_account_id(email, password)
        if not account_id:
            raise HTTPException(status_code=404, detail="ERROR: Account ID not found || upload_leads")
    
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
            task = row.get("task", "connection")  # Read task from CSV, default to "connection"
            if linkedin_url:
                await add_batch(batch_id, linkedin_url, task=task)
                count += 1

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ERROR: CSV processing failed || upload_leads: {e}")

    return {
        "status": "success",
        "batch_id": batch_id,
        "leads_added": count}