# Query database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class QueryModel:
    """Query database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["queries"]
    
    async def create_indexes(self):
        """Create query-specific indexes."""
        await self.collection.create_index("query", unique=True)
    
    async def find_by_id(self, query_id: str):
        """Find query by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(query_id)})
        except Exception:
            return None
    
    async def find_by_query(self, query_text: str):
        """Find query by query text."""
        return await self.collection.find_one({"query": query_text})
    
    async def find_all(self):
        """Find all queries."""
        return await self.collection.find({}).sort("created_at", -1).to_list(length=None)
    
    async def create(self, query_data: dict):
        """Create a new query."""
        query_data["created_at"] = datetime.utcnow()
        query_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(query_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, query_id: str, update_data: dict):
        """Update query."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(query_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(query_id)})
    
    async def delete(self, query_id: str):
        """Delete query."""
        return await self.collection.delete_one({"_id": ObjectId(query_id)})
    
    async def check_query_conflict(self, query_text: str, exclude_id: str = None):
        """Check if query conflicts with existing."""
        query = {"query": query_text}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.find_one(query)

# Global query model instance
query_model = QueryModel()
