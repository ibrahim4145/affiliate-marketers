from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# Lead Schemas
class LeadBase(BaseModel):
    domain: str = Field(..., description="Website domain (e.g., abc.com)")
    title: str = Field(..., description="Website title")
    description: str = Field(..., description="Website description")
    scraper_progress_id: str = Field(..., description="Scraper progress ID")
    scraped: bool = Field(default=False, description="Whether email has been scraped")
    google_done: bool = Field(default=False, description="Whether Google search is done")
    visible: bool = Field(default=False, description="Whether lead is visible on main leads page")

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scraper_progress_id: Optional[str] = None
    scraped: Optional[bool] = None
    google_done: Optional[bool] = None
    visible: Optional[bool] = None

class LeadResponse(LeadBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BulkLeadCreate(BaseModel):
    leads: List[LeadCreate] = Field(..., description="List of leads to create")

class BulkLeadResponse(BaseModel):
    created_count: int
    created_ids: List[str]
    message: str

# Contact schemas for lead contacts
class EmailContact(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    page_source: str = Field(..., description="Page source where email was found (e.g., '/contact')")

class PhoneContact(BaseModel):
    phone: str = Field(..., description="Phone number in any format")
    page_source: str = Field(..., description="Page source where phone was found (e.g., '/contact')")

class SocialContact(BaseModel):
    platform: str = Field(..., description="Social media platform (instagram, facebook, x, linkedin, etc.)")
    handle: str = Field(..., description="Social media handle/username")
    page_source: str = Field(..., description="Page source where social handle was found (e.g., '/contact')")

class LeadContactsData(BaseModel):
    emails: List[EmailContact] = Field(default=[], description="List of emails to create")
    phones: List[PhoneContact] = Field(default=[], description="List of phones to create")
    socials: List[SocialContact] = Field(default=[], description="List of social handles to create")

class LeadContactsResponse(BaseModel):
    lead_updated: bool
    emails_created: int
    phones_created: int
    socials_created: int
    total_contacts_created: int
    message: str
