from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
import os
import asyncio
from datetime import datetime

router = APIRouter()

# MongoDB connection
async def get_database():
    mongodb_url = os.getenv("MONGO_URI")
    database_name = os.getenv("MONGO_DB")
    client = AsyncIOMotorClient(mongodb_url)
    return client[database_name]

# Pydantic models
class LeadBase(BaseModel):
    domain: str = Field(..., description="Website domain (e.g., abc.com)")
    title: str = Field(..., description="Website title")
    description: str = Field(..., description="Website description")
    scraper_progress_id: str = Field(..., description="Scraper progress ID")
    scraped: bool = Field(default=False, description="Whether email has been scraped")
    google_done: bool = Field(default=False, description="Whether Google search is done")

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scraper_progress_id: Optional[str] = None
    scraped: Optional[bool] = None
    google_done: Optional[bool] = None

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

@router.post("/leads", response_model=BulkLeadResponse)
async def create_leads(
    bulk_data: BulkLeadCreate,
    db=Depends(get_database)
):
    """
    Create multiple leads in bulk. Duplicates are automatically filtered out.
    """
    try:
        leads_collection = db.leads
        
        # Prepare leads data with timestamps
        leads_to_insert = []
        duplicate_domains = []
        existing_domains = set()
        
        for lead in bulk_data.leads:
            # Check if domain already exists in current batch
            if lead.domain in existing_domains:
                duplicate_domains.append(lead.domain)
                continue
            
            # Check if domain already exists in database
            existing_lead = await leads_collection.find_one({"domain": lead.domain})
            if existing_lead:
                duplicate_domains.append(lead.domain)
                continue
            
            # Add to batch and mark as processed
            lead_doc = lead.dict()
            lead_doc["created_at"] = datetime.utcnow()
            lead_doc["updated_at"] = datetime.utcnow()
            leads_to_insert.append(lead_doc)
            existing_domains.add(lead.domain)
        
        # Insert only unique leads with error handling
        created_count = 0
        created_ids = []
        
        if leads_to_insert:
            try:
                result = await leads_collection.insert_many(leads_to_insert)
                created_count = len(result.inserted_ids)
                created_ids = [str(id) for id in result.inserted_ids]
            except Exception as insert_error:
                # Handle batch insert errors gracefully
                if "duplicate key error" in str(insert_error).lower():
                    # Try inserting one by one to identify which ones are duplicates
                    for lead_doc in leads_to_insert:
                        try:
                            result = await leads_collection.insert_one(lead_doc)
                            created_count += 1
                            created_ids.append(str(result.inserted_id))
                        except Exception as single_error:
                            if "duplicate key error" in str(single_error).lower():
                                duplicate_domains.append(lead_doc["domain"])
                            else:
                                # Log other errors but don't break the process
                                print(f"Error inserting lead {lead_doc.get('domain', 'unknown')}: {str(single_error)}")
                else:
                    # Re-raise non-duplicate errors
                    raise insert_error
        
        # Prepare response message
        message = f"Successfully created {created_count} leads"
        if duplicate_domains:
            message += f". Skipped {len(duplicate_domains)} duplicates: {', '.join(duplicate_domains[:5])}"
            if len(duplicate_domains) > 5:
                message += f" and {len(duplicate_domains) - 5} more"
        
        return BulkLeadResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't break the scraper
        print(f"Unexpected error in create_leads: {str(e)}")
        # Return a successful response with 0 created to keep scraper running
        return BulkLeadResponse(
            created_count=0,
            created_ids=[],
            message=f"Error occurred but scraper continues: {str(e)[:100]}..."
        )

