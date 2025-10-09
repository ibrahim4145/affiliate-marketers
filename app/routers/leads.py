from fastapi import APIRouter, HTTPException, Depends
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, BulkLeadCreate, BulkLeadResponse
from app.schemas.lead import LeadContactsData, LeadContactsResponse
from app.crud.lead import (
    create_leads_bulk, get_leads, get_lead_by_id, update_lead, 
    delete_lead, get_leads_stats, add_lead_contacts
)
from app.dependencies import get_database
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
    visible_only: Optional[bool] = None,
    db=Depends(get_database)
):
    """Get leads with all related data (niche, emails, phones, socials) in a single response.
    Use visible_only=true to get only visible leads, visible_only=false to get only hidden leads,
    or omit to get all leads regardless of visibility."""
    try:
        from app.models.lead import lead_model
        from app.models.niche import niche_model
        from app.models.email import email_model
        from app.models.phone import phone_model
        from app.models.social import social_model
        
        leads_collection = lead_model.collection
        niches_collection = niche_model.collection
        emails_collection = email_model.collection
        phones_collection = phone_model.collection
        socials_collection = social_model.collection
        
        # Build filter query for leads
        filter_query = {}
        if scraper_progress_id:
            filter_query["scraper_progress_id"] = scraper_progress_id
        if scraped is not None:
            filter_query["scraped"] = scraped
        if google_done is not None:
            filter_query["google_done"] = google_done
        
        # Add visibility filter
        if visible_only is not None:
            filter_query["visible"] = visible_only
        
        # Note: Search functionality is handled in post-processing to allow niche searching
        
        # Get leads with pagination, sorted by created_at ascending
        # If searching, get more leads initially to account for post-processing filtering
        fetch_limit = limit * 3 if search else limit
        cursor = leads_collection.find(filter_query).sort("created_at", 1).skip(skip).limit(fetch_limit)
        leads = await cursor.to_list(length=fetch_limit)
        
        # Post-process search results to ensure accuracy
        if search:
            # Get all niches for matching
            niches_cursor = niches_collection.find({})
            all_niches = await niches_cursor.to_list(length=None)
            niches_map = {str(niche["_id"]): niche for niche in all_niches}
            
            # Filter leads to only include those where search term actually appears
            filtered_leads = []
            for lead in leads:
                lead_matches = False
                search_lower = search.lower()
                
                # Check if search term appears in lead fields
                domain = lead.get("domain", "").lower()
                
                if visible_only is True:
                    # For visible leads (leads page), only check domain (no title column)
                    if search_lower in domain:
                        lead_matches = True
                else:
                    # For all leads (middleman page), check domain and title
                    title = lead.get("title", "").lower()
                    if (search_lower in domain or search_lower in title):
                        lead_matches = True
                
                # Always check niche regardless of lead field matches
                if not lead_matches:
                    scraper_progress_id = lead.get("scraper_progress_id")
                    if scraper_progress_id:
                        try:
                            from app.models.scraper import scraper_progress_model
                            progress_collection = scraper_progress_model.collection
                            progress_record = await progress_collection.find_one({"_id": ObjectId(scraper_progress_id)})
                            if progress_record:
                                niche_id = progress_record.get("niche_id") or progress_record.get("i_id")
                                if niche_id and str(niche_id) in niches_map:
                                    niche = niches_map[str(niche_id)]
                                    niche_name = niche.get("niche_name", "").lower()
                                    if search_lower in niche_name:
                                        lead_matches = True
                        except Exception as e:
                            pass
                
                if lead_matches:
                    filtered_leads.append(lead)
            
            leads = filtered_leads[:limit]  # Limit to requested number of results
        
        # Get all niches for mapping
        niches_cursor = niches_collection.find({})
        niches = await niches_cursor.to_list(length=None)
        niches_map = {str(niche["_id"]): niche for niche in niches}
        
        # Get all lead IDs for parallel queries
        lead_ids = [lead["_id"] for lead in leads]
        
        # Parallel queries for related data
        async def get_emails_for_leads():
            if not lead_ids:
                return []
            # Convert lead_ids to ObjectId since contact collections store lead_id as ObjectId
            lead_id_objects = [ObjectId(lead_id) for lead_id in lead_ids]
            emails_cursor = emails_collection.find({"lead_id": {"$in": lead_id_objects}})
            return await emails_cursor.to_list(length=None)
        
        async def get_phones_for_leads():
            if not lead_ids:
                return []
            # Convert lead_ids to ObjectId since contact collections store lead_id as ObjectId
            lead_id_objects = [ObjectId(lead_id) for lead_id in lead_ids]
            phones_cursor = phones_collection.find({"lead_id": {"$in": lead_id_objects}})
            return await phones_cursor.to_list(length=None)
        
        async def get_socials_for_leads():
            if not lead_ids:
                return []
            # Convert lead_ids to ObjectId since contact collections store lead_id as ObjectId
            lead_id_objects = [ObjectId(lead_id) for lead_id in lead_ids]
            socials_cursor = socials_collection.find({"lead_id": {"$in": lead_id_objects}})
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
            lead_id = str(email["lead_id"])  # Convert ObjectId to string for grouping
            if lead_id not in emails_by_lead:
                emails_by_lead[lead_id] = []
            emails_by_lead[lead_id].append({
                "id": str(email["_id"]),
                "email": email["email"],
                "page_source": email.get("page_source", ""),
                "created_at": email.get("created_at"),
                "updated_at": email.get("updated_at")
            })
        
        phones_by_lead = {}
        for phone in phones:
            lead_id = str(phone["lead_id"])  # Convert ObjectId to string for grouping
            if lead_id not in phones_by_lead:
                phones_by_lead[lead_id] = []
            phones_by_lead[lead_id].append({
                "id": str(phone["_id"]),
                "phone": phone["phone"],
                "page_source": phone.get("page_source", ""),
                "created_at": phone.get("created_at"),
                "updated_at": phone.get("updated_at")
            })
        
        socials_by_lead = {}
        for social in socials:
            lead_id = str(social["lead_id"])  # Convert ObjectId to string for grouping
            if lead_id not in socials_by_lead:
                socials_by_lead[lead_id] = []
            socials_by_lead[lead_id].append({
                "id": str(social["_id"]),
                "platform": social["platform"],
                "handle": social["handle"],
                "page_source": social.get("page_source", ""),
                "created_at": social.get("created_at"),
                "updated_at": social.get("updated_at")
            })
        
        # Build response with combined data
        combined_leads = []
        for lead in leads:
            lead_id = str(lead["_id"])
            
            # Get niche info - default to Unknown
            niche_info = {
                "id": "unknown",
                "name": "Unknown",
                "description": "Niche information not available"
            }
            
            # First try direct niche_id on lead
            niche_id = lead.get("niche_id")
            if niche_id and str(niche_id) in niches_map:
                niche = niches_map[str(niche_id)]
                niche_info = {
                    "id": str(niche["_id"]),
                    "name": niche["niche_name"],
                    "description": niche.get("description")
                }
            else:
                # Try scraper_progress_id lookup - check multiple possible field names
                scraper_progress_id = lead.get("scraper_progress_id") or lead.get("scraper_progress") or lead.get("progress_id")
                if scraper_progress_id:
                    try:
                        from app.models.scraper import scraper_progress_model
                        progress_collection = scraper_progress_model.collection
                        progress_record = await progress_collection.find_one({"_id": ObjectId(scraper_progress_id)})
                        if progress_record:
                            niche_id = progress_record.get("niche_id") or progress_record.get("i_id")
                            if niche_id and str(niche_id) in niches_map:
                                niche = niches_map[str(niche_id)]
                                niche_info = {
                                    "id": str(niche["_id"]),
                                    "name": niche["niche_name"],
                                    "description": niche.get("description")
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
                "visible": lead.get("visible", False),
                "created_at": lead.get("created_at"),
                "updated_at": lead.get("updated_at"),
                "niche": niche_info,
                "emails": emails_by_lead.get(lead_id, []),
                "phones": phones_by_lead.get(lead_id, []),
                "socials": socials_by_lead.get(lead_id, [])
            }
            combined_leads.append(combined_lead)
        
        # Calculate pagination info
        total_count = await leads_collection.count_documents(filter_query)
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        current_page = (skip // limit) + 1
        has_next = (skip + limit) < total_count
        has_prev = skip > 0
        
        return {
            "leads": combined_leads,
            "pagination": {
                "page": current_page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "count": len(combined_leads)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve combined leads data: {str(e)}")

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
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
):
    """Delete a lead."""
    success = await delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": "Lead deleted successfully"}

@router.get("/stats/summary")
async def get_leads_stats_endpoint(visible_only: Optional[bool] = None, db=Depends(get_database)):
    """Get leads statistics."""
    try:
        return await get_leads_stats(visible_only=visible_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads stats: {str(e)}")

@router.post("/{lead_id}/contacts", response_model=LeadContactsResponse)
async def add_lead_contacts_endpoint(
    lead_id: str,
    contacts_data: LeadContactsData,
):
    """Add contacts to a lead."""
    try:
        return await add_lead_contacts(lead_id, contacts_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add contacts: {str(e)}")

# @router.post("/ensure-indexes")
# async def ensure_indexes(db=Depends(get_database)):
#     """Ensure MongoDB indexes are created for optimal performance."""
#     try:
#         from app.models.indexes import create_indexes
#         result = await create_indexes()
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create indexes: {str(e)}")



