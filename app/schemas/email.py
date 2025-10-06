from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# Email Schemas
class EmailBase(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    email: EmailStr = Field(..., description="Email address")
    page_source: str = Field(..., description="Page source where email was found (e.g., '/contact')")

class EmailCreate(EmailBase):
    pass

class EmailUpdate(BaseModel):
    lead_id: Optional[str] = None
    email: Optional[EmailStr] = None
    page_source: Optional[str] = None

class EmailResponse(EmailBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BulkEmailCreate(BaseModel):
    emails: List[EmailCreate] = Field(..., description="List of emails to create")

class BulkEmailResponse(BaseModel):
    created_count: int
    created_ids: List[str]
    message: str
