from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
import os
from datetime import datetime

router = APIRouter()

# MongoDB connection
async def get_database():
    mongodb_url = os.getenv("MONGO_URI")
    database_name = os.getenv("MONGO_DB")
    client = AsyncIOMotorClient(mongodb_url)
    return client[database_name]

# Pydantic models
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

@router.post("/email", response_model=BulkEmailResponse)
async def create_emails(
    bulk_data: BulkEmailCreate,
    db=Depends(get_database)
):
    """
    Create multiple emails in bulk. Duplicates are automatically filtered out.
    """
    try:
        emails_collection = db.email
        
        # Prepare emails data with timestamps
        emails_to_insert = []
        duplicate_emails = []
        existing_emails = set()
        
        for email in bulk_data.emails:
            # Create unique key for duplicate checking (email + lead_id)
            unique_key = f"{email.email}_{email.lead_id}"
            
            # Check if email already exists in current batch
            if unique_key in existing_emails:
                duplicate_emails.append(f"{email.email} (lead: {email.lead_id})")
                continue
            
            # Check if email already exists in database
            existing_email = await emails_collection.find_one({
                "email": email.email,
                "lead_id": email.lead_id
            })
            if existing_email:
                duplicate_emails.append(f"{email.email} (lead: {email.lead_id})")
                continue
            
            # Add to batch and mark as processed
            email_doc = email.dict()
            email_doc["created_at"] = datetime.utcnow()
            email_doc["updated_at"] = datetime.utcnow()
            emails_to_insert.append(email_doc)
            existing_emails.add(unique_key)
        
        # Insert only unique emails with error handling
        created_count = 0
        created_ids = []
        
        if emails_to_insert:
            try:
                result = await emails_collection.insert_many(emails_to_insert)
                created_count = len(result.inserted_ids)
                created_ids = [str(id) for id in result.inserted_ids]
            except Exception as insert_error:
                # Handle batch insert errors gracefully
                if "duplicate key error" in str(insert_error).lower():
                    # Try inserting one by one to identify which ones are duplicates
                    for email_doc in emails_to_insert:
                        try:
                            result = await emails_collection.insert_one(email_doc)
                            created_count += 1
                            created_ids.append(str(result.inserted_id))
                        except Exception as single_error:
                            if "duplicate key error" in str(single_error).lower():
                                duplicate_emails.append(f"{email_doc['email']} (lead: {email_doc['lead_id']})")
                            else:
                                # Log other errors but don't break the process
                                print(f"Error inserting email {email_doc.get('email', 'unknown')}: {str(single_error)}")
                else:
                    # Re-raise non-duplicate errors
                    raise insert_error
        
        # Prepare response message
        message = f"Successfully created {created_count} emails"
        if duplicate_emails:
            message += f". Skipped {len(duplicate_emails)} duplicates: {', '.join(duplicate_emails[:3])}"
            if len(duplicate_emails) > 3:
                message += f" and {len(duplicate_emails) - 3} more"
        
        return BulkEmailResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't break the scraper
        print(f"Unexpected error in create_emails: {str(e)}")
        # Return a successful response with 0 created to keep scraper running
        return BulkEmailResponse(
            created_count=0,
            created_ids=[],
            message=f"Error occurred but scraper continues: {str(e)[:100]}..."
        )

@router.get("/email", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[str] = None,
    page_source: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get emails with optional filtering.
    """
    try:
        emails_collection = db.email
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = lead_id
        if page_source:
            filter_query["page_source"] = page_source
        
        # Get emails with pagination
        cursor = emails_collection.find(filter_query).skip(skip).limit(limit)
        emails = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for email in emails:
            email["_id"] = str(email["_id"])
        
        return emails
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emails: {str(e)}")

@router.get("/email/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    db=Depends(get_database)
):
    """
    Get a specific email by ID.
    """
    try:
        emails_collection = db.email
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(email_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid email ID format")
        
        # Find the email
        email = await emails_collection.find_one({"_id": object_id})
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Convert ObjectId to string
        email["_id"] = str(email["_id"])
        
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve email: {str(e)}")

@router.put("/email/{email_id}", response_model=EmailResponse)
async def update_email(
    email_id: str,
    email_update: EmailUpdate,
    db=Depends(get_database)
):
    """
    Update a specific email.
    """
    try:
        emails_collection = db.email
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(email_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid email ID format")
        
        # Check if email exists
        existing_email = await emails_collection.find_one({"_id": object_id})
        if not existing_email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Prepare update data (only include non-None fields)
        update_data = {k: v for k, v in email_update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update the email
            await emails_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
        
        # Get the updated email
        updated_email = await emails_collection.find_one({"_id": object_id})
        updated_email["_id"] = str(updated_email["_id"])
        
        return updated_email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update email: {str(e)}")

@router.delete("/email/{email_id}")
async def delete_email(
    email_id: str,
    db=Depends(get_database)
):
    """
    Delete a specific email.
    """
    try:
        emails_collection = db.email
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(email_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid email ID format")
        
        # Check if email exists
        existing_email = await emails_collection.find_one({"_id": object_id})
        if not existing_email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Delete the email
        result = await emails_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return {"message": "Email deleted successfully", "deleted_id": email_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")

@router.get("/email/stats/summary")
async def get_emails_stats(db=Depends(get_database)):
    """
    Get emails statistics.
    """
    try:
        emails_collection = db.email
        
        # Get total count
        total_emails = await emails_collection.count_documents({})
        
        # Get emails by lead_id
        lead_stats = await emails_collection.aggregate([
            {"$group": {"_id": "$lead_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        # Get emails by page_source
        page_stats = await emails_collection.aggregate([
            {"$group": {"_id": "$page_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        return {
            "total_emails": total_emails,
            "lead_stats": lead_stats,
            "page_source_stats": page_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get emails statistics: {str(e)}")

@router.post("/email/ensure-unique-index")
async def ensure_unique_index(db=Depends(get_database)):
    """
    Create a unique index on email and lead_id combination to prevent duplicates.
    """
    try:
        emails_collection = db.email
        
        # Create unique compound index on email and lead_id
        await emails_collection.create_index([("email", 1), ("lead_id", 1)], unique=True)
        
        return {
            "message": "Unique compound index created successfully on email and lead_id",
            "index_name": "email_1_lead_id_1"
        }
        
    except Exception as e:
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            return {
                "message": "Unique compound index already exists on email and lead_id",
                "index_name": "email_1_lead_id_1"
            }
        raise HTTPException(status_code=500, detail=f"Failed to create unique index: {str(e)}")
