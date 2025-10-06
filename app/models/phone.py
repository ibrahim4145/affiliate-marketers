# Phone database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class PhoneModel:
    """Phone contact database model."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["phone"]
    
    async def create_indexes(self):
        """Create phone-specific indexes."""
        await self.collection.create_index("lead_id")
        await self.collection.create_index("phone")
    
    async def find_by_lead_id(self, lead_id: str):
        """Find phones by lead ID."""
        return await self.collection.find({"lead_id": ObjectId(lead_id)}).to_list(length=None)
    
    async def find_by_id(self, phone_id: str):
        """Find phone by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(phone_id)})
        except Exception:
            return None
    
    async def create_many(self, phones_data: List[dict]):
        """Create multiple phones."""
        for phone_data in phones_data:
            phone_data["created_at"] = datetime.utcnow()
            phone_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_many(phones_data)
        return result.inserted_ids
    
    async def update(self, phone_id: str, update_data: dict):
        """Update phone."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(phone_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(phone_id)})
    
    async def delete(self, phone_id: str):
        """Delete phone."""
        return await self.collection.delete_one({"_id": ObjectId(phone_id)})

# Global phone model instance
phone_model = PhoneModel()
