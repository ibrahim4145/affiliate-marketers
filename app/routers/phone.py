from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_database
from app.utils.authentication import get_current_user
from app.schemas.phone import PhoneCreate, PhoneUpdate, PhoneResponse, BulkPhoneCreate, BulkPhoneResponse
from app.models.phone import phone_model
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/phone", tags=["Phone"])

@router.post("/", response_model=BulkPhoneResponse)
async def create_phones(
    bulk_data: BulkPhoneCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create multiple phones in bulk."""
    try:
        phones_collection = phone_model.collection
        
        # Prepare phones data with timestamps
        phones_to_insert = []
        for phone in bulk_data.phones:
            phone_doc = phone.dict()
            phone_doc["created_at"] = datetime.utcnow()
            phone_doc["updated_at"] = datetime.utcnow()
            phones_to_insert.append(phone_doc)
        
        # Insert phones
        result = await phones_collection.insert_many(phones_to_insert)
        created_count = len(result.inserted_ids)
        created_ids = [str(id) for id in result.inserted_ids]
        
        return BulkPhoneResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=f"Successfully created {created_count} phones"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create phones: {str(e)}")

@router.get("/", response_model=List[PhoneResponse])
async def get_phones(
    skip: int = 0,
    limit: int = 50,
    lead_id: Optional[str] = None,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get phones with filtering and pagination."""
    try:
        phones_collection = phone_model.collection
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = ObjectId(lead_id)
        
        # Get phones with pagination
        cursor = phones_collection.find(filter_query).skip(skip).limit(limit)
        phones = await cursor.to_list(length=limit)
        
        return [phone_helper(phone) for phone in phones]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve phones: {str(e)}")

@router.get("/{phone_id}", response_model=PhoneResponse)
async def get_phone(
    phone_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific phone by ID."""
    try:
        phone = await phone_model.find_by_id(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return phone_helper(phone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid phone ID")

@router.put("/{phone_id}", response_model=PhoneResponse)
async def update_phone(
    phone_id: str,
    phone_update: PhoneUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Update a phone."""
    try:
        # Check if phone exists
        existing_phone = await db.phone.find_one({"_id": ObjectId(phone_id)})
        if not existing_phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if phone_update.lead_id is not None:
            update_data["lead_id"] = ObjectId(phone_update.lead_id)
        if phone_update.phone is not None:
            update_data["phone"] = phone_update.phone
        if phone_update.page_source is not None:
            update_data["page_source"] = phone_update.page_source
        
        # Update the phone
        updated_phone = await phone_model.update(phone_id, update_data)
        return phone_helper(updated_phone)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid phone ID")

@router.delete("/{phone_id}")
async def delete_phone(
    phone_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Delete a phone."""
    try:
        # Check if phone exists
        phone = await phone_model.find_by_id(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        # Delete the phone
        await phone_model.delete(phone_id)
        
        return {"message": "Phone deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid phone ID")

def phone_helper(phone) -> PhoneResponse:
    """Convert MongoDB document to PhoneResponse."""
    return PhoneResponse(
        id=str(phone["_id"]),
        lead_id=str(phone["lead_id"]),
        phone=phone["phone"],
        page_source=phone["page_source"],
        created_at=phone.get("created_at", datetime.utcnow()),
        updated_at=phone.get("updated_at", datetime.utcnow())
    )
