from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.models import IndustryCreate, IndustryUpdate, IndustryOut
from app.auth import get_current_user
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/industries", tags=["Industries"])

# Helper: Convert MongoDB document to dict
def industry_helper(industry) -> dict:
    return {
        "id": str(industry["_id"]),
        "industry_name": industry["industry_name"],
        "description": industry.get("description"),
        "created_at": industry.get("created_at", datetime.utcnow()),
        "updated_at": industry.get("updated_at", datetime.utcnow())
    }

@router.post("/", response_model=IndustryOut)
async def create_industry(
    industry: IndustryCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create a new industry."""
    # Check if industry already exists
    existing = await db["industries"].find_one({"industry_name": industry.industry_name})
    if existing:
        raise HTTPException(status_code=400, detail="Industry already exists")
    
    industry_data = {
        "industry_name": industry.industry_name,
        "description": industry.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db["industries"].insert_one(industry_data)
    created_industry = await db["industries"].find_one({"_id": result.inserted_id})
    return industry_helper(created_industry)

@router.get("/", response_model=List[IndustryOut])
async def get_industries(current_user: dict = Depends(get_current_user)):
    """Get all industries."""
    industries = await db["industries"].find({}).sort("created_at", -1).to_list(length=None)
    return [industry_helper(industry) for industry in industries]

@router.get("/{industry_id}", response_model=IndustryOut)
async def get_industry(
    industry_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Get a specific industry by ID."""
    try:
        industry = await db["industries"].find_one({"_id": ObjectId(industry_id)})
        if not industry:
            raise HTTPException(status_code=404, detail="Industry not found")
        return industry_helper(industry)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid industry ID")

@router.put("/{industry_id}", response_model=IndustryOut)
async def update_industry(
    industry_id: str,
    industry_update: IndustryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an industry."""
    try:
        # Check if industry exists
        existing_industry = await db["industries"].find_one({"_id": ObjectId(industry_id)})
        if not existing_industry:
            raise HTTPException(status_code=404, detail="Industry not found")
        
        # Check if new name conflicts with existing industry
        if industry_update.industry_name:
            name_conflict = await db["industries"].find_one({
                "industry_name": industry_update.industry_name,
                "_id": {"$ne": ObjectId(industry_id)}
            })
            if name_conflict:
                raise HTTPException(status_code=400, detail="Industry name already exists")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if industry_update.industry_name is not None:
            update_data["industry_name"] = industry_update.industry_name
        if industry_update.description is not None:
            update_data["description"] = industry_update.description
        
        # Update the industry
        await db["industries"].update_one(
            {"_id": ObjectId(industry_id)},
            {"$set": update_data}
        )
        
        # Return updated industry
        updated_industry = await db["industries"].find_one({"_id": ObjectId(industry_id)})
        return industry_helper(updated_industry)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid industry ID")

@router.delete("/{industry_id}")
async def delete_industry(
    industry_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an industry."""
    try:
        # Check if industry exists
        industry = await db["industries"].find_one({"_id": ObjectId(industry_id)})
        if not industry:
            raise HTTPException(status_code=404, detail="Industry not found")
        
        # Delete the industry
        await db["industries"].delete_one({"_id": ObjectId(industry_id)})
        
        return {"message": "Industry deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid industry ID")
