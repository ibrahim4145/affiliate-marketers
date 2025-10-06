from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.models.industry import industry_model
from app.schemas.industry import IndustryCreate, IndustryUpdate, IndustryOut

async def create_industry(industry: IndustryCreate) -> IndustryOut:
    """Create a new industry."""
    # Check if industry already exists
    existing = await industry_model.find_by_name(industry.industry_name)
    if existing:
        raise ValueError("Industry already exists")
    
    industry_data = {
        "industry_name": industry.industry_name,
        "description": industry.description
    }
    
    created_industry = await industry_model.create(industry_data)
    return industry_helper(created_industry)

async def get_industry_by_id(industry_id: str) -> Optional[IndustryOut]:
    """Get industry by ID."""
    try:
        industry = await industry_model.find_by_id(industry_id)
        if not industry:
            return None
        return industry_helper(industry)
    except Exception:
        return None

async def get_all_industries() -> List[IndustryOut]:
    """Get all industries."""
    industries = await industry_model.find_all()
    return [industry_helper(industry) for industry in industries]

async def update_industry(industry_id: str, industry_update: IndustryUpdate) -> Optional[IndustryOut]:
    """Update an industry."""
    try:
        # Check if industry exists
        existing_industry = await industry_model.find_by_id(industry_id)
        if not existing_industry:
            return None
        
        # Check if new name conflicts with existing industry
        if industry_update.industry_name:
            name_conflict = await industry_model.check_name_conflict(
                industry_update.industry_name, industry_id
            )
            if name_conflict:
                raise ValueError("Industry name already exists")
        
        # Prepare update data
        update_data = {}
        if industry_update.industry_name is not None:
            update_data["industry_name"] = industry_update.industry_name
        if industry_update.description is not None:
            update_data["description"] = industry_update.description
        
        # Update the industry
        updated_industry = await industry_model.update(industry_id, update_data)
        return industry_helper(updated_industry)
    except Exception:
        return None

async def delete_industry(industry_id: str) -> bool:
    """Delete an industry."""
    try:
        # Check if industry exists
        industry = await industry_model.find_by_id(industry_id)
        if not industry:
            return False
        
        # Delete the industry
        result = await industry_model.delete(industry_id)
        return True
    except Exception:
        return False

def industry_helper(industry) -> IndustryOut:
    """Convert MongoDB document to IndustryOut."""
    return IndustryOut(
        id=str(industry["_id"]),
        industry_name=industry["industry_name"],
        description=industry.get("description"),
        created_at=industry.get("created_at", datetime.utcnow()),
        updated_at=industry.get("updated_at", datetime.utcnow())
    )
