# Sub Query database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class SubQueryModel:
    """Sub Query database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["sub_queries"]
    
    async def create_indexes(self):
        """Create sub query-specific indexes."""
        await self.collection.create_index("query_id")
        await self.collection.create_index("added_by")
        await self.collection.create_index([("query_id", 1), ("sub_query", 1)], unique=True)
    
    async def create(self, sub_query_data: dict) -> dict:
        """Create a new sub query."""
        sub_query_data["created_at"] = datetime.utcnow()
        sub_query_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(sub_query_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def find_by_id(self, sub_query_id: str) -> Optional[dict]:
        """Find sub query by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(sub_query_id)})
        except Exception:
            return None
    
    async def find_by_query_id(self, query_id: str) -> List[dict]:
        """Find all sub queries for a specific query."""
        return await self.collection.find({"query_id": ObjectId(query_id)}).to_list(length=None)
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Find all sub queries with pagination."""
        return await self.collection.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=None)
    
    async def update(self, sub_query_id: str, update_data: dict) -> Optional[dict]:
        """Update sub query."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(sub_query_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(sub_query_id)})
    
    async def delete(self, sub_query_id: str) -> bool:
        """Delete sub query."""
        result = await self.collection.delete_one({"_id": ObjectId(sub_query_id)})
        return result.deleted_count > 0
    
    async def count(self) -> int:
        """Count total sub queries."""
        return await self.collection.count_documents({})

# Global sub query model instance
sub_query_model = SubQueryModel()
