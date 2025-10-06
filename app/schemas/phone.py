from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Phone Schemas
class PhoneBase(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    phone: str = Field(..., description="Phone number in any format")
    page_source: str = Field(..., description="Page source where phone was found (e.g., '/contact')")

class PhoneCreate(PhoneBase):
    pass

class PhoneUpdate(BaseModel):
    lead_id: Optional[str] = None
    phone: Optional[str] = None
    page_source: Optional[str] = None

class PhoneResponse(PhoneBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BulkPhoneCreate(BaseModel):
    phones: List[PhoneCreate] = Field(..., description="List of phones to create")

class BulkPhoneResponse(BaseModel):
    created_count: int
    created_ids: List[str]
    message: str
