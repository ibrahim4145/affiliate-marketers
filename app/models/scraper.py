# Scraper database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class ScraperProgressModel:
    """Scraper progress database model."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["scraped_progress"]
    
    async def create_indexes(self):
        """Create scraper progress-specific indexes."""
        await self.collection.create_index("industry_id")
        await self.collection.create_index("query_id")
        await self.collection.create_index("done")
    
    async def find_by_id(self, progress_id: str):
        """Find progress by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(progress_id)})
        except Exception:
            return None
    
    async def find_incomplete(self):
        """Find next incomplete progress record."""
        return await self.collection.find_one({"done": False})
    
    async def find_all(self):
        """Find all progress records."""
        return await self.collection.find({}).sort("created_at", -1).to_list(length=None)
    
    async def create(self, progress_data: dict):
        """Create a new progress record."""
        progress_data["created_at"] = datetime.utcnow()
        progress_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(progress_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, progress_id: str, update_data: dict):
        """Update progress record."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(progress_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(progress_id)})
    
    async def delete(self, progress_id: str):
        """Delete progress record."""
        return await self.collection.delete_one({"_id": ObjectId(progress_id)})

# Global scraper model instance
scraper_progress_model = ScraperProgressModel()
