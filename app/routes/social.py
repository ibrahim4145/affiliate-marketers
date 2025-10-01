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

@router.post("/social", response_model=BulkSocialResponse)
async def create_socials(
    bulk_data: BulkSocialCreate,
    db=Depends(get_database)
):
    """
    Create multiple social handles in bulk. Duplicates are automatically filtered out.
    """
    try:
        socials_collection = db.social
        
        # Prepare socials data with timestamps
        socials_to_insert = []
        duplicate_socials = []
        existing_socials = set()
        
        for social in bulk_data.socials:
            # Create unique key for duplicate checking (platform + handle + lead_id)
            unique_key = f"{social.platform}_{social.handle}_{social.lead_id}"
            
            # Check if social already exists in current batch
            if unique_key in existing_socials:
                duplicate_socials.append(f"{social.platform}:{social.handle} (lead: {social.lead_id})")
                continue
            
            # Check if social already exists in database
            existing_social = await socials_collection.find_one({
                "platform": social.platform,
                "handle": social.handle,
                "lead_id": social.lead_id
            })
            if existing_social:
                duplicate_socials.append(f"{social.platform}:{social.handle} (lead: {social.lead_id})")
                continue
            
            # Add to batch and mark as processed
            social_doc = social.dict()
            social_doc["created_at"] = datetime.utcnow()
            social_doc["updated_at"] = datetime.utcnow()
            socials_to_insert.append(social_doc)
            existing_socials.add(unique_key)
        
        # Insert only unique socials
        created_count = 0
        created_ids = []
        
        if socials_to_insert:
            result = await socials_collection.insert_many(socials_to_insert)
            created_count = len(result.inserted_ids)
            created_ids = [str(id) for id in result.inserted_ids]
        
        # Prepare response message
        message = f"Successfully created {created_count} social handles"
        if duplicate_socials:
            message += f". Skipped {len(duplicate_socials)} duplicates: {', '.join(duplicate_socials[:3])}"
            if len(duplicate_socials) > 3:
                message += f" and {len(duplicate_socials) - 3} more"
        
        return BulkSocialResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create social handles: {str(e)}")

@router.get("/social", response_model=List[SocialResponse])
async def get_socials(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[str] = None,
    platform: Optional[str] = None,
    page_source: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get social handles with optional filtering.
    """
    try:
        socials_collection = db.social
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = lead_id
        if platform:
            filter_query["platform"] = platform
        if page_source:
            filter_query["page_source"] = page_source
        
        # Get socials with pagination
        cursor = socials_collection.find(filter_query).skip(skip).limit(limit)
        socials = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for social in socials:
            social["_id"] = str(social["_id"])
        
        return socials
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve social handles: {str(e)}")

@router.get("/social/{social_id}", response_model=SocialResponse)
async def get_social(
    social_id: str,
    db=Depends(get_database)
):
    """
    Get a specific social handle by ID.
    """
    try:
        socials_collection = db.social
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(social_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid social ID format")
        
        # Find the social
        social = await socials_collection.find_one({"_id": object_id})
        if not social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        # Convert ObjectId to string
        social["_id"] = str(social["_id"])
        
        return social
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve social handle: {str(e)}")

@router.put("/social/{social_id}", response_model=SocialResponse)
async def update_social(
    social_id: str,
    social_update: SocialUpdate,
    db=Depends(get_database)
):
    """
    Update a specific social handle.
    """
    try:
        socials_collection = db.social
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(social_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid social ID format")
        
        # Check if social exists
        existing_social = await socials_collection.find_one({"_id": object_id})
        if not existing_social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        # Prepare update data (only include non-None fields)
        update_data = {k: v for k, v in social_update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update the social
            await socials_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
        
        # Get the updated social
        updated_social = await socials_collection.find_one({"_id": object_id})
        updated_social["_id"] = str(updated_social["_id"])
        
        return updated_social
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update social handle: {str(e)}")

@router.delete("/social/{social_id}")
async def delete_social(
    social_id: str,
    db=Depends(get_database)
):
    """
    Delete a specific social handle.
    """
    try:
        socials_collection = db.social
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(social_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid social ID format")
        
        # Check if social exists
        existing_social = await socials_collection.find_one({"_id": object_id})
        if not existing_social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        # Delete the social
        result = await socials_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        return {"message": "Social handle deleted successfully", "deleted_id": social_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete social handle: {str(e)}")

@router.get("/social/stats/summary")
async def get_socials_stats(db=Depends(get_database)):
    """
    Get social handles statistics.
    """
    try:
        socials_collection = db.social
        
        # Get total count
        total_socials = await socials_collection.count_documents({})
        
        # Get socials by lead_id
        lead_stats = await socials_collection.aggregate([
            {"$group": {"_id": "$lead_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        # Get socials by platform
        platform_stats = await socials_collection.aggregate([
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        # Get socials by page_source
        page_stats = await socials_collection.aggregate([
            {"$group": {"_id": "$page_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        return {
            "total_socials": total_socials,
            "lead_stats": lead_stats,
            "platform_stats": platform_stats,
            "page_source_stats": page_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get social handles statistics: {str(e)}")

@router.post("/social/ensure-unique-index")
async def ensure_unique_index(db=Depends(get_database)):
    """
    Create a unique index on platform, handle, and lead_id combination to prevent duplicates.
    """
    try:
        socials_collection = db.social
        
        # Create unique compound index on platform, handle, and lead_id
        await socials_collection.create_index([("platform", 1), ("handle", 1), ("lead_id", 1)], unique=True)
        
        return {
            "message": "Unique compound index created successfully on platform, handle, and lead_id",
            "index_name": "platform_1_handle_1_lead_id_1"
        }
        
    except Exception as e:
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            return {
                "message": "Unique compound index already exists on platform, handle, and lead_id",
                "index_name": "platform_1_handle_1_lead_id_1"
            }
        raise HTTPException(status_code=500, detail=f"Failed to create unique index: {str(e)}")
