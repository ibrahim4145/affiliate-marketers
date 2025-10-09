# Lead database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime

class LeadModel:
    """Lead database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["leads"]
    
    async def create_indexes(self):
        """Create lead-specific indexes."""
        await self.collection.create_index("domain", unique=True)
        await self.collection.create_index("title")
        await self.collection.create_index([("title", "text"), ("description", "text")])
        await self.collection.create_index("niche_id")
        await self.collection.create_index("scraped")
        await self.collection.create_index("google_done")
        await self.collection.create_index("scraper_progress_id")
        await self.collection.create_index("visible")
    
    async def find_by_id(self, lead_id: str):
        """Find lead by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(lead_id)})
        except Exception:
            return None
    
    async def find_by_domain(self, domain: str):
        """Find lead by domain."""
        return await self.collection.find_one({"domain": domain})
    
    async def find_with_filters(self, skip: int = 0, limit: int = 50, **filters):
        """Find leads with filters and pagination."""
        filter_query = {}
        for key, value in filters.items():
            if value is not None:
                if key == "search":
                    filter_query["$or"] = [
                        {"domain": {"$regex": value, "$options": "i"}},
                        {"title": {"$regex": value, "$options": "i"}}
                    ]
                else:
                    filter_query[key] = value
        
        cursor = self.collection.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_with_filters(self, **filters):
        """Count leads with filters."""
        filter_query = {}
        for key, value in filters.items():
            if value is not None:
                if key == "search":
                    filter_query["$or"] = [
                        {"domain": {"$regex": value, "$options": "i"}},
                        {"title": {"$regex": value, "$options": "i"}}
                    ]
                else:
                    filter_query[key] = value
        
        return await self.collection.count_documents(filter_query)
    
    async def create(self, lead_data: dict):
        """Create a new lead."""
        lead_data["created_at"] = datetime.utcnow()
        lead_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(lead_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def create_many(self, leads_data: List[dict]):
        """Create multiple leads."""
        for lead_data in leads_data:
            lead_data["created_at"] = datetime.utcnow()
            lead_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_many(leads_data)
        return result.inserted_ids
    
    async def update(self, lead_id: str, update_data: dict):
        """Update lead."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(lead_id)})
    
    async def delete(self, lead_id: str):
        """Delete lead."""
        return await self.collection.delete_one({"_id": ObjectId(lead_id)})
    
    async def get_stats(self, visible_only: Optional[bool] = None):
        """Get lead statistics."""
        # Build filter query based on visibility
        filter_query = {}
        if visible_only is not None:
            filter_query["visible"] = visible_only
        
        total_leads = await self.collection.count_documents(filter_query)
        scraped_count = await self.collection.count_documents({**filter_query, "scraped": True})
        google_done_count = await self.collection.count_documents({**filter_query, "google_done": True})
        # New leads are those that are not scraped (scraped: False or scraped: null)
        new_count = await self.collection.count_documents({
            **filter_query,
            "$or": [
                {"scraped": False},
                {"scraped": {"$exists": False}},
                {"scraped": None}
            ]
        })
        
        return {
            "total_leads": total_leads,
            "scraped_leads": scraped_count,
            "google_done_leads": google_done_count,
            "unscraped_leads": new_count
        }

# Global lead model instance
lead_model = LeadModel()
