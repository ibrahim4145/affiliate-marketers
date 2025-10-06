from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from app.models.lead import lead_model
from app.models.email import email_model
from app.models.phone import phone_model
from app.models.social import social_model
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, BulkLeadCreate, BulkLeadResponse
from app.schemas.lead import LeadContactsData, LeadContactsResponse

async def create_leads_bulk(bulk_data: BulkLeadCreate) -> BulkLeadResponse:
    """Create multiple leads in bulk."""
    leads_collection = lead_model.collection
    
    # Prepare leads data with timestamps
    leads_to_insert = []
    duplicate_domains = []
    existing_domains = set()
    
    for lead in bulk_data.leads:
        # Check if domain already exists in current batch
        if lead.domain in existing_domains:
            duplicate_domains.append(lead.domain)
            continue
        
        # Check if domain already exists in database
        existing_lead = await lead_model.find_by_domain(lead.domain)
        if existing_lead:
            duplicate_domains.append(lead.domain)
            continue
        
        # Add to batch and mark as processed
        lead_doc = lead.dict()
        leads_to_insert.append(lead_doc)
        existing_domains.add(lead.domain)
    
    # Insert only unique leads
    created_count = 0
    created_ids = []
    
    if leads_to_insert:
        try:
            result = await lead_model.create_many(leads_to_insert)
            created_count = len(result)
            created_ids = [str(id) for id in result]
        except Exception as insert_error:
            # Handle batch insert errors gracefully
            print(f"Batch insert error: {insert_error}")
            # Try individual inserts
            for lead_doc in leads_to_insert:
                try:
                    result = await lead_model.create(lead_doc)
                    created_count += 1
                    created_ids.append(str(result["_id"]))
                except Exception:
                    continue
    
    return BulkLeadResponse(
        created_count=created_count,
        created_ids=created_ids,
        message=f"Successfully created {created_count} leads. {len(duplicate_domains)} duplicates skipped."
    )

async def get_leads(
    skip: int = 0,
    limit: int = 50,
    scraper_progress_id: Optional[str] = None,
    scraped: Optional[bool] = None,
    google_done: Optional[bool] = None,
    search: Optional[str] = None
) -> List[LeadResponse]:
    """Get leads with filtering and pagination."""
    # Build filters
    filters = {}
    if scraper_progress_id:
        filters["scraper_progress_id"] = scraper_progress_id
    if scraped is not None:
        filters["scraped"] = scraped
    if google_done is not None:
        filters["google_done"] = google_done
    if search:
        filters["search"] = search
    
    # Get leads with pagination
    leads = await lead_model.find_with_filters(skip, limit, **filters)
    
    return [lead_helper(lead) for lead in leads]

async def get_lead_by_id(lead_id: str) -> Optional[LeadResponse]:
    """Get a specific lead by ID."""
    try:
        lead = await lead_model.find_by_id(lead_id)
        if not lead:
            return None
        return lead_helper(lead)
    except Exception:
        return None

async def update_lead(lead_id: str, lead_update: LeadUpdate) -> Optional[LeadResponse]:
    """Update a lead."""
    try:
        # Check if lead exists
        existing_lead = await lead_model.find_by_id(lead_id)
        if not existing_lead:
            return None
        
        # Prepare update data
        update_data = {}
        if lead_update.domain is not None:
            update_data["domain"] = lead_update.domain
        if lead_update.title is not None:
            update_data["title"] = lead_update.title
        if lead_update.description is not None:
            update_data["description"] = lead_update.description
        if lead_update.scraper_progress_id is not None:
            update_data["scraper_progress_id"] = lead_update.scraper_progress_id
        if lead_update.scraped is not None:
            update_data["scraped"] = lead_update.scraped
        if lead_update.google_done is not None:
            update_data["google_done"] = lead_update.google_done
        
        # Update the lead
        updated_lead = await lead_model.update(lead_id, update_data)
        return lead_helper(updated_lead)
    except Exception:
        return None

async def delete_lead(lead_id: str) -> bool:
    """Delete a lead."""
    try:
        # Check if lead exists
        lead = await lead_model.find_by_id(lead_id)
        if not lead:
            return False
        
        # Delete the lead
        result = await lead_model.delete(lead_id)
        return True
    except Exception:
        return False

async def get_leads_stats() -> Dict[str, Any]:
    """Get leads statistics."""
    return await lead_model.get_stats()

async def add_lead_contacts(lead_id: str, contacts_data: LeadContactsData) -> LeadContactsResponse:
    """Add contacts to a lead."""
    try:
        # Check if lead exists
        lead = await lead_model.find_by_id(lead_id)
        if not lead:
            return LeadContactsResponse(
                lead_updated=False,
                emails_created=0,
                phones_created=0,
                socials_created=0,
                total_contacts_created=0,
                message="Lead not found"
            )
        
        # Update lead to mark as scraped
        await lead_model.update(lead_id, {"scraped": True})
        
        # Insert emails
        emails_created = 0
        if contacts_data.emails:
            email_docs = []
            for email in contacts_data.emails:
                email_doc = {
                    "lead_id": ObjectId(lead_id),
                    "email": email.email,
                    "page_source": email.page_source
                }
                email_docs.append(email_doc)
            
            if email_docs:
                result = await email_model.create_many(email_docs)
                emails_created = len(result)
        
        # Insert phones
        phones_created = 0
        if contacts_data.phones:
            phone_docs = []
            for phone in contacts_data.phones:
                phone_doc = {
                    "lead_id": ObjectId(lead_id),
                    "phone": phone.phone,
                    "page_source": phone.page_source
                }
                phone_docs.append(phone_doc)
            
            if phone_docs:
                result = await phone_model.create_many(phone_docs)
                phones_created = len(result)
        
        # Insert socials
        socials_created = 0
        if contacts_data.socials:
            social_docs = []
            for social in contacts_data.socials:
                social_doc = {
                    "lead_id": ObjectId(lead_id),
                    "platform": social.platform,
                    "handle": social.handle,
                    "page_source": social.page_source
                }
                social_docs.append(social_doc)
            
            if social_docs:
                result = await social_model.create_many(social_docs)
                socials_created = len(result)
        
        total_contacts_created = emails_created + phones_created + socials_created
        
        return LeadContactsResponse(
            lead_updated=True,
            emails_created=emails_created,
            phones_created=phones_created,
            socials_created=socials_created,
            total_contacts_created=total_contacts_created,
            message=f"Successfully added {total_contacts_created} contacts to lead"
        )
    except Exception as e:
        return LeadContactsResponse(
            lead_updated=False,
            emails_created=0,
            phones_created=0,
            socials_created=0,
            total_contacts_created=0,
            message=f"Error adding contacts: {str(e)}"
        )

def lead_helper(lead) -> LeadResponse:
    """Convert MongoDB document to LeadResponse."""
    return LeadResponse(
        id=str(lead["_id"]),
        domain=lead["domain"],
        title=lead["title"],
        description=lead["description"],
        scraper_progress_id=lead["scraper_progress_id"],
        scraped=lead.get("scraped", False),
        google_done=lead.get("google_done", False),
        created_at=lead.get("created_at", datetime.utcnow()),
        updated_at=lead.get("updated_at", datetime.utcnow())
    )
