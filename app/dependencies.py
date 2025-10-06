from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

MONGO_DB = os.getenv("MONGO_DB")
MONGO_URI = os.getenv("MONGODB_URL", os.getenv("MONGO_URI"))

# Global database connection
_client: Optional[AsyncIOMotorClient] = None
_db = None

def get_database_connection():
    """Get database connection."""
    global _db
    if _db is None:
        global _client
        if _client is None:
            _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[MONGO_DB]
    return _db

async def get_database():
    """Get database connection dependency."""
    return get_database_connection()
