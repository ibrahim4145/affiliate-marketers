# Category database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class CategoryModel:
    """Category database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["categories"]
    
    async def create_indexes(self):
        """Create category-specific indexes."""
        await self.collection.create_index("category_name", unique=True)
        await self.collection.create_index("description")
    
    async def find_by_id(self, category_id: str):
        """Find category by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(category_id)})
        except Exception:
            return None
    
    async def find_by_name(self, category_name: str):
        """Find category by name."""
        return await self.collection.find_one({"category_name": category_name})
    
    async def find_all(self, skip: int = 0, limit: int = 100):
        """Find all categories with pagination."""
        cursor = self.collection.find({}).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)
    
    async def count_all(self):
        """Count all categories."""
        return await self.collection.count_documents({})
    
    async def create(self, category_data: dict):
        """Create a new category."""
        category_data["created_at"] = datetime.utcnow()
        category_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(category_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, category_id: str, update_data: dict):
        """Update category."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(category_id)})
    
    async def delete(self, category_id: str):
        """Delete category."""
        return await self.collection.delete_one({"_id": ObjectId(category_id)})
    
    async def check_name_conflict(self, category_name: str, exclude_id: str = None):
        """Check if category name conflicts with existing."""
        query = {"category_name": category_name}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.find_one(query)

# Global category model instance
category_model = CategoryModel()
