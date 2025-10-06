# Social database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class SocialModel:
    """Social contact database model."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["social"]
    
    async def create_indexes(self):
        """Create social-specific indexes."""
        await self.collection.create_index("lead_id")
        await self.collection.create_index("platform")
    
    async def find_by_lead_id(self, lead_id: str):
        """Find socials by lead ID."""
        return await self.collection.find({"lead_id": ObjectId(lead_id)}).to_list(length=None)
    
    async def find_by_id(self, social_id: str):
        """Find social by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(social_id)})
        except Exception:
            return None
    
    async def create_many(self, socials_data: List[dict]):
        """Create multiple socials."""
        for social_data in socials_data:
            social_data["created_at"] = datetime.utcnow()
            social_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_many(socials_data)
        return result.inserted_ids
    
    async def update(self, social_id: str, update_data: dict):
        """Update social."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(social_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(social_id)})
    
    async def delete(self, social_id: str):
        """Delete social."""
        return await self.collection.delete_one({"_id": ObjectId(social_id)})

# Global social model instance
social_model = SocialModel()
