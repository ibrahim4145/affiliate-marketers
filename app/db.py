# app/db.py
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_DB = os.getenv("MONGO_DB", "affiliate_scraper")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]  
