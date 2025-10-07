# Niche database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class NicheModel:
    """Niche database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["niches"]
    
    async def create_indexes(self):
        """Create niche-specific indexes."""
        await self.collection.create_index("niche_name", unique=True)
        await self.collection.create_index("category_id")
        await self.collection.create_index("description")
    
    async def find_by_id(self, niche_id: str):
        """Find niche by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(niche_id)})
        except Exception:
            return None
    
    async def find_by_name(self, niche_name: str):
        """Find niche by name."""
        return await self.collection.find_one({"niche_name": niche_name})
    
    async def find_by_category(self, category_id: str):
        """Find niches by category ID."""
        return await self.collection.find({"category_id": ObjectId(category_id)}).sort("created_at", -1).to_list(length=None)
    
    async def find_all(self, skip: int = 0, limit: int = 100):
        """Find all niches with pagination."""
        cursor = self.collection.find({}).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)
    
    async def count_all(self):
        """Count all niches."""
        return await self.collection.count_documents({})
    
    async def create(self, niche_data: dict):
        """Create a new niche."""
        niche_data["created_at"] = datetime.utcnow()
        niche_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(niche_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, niche_id: str, update_data: dict):
        """Update niche."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(niche_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(niche_id)})
    
    async def delete(self, niche_id: str):
        """Delete niche."""
        return await self.collection.delete_one({"_id": ObjectId(niche_id)})
    
    async def check_name_conflict(self, niche_name: str, exclude_id: str = None):
        """Check if niche name conflicts with existing."""
        query = {"niche_name": niche_name}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.find_one(query)
    
    async def search_niches(self, search_term: str, skip: int = 0, limit: int = 100):
        """Search niches by name or description."""
        search_query = {
            "$or": [
                {"niche_name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}}
            ]
        }
        cursor = self.collection.find(search_query).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

# Global niche model instance
niche_model = NicheModel()
