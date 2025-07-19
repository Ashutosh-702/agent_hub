from pydantic import BaseModel
from typing import Optional

class Account(BaseModel):
    linkedin_email: str
    linkedin_password: str
    account_id: str

class Lead(BaseModel):
    linkedin_url: str
    account_id: str
    provider_id: str

class BatchValue(BaseModel):
    batch_id: str
    data: dict  # {"url": "", "task": "messaging/connection"}
    status: Optional[bool] = None  # completed or not

class Batch(BaseModel):
    is_completed: bool  # connections sent or not
    account_id: str
    batch_id: str  # UUID generated

