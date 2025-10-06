from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_database
from app.utils.authentication import get_current_user
from app.schemas.social import SocialCreate, SocialUpdate, SocialResponse, BulkSocialCreate, BulkSocialResponse
from app.models.social import social_model
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/social", tags=["Social"])

@router.post("/", response_model=BulkSocialResponse)
async def create_socials(
    bulk_data: BulkSocialCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create multiple social handles in bulk."""
    try:
        socials_collection = social_model.collection
        
        # Prepare socials data with timestamps
        socials_to_insert = []
        for social in bulk_data.socials:
            social_doc = social.dict()
            social_doc["created_at"] = datetime.utcnow()
            social_doc["updated_at"] = datetime.utcnow()
            socials_to_insert.append(social_doc)
        
        # Insert socials
        result = await socials_collection.insert_many(socials_to_insert)
        created_count = len(result.inserted_ids)
        created_ids = [str(id) for id in result.inserted_ids]
        
        return BulkSocialResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=f"Successfully created {created_count} social handles"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create social handles: {str(e)}")

@router.get("/", response_model=List[SocialResponse])
async def get_socials(
    skip: int = 0,
    limit: int = 50,
    lead_id: Optional[str] = None,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get social handles with filtering and pagination."""
    try:
        socials_collection = social_model.collection
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = ObjectId(lead_id)
        
        # Get socials with pagination
        cursor = socials_collection.find(filter_query).skip(skip).limit(limit)
        socials = await cursor.to_list(length=limit)
        
        return [social_helper(social) for social in socials]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve social handles: {str(e)}")

@router.get("/{social_id}", response_model=SocialResponse)
async def get_social(
    social_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific social handle by ID."""
    try:
        social = await social_model.find_by_id(social_id)
        if not social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        return social_helper(social)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid social handle ID")

@router.put("/{social_id}", response_model=SocialResponse)
async def update_social(
    social_id: str,
    social_update: SocialUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Update a social handle."""
    try:
        # Check if social exists
        existing_social = await db.social.find_one({"_id": ObjectId(social_id)})
        if not existing_social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if social_update.lead_id is not None:
            update_data["lead_id"] = ObjectId(social_update.lead_id)
        if social_update.platform is not None:
            update_data["platform"] = social_update.platform
        if social_update.handle is not None:
            update_data["handle"] = social_update.handle
        if social_update.page_source is not None:
            update_data["page_source"] = social_update.page_source
        
        # Update the social
        updated_social = await social_model.update(social_id, update_data)
        return social_helper(updated_social)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid social handle ID")

@router.delete("/{social_id}")
async def delete_social(
    social_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Delete a social handle."""
    try:
        # Check if social exists
        social = await social_model.find_by_id(social_id)
        if not social:
            raise HTTPException(status_code=404, detail="Social handle not found")
        
        # Delete the social
        await social_model.delete(social_id)
        
        return {"message": "Social handle deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid social handle ID")

def social_helper(social) -> SocialResponse:
    """Convert MongoDB document to SocialResponse."""
    return SocialResponse(
        id=str(social["_id"]),
        lead_id=str(social["lead_id"]),
        platform=social["platform"],
        handle=social["handle"],
        page_source=social["page_source"],
        created_at=social.get("created_at", datetime.utcnow()),
        updated_at=social.get("updated_at", datetime.utcnow())
    )
