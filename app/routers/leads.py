from fastapi import APIRouter, HTTPException, Depends
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, BulkLeadCreate, BulkLeadResponse
from app.schemas.contact import LeadContactsData, LeadContactsResponse
from app.crud.lead import (
    create_leads_bulk, get_leads, get_lead_by_id, update_lead, 
    delete_lead, get_leads_stats, add_lead_contacts
)
from app.dependencies import get_database
from app.utils.authentication import get_current_user
from typing import List, Optional, Dict, Any
from bson import ObjectId
import asyncio

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/", response_model=BulkLeadResponse)
async def create_leads(
    bulk_data: BulkLeadCreate,
    db=Depends(get_database)
):
    """Create multiple leads in bulk."""
    try:
        return await create_leads_bulk(bulk_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create leads: {str(e)}")

@router.get("/", response_model=List[LeadResponse])
async def get_leads_endpoint(
    skip: int = 0,
    limit: int = 50,
    scraper_progress_id: Optional[str] = None,
    scraped: Optional[bool] = None,
    google_done: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leads with filtering and pagination."""
    try:
        return await get_leads(skip, limit, scraper_progress_id, scraped, google_done, search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")

@router.get("/combined-data")
async def get_leads_combined(
    skip: int = 0,
    limit: int = 50,
    scraper_progress_id: Optional[str] = None,
    scraped: Optional[bool] = None,
    google_done: Optional[bool] = None,
    search: Optional[str] = None,
    db=Depends(get_database)
):
    """Get leads with all related data (industry, emails, phones, socials) in a single response."""
    try:
        from app.models.database import collections
        leads_collection = collections.leads
        industries_collection = collections.industries
        emails_collection = collections.email
        phones_collection = collections.phone
        socials_collection = collections.social
        
        # Build filter query for leads
        filter_query = {}
        if scraper_progress_id:
            filter_query["scraper_progress_id"] = scraper_progress_id
        if scraped is not None:
            filter_query["scraped"] = scraped
        if google_done is not None:
            filter_query["google_done"] = google_done
        
        # Add search functionality
        if search:
            # Build search query for leads - only search in domain and title
            filter_query["$or"] = [
                {"domain": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}}
            ]
        
        # Get leads with pagination
        cursor = leads_collection.find(filter_query).skip(skip).limit(limit)
        leads = await cursor.to_list(length=limit)
        
        # Post-process search results to ensure accuracy
        if search:
            # Get all industries for matching
            industries_cursor = industries_collection.find({})
            all_industries = await industries_cursor.to_list(length=None)
            industries_map = {str(industry["_id"]): industry for industry in all_industries}
            
            # Filter leads to only include those where search term actually appears
            filtered_leads = []
            for lead in leads:
                lead_matches = False
                search_lower = search.lower()
                
                # Check if search term appears in lead fields
                domain = lead.get("domain", "").lower()
                title = lead.get("title", "").lower()
                
                if (search_lower in domain or search_lower in title):
                    lead_matches = True
                
                # If not found in lead fields, check industry
                if not lead_matches:
                    scraper_progress_id = lead.get("scraper_progress_id")
                    if scraper_progress_id:
                        try:
                            progress_collection = collections.scraped_progress
                            progress_record = await progress_collection.find_one({"_id": ObjectId(scraper_progress_id)})
                            if progress_record:
                                industry_id = progress_record.get("industry_id") or progress_record.get("i_id")
                                if industry_id and str(industry_id) in industries_map:
                                    industry = industries_map[str(industry_id)]
                                    industry_name = industry.get("industry_name", "").lower()
                                    if search_lower in industry_name:
                                        lead_matches = True
                        except Exception as e:
                            pass
                
                if lead_matches:
                    filtered_leads.append(lead)
            
            leads = filtered_leads
        
        # Get all industries for mapping
        industries_cursor = industries_collection.find({})
        industries = await industries_cursor.to_list(length=None)
        industries_map = {str(industry["_id"]): industry for industry in industries}
        
        # Get all lead IDs for parallel queries
        lead_ids = [lead["_id"] for lead in leads]
        
        # Parallel queries for related data
        async def get_emails_for_leads():
            if not lead_ids:
                return []
            emails_cursor = emails_collection.find({"lead_id": {"$in": lead_ids}})
            return await emails_cursor.to_list(length=None)
        
        async def get_phones_for_leads():
            if not lead_ids:
                return []
            phones_cursor = phones_collection.find({"lead_id": {"$in": lead_ids}})
            return await phones_cursor.to_list(length=None)
        
        async def get_socials_for_leads():
            if not lead_ids:
                return []
            socials_cursor = socials_collection.find({"lead_id": {"$in": lead_ids}})
            return await socials_cursor.to_list(length=None)
        
        # Execute parallel queries
        emails, phones, socials = await asyncio.gather(
            get_emails_for_leads(),
            get_phones_for_leads(),
            get_socials_for_leads()
        )
        
        # Group related data by lead_id
        emails_by_lead = {}
        for email in emails:
            lead_id = str(email["lead_id"])
            if lead_id not in emails_by_lead:
                emails_by_lead[lead_id] = []
            emails_by_lead[lead_id].append({
                "email": email["email"],
                "page_source": email.get("page_source", "")
            })
        
        phones_by_lead = {}
        for phone in phones:
            lead_id = str(phone["lead_id"])
            if lead_id not in phones_by_lead:
                phones_by_lead[lead_id] = []
            phones_by_lead[lead_id].append({
                "phone": phone["phone"],
                "page_source": phone.get("page_source", "")
            })
        
        socials_by_lead = {}
        for social in socials:
            lead_id = str(social["lead_id"])
            if lead_id not in socials_by_lead:
                socials_by_lead[lead_id] = []
            socials_by_lead[lead_id].append({
                "platform": social["platform"],
                "handle": social["handle"],
                "page_source": social.get("page_source", "")
            })
        
        # Build response with combined data
        combined_leads = []
        for lead in leads:
            lead_id = str(lead["_id"])
            
            # Get industry info
            industry_info = None
            scraper_progress_id = lead.get("scraper_progress_id")
            if scraper_progress_id:
                try:
                    progress_collection = collections.scraped_progress
                    progress_record = await progress_collection.find_one({"_id": ObjectId(scraper_progress_id)})
                    if progress_record:
                        industry_id = progress_record.get("industry_id") or progress_record.get("i_id")
                        if industry_id and str(industry_id) in industries_map:
                            industry = industries_map[str(industry_id)]
                            industry_info = {
                                "id": str(industry["_id"]),
                                "name": industry["industry_name"],
                                "description": industry.get("description")
                            }
                except Exception:
                    pass
            
            combined_lead = {
                "id": lead_id,
                "domain": lead["domain"],
                "title": lead["title"],
                "description": lead.get("description", ""),
                "scraper_progress_id": lead.get("scraper_progress_id"),
                "scraped": lead.get("scraped", False),
                "google_done": lead.get("google_done", False),
                "created_at": lead.get("created_at"),
                "updated_at": lead.get("updated_at"),
                "industry": industry_info,
                "emails": emails_by_lead.get(lead_id, []),
                "phones": phones_by_lead.get(lead_id, []),
                "socials": socials_by_lead.get(lead_id, [])
            }
            combined_leads.append(combined_lead)
        
        # Calculate pagination info
        total_count = await leads_collection.count_documents(filter_query)
        has_next = (skip + limit) < total_count
        next_cursor = str(leads[-1]["_id"]) if leads and has_next else None
        
        return {
            "leads": combined_leads,
            "pagination": {
                "limit": limit,
                "has_next": has_next,
                "next_cursor": next_cursor,
                "count": len(combined_leads)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve combined leads data: {str(e)}")

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific lead by ID."""
    lead = await get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead_endpoint(
    lead_id: str,
    lead_update: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a lead."""
    try:
        updated_lead = await update_lead(lead_id, lead_update)
        if not updated_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return updated_lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")

@router.delete("/{lead_id}")
async def delete_lead_endpoint(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a lead."""
    success = await delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": "Lead deleted successfully"}

@router.get("/stats/summary")
async def get_leads_stats_endpoint(db=Depends(get_database)):
    """Get leads statistics."""
    try:
        return await get_leads_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads stats: {str(e)}")

@router.post("/{lead_id}/contacts", response_model=LeadContactsResponse)
async def add_lead_contacts_endpoint(
    lead_id: str,
    contacts_data: LeadContactsData,
    current_user: dict = Depends(get_current_user)
):
    """Add contacts to a lead."""
    try:
        return await add_lead_contacts(lead_id, contacts_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add contacts: {str(e)}")

@router.post("/ensure-indexes")
async def ensure_indexes(db=Depends(get_database)):
    """Ensure MongoDB indexes are created for optimal performance."""
    try:
        from app.models.indexes import create_indexes
        result = await create_indexes()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create indexes: {str(e)}")
