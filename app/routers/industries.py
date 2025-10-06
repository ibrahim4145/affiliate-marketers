from fastapi import APIRouter, HTTPException, Depends
from app.schemas.industry import IndustryCreate, IndustryUpdate, IndustryOut
from app.crud.industry import create_industry, get_industry_by_id, get_all_industries, update_industry, delete_industry
from typing import List

router = APIRouter(prefix="/industries", tags=["Industries"])

@router.post("/", response_model=IndustryOut)
async def create_industry_endpoint(
    industry: IndustryCreate, 
):
    """Create a new industry."""
    try:
        return await create_industry(industry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create industry: {str(e)}")

@router.get("/", response_model=List[IndustryOut])
async def get_industries():
    """Get all industries."""
    return await get_all_industries()

@router.get("/{industry_id}", response_model=IndustryOut)
async def get_industry(
    industry_id: str, 
):
    """Get a specific industry by ID."""
    industry = await get_industry_by_id(industry_id)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry

@router.put("/{industry_id}", response_model=IndustryOut)
async def update_industry_endpoint(
    industry_id: str,
    industry_update: IndustryUpdate,
):
    """Update an industry."""
    try:
        updated_industry = await update_industry(industry_id, industry_update)
        if not updated_industry:
            raise HTTPException(status_code=404, detail="Industry not found")
        return updated_industry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update industry: {str(e)}")

@router.delete("/{industry_id}")
async def delete_industry_endpoint(
    industry_id: str,
):
    """Delete an industry."""
    success = await delete_industry(industry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Industry not found")
    
    return {"message": "Industry deleted successfully"}
