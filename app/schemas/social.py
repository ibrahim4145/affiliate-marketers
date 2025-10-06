from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Social Schemas
class SocialBase(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    platform: str = Field(..., description="Social media platform (instagram, facebook, x, linkedin, etc.)")
    handle: str = Field(..., description="Social media handle/username")
    page_source: str = Field(..., description="Page source where social handle was found (e.g., '/contact')")

class SocialCreate(SocialBase):
    pass

class SocialUpdate(BaseModel):
    lead_id: Optional[str] = None
    platform: Optional[str] = None
    handle: Optional[str] = None
    page_source: Optional[str] = None

class SocialResponse(SocialBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BulkSocialCreate(BaseModel):
    socials: List[SocialCreate] = Field(..., description="List of social handles to create")

class BulkSocialResponse(BaseModel):
    created_count: int
    created_ids: List[str]
    message: str
