from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
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
class LeadBase(BaseModel):
    domain: str = Field(..., description="Website domain (e.g., abc.com)")
    title: str = Field(..., description="Website title")
    description: str = Field(..., description="Website description")
    progress_id: str = Field(..., description="Scraper progress ID")
    scraped: bool = Field(default=False, description="Whether email has been scraped")
    google_done: bool = Field(default=False, description="Whether Google search is done")

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    progress_id: Optional[str] = None
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
    Create multiple leads in bulk.
    """
    try:
        leads_collection = db.leads
        
        # Prepare leads data with timestamps
        leads_to_insert = []
        for lead in bulk_data.leads:
            lead_doc = lead.dict()
            lead_doc["created_at"] = datetime.utcnow()
            lead_doc["updated_at"] = datetime.utcnow()
            leads_to_insert.append(lead_doc)
        
        # Insert all leads
        result = await leads_collection.insert_many(leads_to_insert)
        
        return BulkLeadResponse(
            created_count=len(result.inserted_ids),
            created_ids=[str(id) for id in result.inserted_ids],
            message=f"Successfully created {len(result.inserted_ids)} leads"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create leads: {str(e)}")

@router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    progress_id: Optional[str] = None,
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
        if progress_id:
            filter_query["progress_id"] = progress_id
        if scraped is not None:
            filter_query["scraped"] = scraped
        if google_done is not None:
            filter_query["google_done"] = google_done
        
        # Get leads with pagination
        cursor = leads_collection.find(filter_query).skip(skip).limit(limit)
        leads = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        
        return leads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")

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
        
        # Get leads by progress_id
        progress_stats = await leads_collection.aggregate([
            {"$group": {"_id": "$progress_id", "count": {"$sum": 1}}},
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
