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
class PhoneBase(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    phone: str = Field(..., description="Phone number in any format")
    page_source: str = Field(..., description="Page source where phone was found (e.g., '/contact')")

class PhoneCreate(PhoneBase):
    pass

class PhoneUpdate(BaseModel):
    lead_id: Optional[str] = None
    phone: Optional[str] = None
    page_source: Optional[str] = None

class PhoneResponse(PhoneBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BulkPhoneCreate(BaseModel):
    phones: List[PhoneCreate] = Field(..., description="List of phones to create")

class BulkPhoneResponse(BaseModel):
    created_count: int
    created_ids: List[str]
    message: str

@router.post("/phone", response_model=BulkPhoneResponse)
async def create_phones(
    bulk_data: BulkPhoneCreate,
    db=Depends(get_database)
):
    """
    Create multiple phones in bulk. Duplicates are automatically filtered out.
    """
    try:
        phones_collection = db.phone
        
        # Prepare phones data with timestamps
        phones_to_insert = []
        duplicate_phones = []
        existing_phones = set()
        
        for phone in bulk_data.phones:
            # Create unique key for duplicate checking (phone + lead_id)
            unique_key = f"{phone.phone}_{phone.lead_id}"
            
            # Check if phone already exists in current batch
            if unique_key in existing_phones:
                duplicate_phones.append(f"{phone.phone} (lead: {phone.lead_id})")
                continue
            
            # Check if phone already exists in database
            existing_phone = await phones_collection.find_one({
                "phone": phone.phone,
                "lead_id": phone.lead_id
            })
            if existing_phone:
                duplicate_phones.append(f"{phone.phone} (lead: {phone.lead_id})")
                continue
            
            # Add to batch and mark as processed
            phone_doc = phone.dict()
            phone_doc["created_at"] = datetime.utcnow()
            phone_doc["updated_at"] = datetime.utcnow()
            phones_to_insert.append(phone_doc)
            existing_phones.add(unique_key)
        
        # Insert only unique phones with error handling
        created_count = 0
        created_ids = []
        
        if phones_to_insert:
            try:
                result = await phones_collection.insert_many(phones_to_insert)
                created_count = len(result.inserted_ids)
                created_ids = [str(id) for id in result.inserted_ids]
            except Exception as insert_error:
                # Handle batch insert errors gracefully
                if "duplicate key error" in str(insert_error).lower():
                    # Try inserting one by one to identify which ones are duplicates
                    for phone_doc in phones_to_insert:
                        try:
                            result = await phones_collection.insert_one(phone_doc)
                            created_count += 1
                            created_ids.append(str(result.inserted_id))
                        except Exception as single_error:
                            if "duplicate key error" in str(single_error).lower():
                                duplicate_phones.append(f"{phone_doc['phone']} (lead: {phone_doc['lead_id']})")
                            else:
                                # Log other errors but don't break the process
                                print(f"Error inserting phone {phone_doc.get('phone', 'unknown')}: {str(single_error)}")
                else:
                    # Re-raise non-duplicate errors
                    raise insert_error
        
        # Prepare response message
        message = f"Successfully created {created_count} phones"
        if duplicate_phones:
            message += f". Skipped {len(duplicate_phones)} duplicates: {', '.join(duplicate_phones[:3])}"
            if len(duplicate_phones) > 3:
                message += f" and {len(duplicate_phones) - 3} more"
        
        return BulkPhoneResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't break the scraper
        print(f"Unexpected error in create_phones: {str(e)}")
        # Return a successful response with 0 created to keep scraper running
        return BulkPhoneResponse(
            created_count=0,
            created_ids=[],
            message=f"Error occurred but scraper continues: {str(e)[:100]}..."
        )

@router.get("/phone", response_model=List[PhoneResponse])
async def get_phones(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[str] = None,
    page_source: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get phones with optional filtering.
    """
    try:
        phones_collection = db.phone
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = lead_id
        if page_source:
            filter_query["page_source"] = page_source
        
        # Get phones with pagination
        cursor = phones_collection.find(filter_query).skip(skip).limit(limit)
        phones = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for phone in phones:
            phone["_id"] = str(phone["_id"])
        
        return phones
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve phones: {str(e)}")

@router.get("/phone/{phone_id}", response_model=PhoneResponse)
async def get_phone(
    phone_id: str,
    db=Depends(get_database)
):
    """
    Get a specific phone by ID.
    """
    try:
        phones_collection = db.phone
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(phone_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid phone ID format")
        
        # Find the phone
        phone = await phones_collection.find_one({"_id": object_id})
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        # Convert ObjectId to string
        phone["_id"] = str(phone["_id"])
        
        return phone
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve phone: {str(e)}")

@router.put("/phone/{phone_id}", response_model=PhoneResponse)
async def update_phone(
    phone_id: str,
    phone_update: PhoneUpdate,
    db=Depends(get_database)
):
    """
    Update a specific phone.
    """
    try:
        phones_collection = db.phone
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(phone_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid phone ID format")
        
        # Check if phone exists
        existing_phone = await phones_collection.find_one({"_id": object_id})
        if not existing_phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        # Prepare update data (only include non-None fields)
        update_data = {k: v for k, v in phone_update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update the phone
            await phones_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
        
        # Get the updated phone
        updated_phone = await phones_collection.find_one({"_id": object_id})
        updated_phone["_id"] = str(updated_phone["_id"])
        
        return updated_phone
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update phone: {str(e)}")

@router.delete("/phone/{phone_id}")
async def delete_phone(
    phone_id: str,
    db=Depends(get_database)
):
    """
    Delete a specific phone.
    """
    try:
        phones_collection = db.phone
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(phone_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid phone ID format")
        
        # Check if phone exists
        existing_phone = await phones_collection.find_one({"_id": object_id})
        if not existing_phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        # Delete the phone
        result = await phones_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        return {"message": "Phone deleted successfully", "deleted_id": phone_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete phone: {str(e)}")

@router.get("/phone/stats/summary")
async def get_phones_stats(db=Depends(get_database)):
    """
    Get phones statistics.
    """
    try:
        phones_collection = db.phone
        
        # Get total count
        total_phones = await phones_collection.count_documents({})
        
        # Get phones by lead_id
        lead_stats = await phones_collection.aggregate([
            {"$group": {"_id": "$lead_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        # Get phones by page_source
        page_stats = await phones_collection.aggregate([
            {"$group": {"_id": "$page_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        return {
            "total_phones": total_phones,
            "lead_stats": lead_stats,
            "page_source_stats": page_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phones statistics: {str(e)}")

@router.post("/phone/ensure-unique-index")
async def ensure_unique_index(db=Depends(get_database)):
    """
    Create a unique index on phone and lead_id combination to prevent duplicates.
    """
    try:
        phones_collection = db.phone
        
        # Create unique compound index on phone and lead_id
        await phones_collection.create_index([("phone", 1), ("lead_id", 1)], unique=True)
        
        return {
            "message": "Unique compound index created successfully on phone and lead_id",
            "index_name": "phone_1_lead_id_1"
        }
        
    except Exception as e:
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            return {
                "message": "Unique compound index already exists on phone and lead_id",
                "index_name": "phone_1_lead_id_1"
            }
        raise HTTPException(status_code=500, detail=f"Failed to create unique index: {str(e)}")
