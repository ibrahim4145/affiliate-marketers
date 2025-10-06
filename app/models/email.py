# Email database models and operations
from app.dependencies import get_database_connection
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class EmailModel:
    """Email contact database model."""
    
    def __init__(self):
        self._db = None
    
    @property
    def collection(self):
        if self._db is None:
            self._db = get_database_connection()
        return self._db["email"]
    
    async def create_indexes(self):
        """Create email-specific indexes."""
        await self.collection.create_index("lead_id")
        await self.collection.create_index("email")
    
    async def find_by_lead_id(self, lead_id: str):
        """Find emails by lead ID."""
        return await self.collection.find({"lead_id": ObjectId(lead_id)}).to_list(length=None)
    
    async def find_by_id(self, email_id: str):
        """Find email by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(email_id)})
        except Exception:
            return None
    
    async def create_many(self, emails_data: List[dict]):
        """Create multiple emails."""
        for email_data in emails_data:
            email_data["created_at"] = datetime.utcnow()
            email_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_many(emails_data)
        return result.inserted_ids
    
    async def update(self, email_id: str, update_data: dict):
        """Update email."""
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(email_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(email_id)})
    
    async def delete(self, email_id: str):
        """Delete email."""
        return await self.collection.delete_one({"_id": ObjectId(email_id)})

# Global email model instance
email_model = EmailModel()
