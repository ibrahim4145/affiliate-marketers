# Industry database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class IndustryModel:
    """Industry database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["industries"]
    
    async def create_indexes(self):
        """Create industry-specific indexes."""
        await self.collection.create_index("industry_name", unique=True)
    
    async def find_by_id(self, industry_id: str):
        """Find industry by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(industry_id)})
        except Exception:
            return None
    
    async def find_by_name(self, industry_name: str):
        """Find industry by name."""
        return await self.collection.find_one({"industry_name": industry_name})
    
    async def find_all(self):
        """Find all industries."""
        return await self.collection.find({}).sort("created_at", -1).to_list(length=None)
    
    async def create(self, industry_data: dict):
        """Create a new industry."""
        industry_data["created_at"] = datetime.utcnow()
        industry_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(industry_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, industry_id: str, update_data: dict):
        """Update industry."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(industry_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(industry_id)})
    
    async def delete(self, industry_id: str):
        """Delete industry."""
        return await self.collection.delete_one({"_id": ObjectId(industry_id)})
    
    async def check_name_conflict(self, industry_name: str, exclude_id: str = None):
        """Check if industry name conflicts with existing."""
        query = {"industry_name": industry_name}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.find_one(query)

# Global industry model instance
industry_model = IndustryModel()
