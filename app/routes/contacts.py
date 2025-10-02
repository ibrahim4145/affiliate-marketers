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

# Pydantic models for combined contact data
class EmailContact(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    email: EmailStr = Field(..., description="Email address")
    page_source: str = Field(..., description="Page source where email was found (e.g., '/contact')")

class PhoneContact(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    phone: str = Field(..., description="Phone number in any format")
    page_source: str = Field(..., description="Page source where phone was found (e.g., '/contact')")

class SocialContact(BaseModel):
    lead_id: str = Field(..., description="Lead ID from leads table")
    platform: str = Field(..., description="Social media platform (instagram, facebook, x, linkedin, etc.)")
    handle: str = Field(..., description="Social media handle/username")
    page_source: str = Field(..., description="Page source where social handle was found (e.g., '/contact')")

class CombinedContactData(BaseModel):
    emails: List[EmailContact] = Field(default=[], description="List of emails to create")
    phones: List[PhoneContact] = Field(default=[], description="List of phones to create")
    socials: List[SocialContact] = Field(default=[], description="List of social handles to create")

class CombinedContactResponse(BaseModel):
    emails_created: int
    emails_ids: List[str]
    phones_created: int
    phones_ids: List[str]
    socials_created: int
    socials_ids: List[str]
    total_created: int
    message: str

@router.post("/contacts/add", response_model=CombinedContactResponse)
async def create_combined_contacts(
    contact_data: CombinedContactData,
    db=Depends(get_database)
):
    """
    Create emails, phones, and social handles in a single API call.
    Duplicates are automatically filtered out for each type.
    """
    try:
        emails_collection = db.email
        phones_collection = db.phone
        socials_collection = db.social
        
        # Initialize response counters
        emails_created = 0
        emails_ids = []
        phones_created = 0
        phones_ids = []
        socials_created = 0
        socials_ids = []
        
        # Process emails
        if contact_data.emails:
            emails_to_insert = []
            duplicate_emails = []
            existing_emails = set()
            
            for email in contact_data.emails:
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
            
            # Insert emails with error handling
            if emails_to_insert:
                try:
                    result = await emails_collection.insert_many(emails_to_insert)
                    emails_created = len(result.inserted_ids)
                    emails_ids = [str(id) for id in result.inserted_ids]
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for email_doc in emails_to_insert:
                            try:
                                result = await emails_collection.insert_one(email_doc)
                                emails_created += 1
                                emails_ids.append(str(result.inserted_id))
                            except Exception as single_error:
                                if "duplicate key error" in str(single_error).lower():
                                    duplicate_emails.append(f"{email_doc['email']} (lead: {email_doc['lead_id']})")
                                else:
                                    print(f"Error inserting email {email_doc.get('email', 'unknown')}: {str(single_error)}")
                    else:
                        print(f"Error inserting emails: {str(insert_error)}")
        
        # Process phones
        if contact_data.phones:
            phones_to_insert = []
            duplicate_phones = []
            existing_phones = set()
            
            for phone in contact_data.phones:
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
            
            # Insert phones with error handling
            if phones_to_insert:
                try:
                    result = await phones_collection.insert_many(phones_to_insert)
                    phones_created = len(result.inserted_ids)
                    phones_ids = [str(id) for id in result.inserted_ids]
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for phone_doc in phones_to_insert:
                            try:
                                result = await phones_collection.insert_one(phone_doc)
                                phones_created += 1
                                phones_ids.append(str(result.inserted_id))
                            except Exception as single_error:
                                if "duplicate key error" in str(single_error).lower():
                                    duplicate_phones.append(f"{phone_doc['phone']} (lead: {phone_doc['lead_id']})")
                                else:
                                    print(f"Error inserting phone {phone_doc.get('phone', 'unknown')}: {str(single_error)}")
                    else:
                        print(f"Error inserting phones: {str(insert_error)}")
        
        # Process socials
        if contact_data.socials:
            socials_to_insert = []
            duplicate_socials = []
            existing_socials = set()
            
            for social in contact_data.socials:
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
            
            # Insert socials with error handling
            if socials_to_insert:
                try:
                    result = await socials_collection.insert_many(socials_to_insert)
                    socials_created = len(result.inserted_ids)
                    socials_ids = [str(id) for id in result.inserted_ids]
                except Exception as insert_error:
                    if "duplicate key error" in str(insert_error).lower():
                        # Try inserting one by one
                        for social_doc in socials_to_insert:
                            try:
                                result = await socials_collection.insert_one(social_doc)
                                socials_created += 1
                                socials_ids.append(str(result.inserted_id))
                            except Exception as single_error:
                                if "duplicate key error" in str(single_error).lower():
                                    duplicate_socials.append(f"{social_doc['platform']}:{social_doc['handle']} (lead: {social_doc['lead_id']})")
                                else:
                                    print(f"Error inserting social {social_doc.get('platform', 'unknown')}:{social_doc.get('handle', 'unknown')}: {str(single_error)}")
                    else:
                        print(f"Error inserting socials: {str(insert_error)}")
        
        # Calculate totals
        total_created = emails_created + phones_created + socials_created
        
        # Prepare response message
        message_parts = []
        if emails_created > 0:
            message_parts.append(f"{emails_created} emails")
        if phones_created > 0:
            message_parts.append(f"{phones_created} phones")
        if socials_created > 0:
            message_parts.append(f"{socials_created} social handles")
        
        if message_parts:
            message = f"Successfully created {', '.join(message_parts)}"
        else:
            message = "No new contacts created (all were duplicates)"
        
        return CombinedContactResponse(
            emails_created=emails_created,
            emails_ids=emails_ids,
            phones_created=phones_created,
            phones_ids=phones_ids,
            socials_created=socials_created,
            socials_ids=socials_ids,
            total_created=total_created,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't break the scraper
        print(f"Unexpected error in create_combined_contacts: {str(e)}")
        # Return a successful response with 0 created to keep scraper running
        return CombinedContactResponse(
            emails_created=0,
            emails_ids=[],
            phones_created=0,
            phones_ids=[],
            socials_created=0,
            socials_ids=[],
            total_created=0,
            message=f"Error occurred but scraper continues: {str(e)[:100]}..."
        )

@router.get("/contacts/stats")
async def get_combined_contacts_stats(db=Depends(get_database)):
    """
    Get combined statistics for all contact types.
    """
    try:
        emails_collection = db.email
        phones_collection = db.phone
        socials_collection = db.social
        
        # Get counts for each type
        total_emails = await emails_collection.count_documents({})
        total_phones = await phones_collection.count_documents({})
        total_socials = await socials_collection.count_documents({})
        
        # Get unique lead counts
        unique_lead_emails = await emails_collection.distinct("lead_id")
        unique_lead_phones = await phones_collection.distinct("lead_id")
        unique_lead_socials = await socials_collection.distinct("lead_id")
        
        # Get all unique leads that have any contact
        all_lead_ids = set(unique_lead_emails + unique_lead_phones + unique_lead_socials)
        
        return {
            "total_contacts": total_emails + total_phones + total_socials,
            "emails": {
                "total": total_emails,
                "unique_leads": len(unique_lead_emails)
            },
            "phones": {
                "total": total_phones,
                "unique_leads": len(unique_lead_phones)
            },
            "socials": {
                "total": total_socials,
                "unique_leads": len(unique_lead_socials)
            },
            "leads_with_contacts": len(all_lead_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get combined contacts statistics: {str(e)}")
