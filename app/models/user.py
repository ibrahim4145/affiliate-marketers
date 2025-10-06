# User database models and operations
from app.dependencies import get_database_connection
from typing import Optional
from bson import ObjectId
from datetime import datetime

class UserModel:
    """User database model with collection access."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["users"]
    
    async def create_indexes(self):
        """Create user-specific indexes."""
        await self.collection.create_index("email", unique=True)
    
    async def find_by_email(self, email: str):
        """Find user by email."""
        return await self.collection.find_one({"email": email})
    
    async def find_by_id(self, user_id: str):
        """Find user by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
    
    async def create(self, user_data: dict):
        """Create a new user."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(user_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update(self, user_id: str, update_data: dict):
        """Update user."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(user_id)})
    
    async def delete(self, user_id: str):
        """Delete user."""
        return await self.collection.delete_one({"_id": ObjectId(user_id)})

# Global user model instance
user_model = UserModel()