@router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    scraper_progress_id: Optional[str] = None,
    scraped: Optional[bool] = None,
    google_done: Optional[bool] = None,
    db=Depends(get_database)
):
    """
    Get leads with optional filtering.
    """
    try:
        leads_collection = db.leads
        
        # Build filter query
        filter_query = {}
        if scraper_progress_id:
            filter_query["scraper_progress_id"] = scraper_progress_id
        if scraped is not None:
            filter_query["scraped"] = scraped
        if google_done is not None:
            filter_query["google_done"] = google_done
        
        # Get leads with pagination
        cursor = leads_collection.find(filter_query).skip(skip).limit(limit)
        leads = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings and handle backward compatibility
        for lead in leads:
            lead["_id"] = str(lead["_id"])
            # Handle backward compatibility for field names
            if "progress_id" in lead and "scraper_progress_id" not in lead:
                lead["scraper_progress_id"] = lead["progress_id"]
        
        return leads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")

@router.get("/leads/combined-data")
async def get_leads_combined(
    skip: int = 0,
    limit: int = 50,
    scraper_progress_id: Optional[str] = None,
    scraped: Optional[bool] = None,
    google_done: Optional[bool] = None,
    search: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get leads with all related data (industry, emails, phones, socials) in a single response.
    """
    try:
        leads_collection = db.leads
        industries_collection = db.industries
        emails_collection = db.email
        phones_collection = db.phone
        socials_collection = db.social
        
        # Build filter query for leads
        filter_query = {}
        if scraper_progress_id:
            filter_query["scraper_progress_id"] = scraper_progress_id
        if scraped is not None:
            filter_query["scraped"] = scraped
        if google_done is not None:
            filter_query["google_done"] = google_done
        
        # Add search functionality
        if search:
            filter_query["$or"] = [
                {"domain": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Get leads with pagination
        cursor = leads_collection.find(filter_query).skip(skip).limit(limit)
        leads = await cursor.to_list(length=limit)
        
        # Get all industries for mapping
        industries_cursor = industries_collection.find({})
        industries = await industries_cursor.to_list(length=None)
        industries_map = {str(industry["_id"]): industry for industry in industries}
        
        # Get only contacts for the current page leads (more efficient)
        lead_ids = [str(lead["_id"]) for lead in leads]
        
        # Use parallel queries for better performance
        emails_task = emails_collection.find({"lead_id": {"$in": lead_ids}}).to_list(length=None)
        phones_task = phones_collection.find({"lead_id": {"$in": lead_ids}}).to_list(length=None)
        socials_task = socials_collection.find({"lead_id": {"$in": lead_ids}}).to_list(length=None)
        
        # Execute all queries in parallel
        emails, phones, socials = await asyncio.gather(emails_task, phones_task, socials_task)
        
        # Group contacts by lead_id
        emails_by_lead = {}
        phones_by_lead = {}
        socials_by_lead = {}
        
        for email in emails:
            lead_id = str(email["lead_id"])
            if lead_id not in emails_by_lead:
                emails_by_lead[lead_id] = []
            emails_by_lead[lead_id].append({
                "id": str(email["_id"]),
                "email": email["email"],
                "page_source": email["page_source"],
                "created_at": email["created_at"].isoformat() if email.get("created_at") else None,
                "updated_at": email["updated_at"].isoformat() if email.get("updated_at") else None
            })
        
        for phone in phones:
            lead_id = str(phone["lead_id"])
            if lead_id not in phones_by_lead:
                phones_by_lead[lead_id] = []
            phones_by_lead[lead_id].append({
                "id": str(phone["_id"]),
                "phone": phone["phone"],
                "page_source": phone["page_source"],
                "created_at": phone["created_at"].isoformat() if phone.get("created_at") else None,
                "updated_at": phone["updated_at"].isoformat() if phone.get("updated_at") else None
            })
        
        for social in socials:
            lead_id = str(social["lead_id"])
            if lead_id not in socials_by_lead:
                socials_by_lead[lead_id] = []
            socials_by_lead[lead_id].append({
                "id": str(social["_id"]),
                "platform": social["platform"],
                "handle": social["handle"],
                "page_source": social["page_source"],
                "created_at": social["created_at"].isoformat() if social.get("created_at") else None,
                "updated_at": social["updated_at"].isoformat() if social.get("updated_at") else None
            })
        
        # Combine all data
        combined_leads = []
        for lead in leads:
            lead_id = str(lead["_id"])
            
            # Handle backward compatibility for field names
            scraper_progress_id_value = lead.get("scraper_progress_id") or lead.get("progress_id")
            
            # Get industry information by following the chain: lead -> scraper_progress -> industry
            industry_info = None
            if scraper_progress_id_value:
                try:
                    # Step 1: Get scraper progress record to find industry_id
                    progress_collection = db.scraped_progress
                    progress_record = await progress_collection.find_one({"_id": ObjectId(scraper_progress_id_value)})
                    
                    if progress_record:
                        # Step 2: Get industry_id from progress record (handle both old and new field names)
                        industry_id = progress_record.get("industry_id") or progress_record.get("i_id")
                        
                        if industry_id:
                            # Step 3: Find industry by industry_id
                            for industry in industries:
                                if str(industry["_id"]) == industry_id:
                                    industry_info = {
                                        "id": str(industry["_id"]),
                                        "name": industry.get("industry_name", "Unknown"),
                                        "description": industry.get("description", ""),
                                        "created_at": industry.get("created_at", "").isoformat() if industry.get("created_at") else None,
                                        "updated_at": industry.get("updated_at", "").isoformat() if industry.get("updated_at") else None
                                    }
                                    break
                except Exception as e:
                    print(f"Error getting industry info for lead {lead_id}: {str(e)}")
                    # Continue without industry info if there's an error
            
            combined_lead = {
                "id": lead_id,
                "domain": lead["domain"],
                "title": lead["title"],
                "description": lead["description"],
                "scraper_progress_id": scraper_progress_id_value,
                "scraped": lead["scraped"],
                "google_done": lead["google_done"],
                "created_at": lead["created_at"].isoformat() if lead.get("created_at") else None,
                "updated_at": lead["updated_at"].isoformat() if lead.get("updated_at") else None,
                "industry": industry_info,
                "emails": emails_by_lead.get(lead_id, []),
                "phones": phones_by_lead.get(lead_id, []),
                "socials": socials_by_lead.get(lead_id, [])
            }
            combined_leads.append(combined_lead)
        
        # Get total count for pagination
        total_count = await leads_collection.count_documents(filter_query)
        
        return {
            "leads": combined_leads,
            "pagination": {
                "page": (skip // limit) + 1,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": skip + limit < total_count,
                "has_prev": skip > 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve combined leads data: {str(e)}")

@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db=Depends(get_database)
):
    """
    Get a specific lead by ID.
    """
    try:
        leads_collection = db.leads
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(lead_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid lead ID format")
        
        # Find the lead
        lead = await leads_collection.find_one({"_id": object_id})
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Convert ObjectId to string
        lead["_id"] = str(lead["_id"])
        
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve lead: {str(e)}")

@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    db=Depends(get_database)
):
    """
    Update a specific lead.
    """
    try:
        leads_collection = db.leads
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(lead_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid lead ID format")
        
        # Check if lead exists
        existing_lead = await leads_collection.find_one({"_id": object_id})
        if not existing_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Prepare update data (only include non-None fields)
        update_data = {k: v for k, v in lead_update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update the lead
            await leads_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
        
        # Get the updated lead
        updated_lead = await leads_collection.find_one({"_id": object_id})
        updated_lead["_id"] = str(updated_lead["_id"])
        
        return updated_lead
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")

@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db=Depends(get_database)
):
    """
    Delete a specific lead.
    """
    try:
        leads_collection = db.leads
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(lead_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid lead ID format")
        
        # Check if lead exists
        existing_lead = await leads_collection.find_one({"_id": object_id})
        if not existing_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Delete the lead
        result = await leads_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {"message": "Lead deleted successfully", "deleted_id": lead_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete lead: {str(e)}")

@router.get("/leads/stats/summary")
async def get_leads_stats(db=Depends(get_database)):
    """
    Get leads statistics.
    """
    try:
        leads_collection = db.leads
        
        # Get total count
        total_leads = await leads_collection.count_documents({})
        
        # Get scraped count
        scraped_leads = await leads_collection.count_documents({"scraped": True})
        
        # Get google_done count
        google_done_leads = await leads_collection.count_documents({"google_done": True})
        
        # Get leads by scraper_progress_id
        progress_stats = await leads_collection.aggregate([
            {"$group": {"_id": "$scraper_progress_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        return {
            "total_leads": total_leads,
            "scraped_leads": scraped_leads,
            "google_done_leads": google_done_leads,
            "unscraped_leads": total_leads - scraped_leads,
            "progress_stats": progress_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leads statistics: {str(e)}")

@router.post("/leads/check-duplicates")
async def check_duplicates(
    domains: List[str],
    db=Depends(get_database)
):
    """
    Check which domains already exist in the database.
    """
    try:
        leads_collection = db.leads
        
        # Find existing domains
        existing_leads = await leads_collection.find(
            {"domain": {"$in": domains}},
            {"domain": 1, "_id": 0}
        ).to_list(length=None)
        
        existing_domains = [lead["domain"] for lead in existing_leads]
        new_domains = [domain for domain in domains if domain not in existing_domains]
        
        return {
            "total_checked": len(domains),
            "existing_domains": existing_domains,
            "new_domains": new_domains,
            "existing_count": len(existing_domains),
            "new_count": len(new_domains)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check duplicates: {str(e)}")

@router.post("/leads/ensure-unique-index")
async def ensure_unique_index(db=Depends(get_database)):
    """
    Create a unique index on the domain field to prevent duplicates at database level.
    """
    try:
        leads_collection = db.leads
        
        # Create unique index on domain field
        await leads_collection.create_index("domain", unique=True)
        
        return {
            "message": "Unique index created successfully on domain field",
            "index_name": "domain_1"
        }
        
    except Exception as e:
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            return {
                "message": "Unique index already exists on domain field",
                "index_name": "domain_1"
            }
        raise HTTPException(status_code=500, detail=f"Failed to create unique index: {str(e)}")

# Contact models for lead contacts
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

@router.post("/leads/{lead_id}/contacts", response_model=LeadContactsResponse)
async def add_lead_contacts(
    lead_id: str,
    contacts_data: LeadContactsData,
    db=Depends(get_database)
):
    """
    Add contacts to a lead and update its scraped status.
    Handles cases where no contacts were found (only updates scraped status).
    """
    try:
        leads_collection = db.leads
        emails_collection = db.email
        phones_collection = db.phone
        socials_collection = db.social
        
        # Initialize response counters
        lead_updated = False
        emails_created = 0
        phones_created = 0
        socials_created = 0
        total_contacts_created = 0
        
        # Step 1: Update lead scraped status
        try:
            lead_object_id = ObjectId(lead_id)
            
            # Update the lead's scraped status
            update_result = await leads_collection.update_one(
                {"_id": lead_object_id},
                {
                    "$set": {
                        "scraped": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                lead_updated = True
            else:
                # Check if lead exists
                lead_exists = await leads_collection.find_one({"_id": lead_object_id})
                if not lead_exists:
                    raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")
                
        except Exception as e:
            if "Invalid ObjectId" in str(e):
                raise HTTPException(status_code=400, detail=f"Invalid lead ID format: {lead_id}")
            raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")
        
        # Step 2: Process contacts if any exist
        contacts = contacts_data
        
        # Process emails
        if contacts.emails:
            emails_to_insert = []
            existing_emails = set()
            
            for email in contacts.emails:
                # Create unique key for duplicate checking
                unique_key = f"{email.email}_{lead_id}"
                
                if unique_key in existing_emails:
                    continue
                
                # Check if email already exists in database
                existing_email = await emails_collection.find_one({
                    "email": email.email,
                    "lead_id": lead_id
                })
                if existing_email:
                    continue
                
                # Add to batch
                email_doc = {
                    "lead_id": lead_id,
                    "email": email.email,
                    "page_source": email.page_source,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                emails_to_insert.append(email_doc)
                existing_emails.add(unique_key)
            
            # Insert emails
            if emails_to_insert:
                try:
                    result = await emails_collection.insert_many(emails_to_insert)
                    emails_created = len(result.inserted_ids)
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for email_doc in emails_to_insert:
                            try:
                                await emails_collection.insert_one(email_doc)
                                emails_created += 1
                            except Exception:
                                pass  # Skip duplicates
                    else:
                        print(f"Error inserting emails: {str(insert_error)}")
        
        # Process phones
        if contacts.phones:
            phones_to_insert = []
            existing_phones = set()
            
            for phone in contacts.phones:
                # Create unique key for duplicate checking
                unique_key = f"{phone.phone}_{lead_id}"
                
                if unique_key in existing_phones:
                    continue
                
                # Check if phone already exists in database
                existing_phone = await phones_collection.find_one({
                    "phone": phone.phone,
                    "lead_id": lead_id
                })
                if existing_phone:
                    continue
                
                # Add to batch
                phone_doc = {
                    "lead_id": lead_id,
                    "phone": phone.phone,
                    "page_source": phone.page_source,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                phones_to_insert.append(phone_doc)
                existing_phones.add(unique_key)
            
            # Insert phones
            if phones_to_insert:
                try:
                    result = await phones_collection.insert_many(phones_to_insert)
                    phones_created = len(result.inserted_ids)
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for phone_doc in phones_to_insert:
                            try:
                                await phones_collection.insert_one(phone_doc)
                                phones_created += 1
                            except Exception:
                                pass  # Skip duplicates
                    else:
                        print(f"Error inserting phones: {str(insert_error)}")
        
        # Process socials
        if contacts.socials:
            socials_to_insert = []
            existing_socials = set()
            
            for social in contacts.socials:
                # Create unique key for duplicate checking
                unique_key = f"{social.platform}_{social.handle}_{lead_id}"
                
                if unique_key in existing_socials:
                    continue
                
                # Check if social already exists in database
                existing_social = await socials_collection.find_one({
                    "platform": social.platform,
                    "handle": social.handle,
                    "lead_id": lead_id
                })
                if existing_social:
                    continue
                
                # Add to batch
                social_doc = {
                    "lead_id": lead_id,
                    "platform": social.platform,
                    "handle": social.handle,
                    "page_source": social.page_source,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                socials_to_insert.append(social_doc)
                existing_socials.add(unique_key)
            
            # Insert socials
            if socials_to_insert:
                try:
                    result = await socials_collection.insert_many(socials_to_insert)
                    socials_created = len(result.inserted_ids)
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for social_doc in socials_to_insert:
                            try:
                                await socials_collection.insert_one(social_doc)
                                socials_created += 1
                            except Exception:
                                pass  # Skip duplicates
                    else:
                        print(f"Error inserting socials: {str(insert_error)}")
        
        # Calculate totals
        total_contacts_created = emails_created + phones_created + socials_created
        
        # Prepare response message
        message_parts = []
        if lead_updated:
            message_parts.append("lead marked as scraped")
        
        if emails_created > 0:
            message_parts.append(f"{emails_created} emails")
        if phones_created > 0:
            message_parts.append(f"{phones_created} phones")
        if socials_created > 0:
            message_parts.append(f"{socials_created} social handles")
        
        if not message_parts:
            message = "Lead marked as scraped (no new contacts found)"
        else:
            message = f"Successfully processed: {', '.join(message_parts)}"
        
        return LeadContactsResponse(
            lead_updated=lead_updated,
            emails_created=emails_created,
            phones_created=phones_created,
            socials_created=socials_created,
            total_contacts_created=total_contacts_created,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't break the scraper
        print(f"Unexpected error in add_lead_contacts: {str(e)}")
        # Return a successful response to keep scraper running
        return LeadContactsResponse(
            lead_updated=False,
            emails_created=0,
            phones_created=0,
            socials_created=0,
            total_contacts_created=0,
            message=f"Error occurred but scraper continues: {str(e)[:100]}..."
        )
