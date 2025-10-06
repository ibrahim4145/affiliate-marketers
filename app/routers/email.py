from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_database
from app.utils.authentication import get_current_user
from app.schemas.email import EmailCreate, EmailUpdate, EmailResponse, BulkEmailCreate, BulkEmailResponse
from app.models.email import email_model
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/email", tags=["Email"])

@router.post("/", response_model=BulkEmailResponse)
async def create_emails(
    bulk_data: BulkEmailCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create multiple emails in bulk."""
    try:
        emails_collection = email_model.collection
        
        # Prepare emails data with timestamps
        emails_to_insert = []
        for email in bulk_data.emails:
            email_doc = email.dict()
            email_doc["created_at"] = datetime.utcnow()
            email_doc["updated_at"] = datetime.utcnow()
            emails_to_insert.append(email_doc)
        
        # Insert emails
        result = await emails_collection.insert_many(emails_to_insert)
        created_count = len(result.inserted_ids)
        created_ids = [str(id) for id in result.inserted_ids]
        
        return BulkEmailResponse(
            created_count=created_count,
            created_ids=created_ids,
            message=f"Successfully created {created_count} emails"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create emails: {str(e)}")

@router.get("/", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 50,
    lead_id: Optional[str] = None,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get emails with filtering and pagination."""
    try:
        emails_collection = email_model.collection
        
        # Build filter query
        filter_query = {}
        if lead_id:
            filter_query["lead_id"] = ObjectId(lead_id)
        
        # Get emails with pagination
        cursor = emails_collection.find(filter_query).skip(skip).limit(limit)
        emails = await cursor.to_list(length=limit)
        
        return [email_helper(email) for email in emails]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emails: {str(e)}")

@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific email by ID."""
    try:
        email = await email_model.find_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        return email_helper(email)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid email ID")

@router.put("/{email_id}", response_model=EmailResponse)
async def update_email(
    email_id: str,
    email_update: EmailUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Update an email."""
    try:
        # Check if email exists
        existing_email = await email_model.find_by_id(email_id)
        if not existing_email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if email_update.lead_id is not None:
            update_data["lead_id"] = ObjectId(email_update.lead_id)
        if email_update.email is not None:
            update_data["email"] = email_update.email
        if email_update.page_source is not None:
            update_data["page_source"] = email_update.page_source
        
        # Update the email
        updated_email = await email_model.update(email_id, update_data)
        return email_helper(updated_email)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid email ID")

@router.delete("/{email_id}")
async def delete_email(
    email_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Delete an email."""
    try:
        # Check if email exists
        email = await email_model.find_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Delete the email
        await email_model.delete(email_id)
        
        return {"message": "Email deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid email ID")

def email_helper(email) -> EmailResponse:
    """Convert MongoDB document to EmailResponse."""
    return EmailResponse(
        id=str(email["_id"]),
        lead_id=str(email["lead_id"]),
        email=email["email"],
        page_source=email["page_source"],
        created_at=email.get("created_at", datetime.utcnow()),
        updated_at=email.get("updated_at", datetime.utcnow())
    )
