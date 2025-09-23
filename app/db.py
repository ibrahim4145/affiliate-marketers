# app/db.py
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_DB = os.getenv("MONGO_DB")
MONGO_URI = os.getenv("MONGO_URI")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]  
