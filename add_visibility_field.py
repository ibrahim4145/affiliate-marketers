#!/usr/bin/env python3
"""
Script to add visibility field to existing leads in the database.
This script will set all existing leads to visible=False by default.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def add_visibility_field():
    """Add visibility field to all existing leads."""
    
    # Get MongoDB connection string from environment or use default
    mongodb_url = os.getenv("MONGODB_URL", os.getenv("MONGO_URI"))
    database_name = os.getenv("MONGO_DB")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    leads_collection = db["leads"]
    
    try:
        print("🔍 Checking existing leads...")
        print(f"🔗 Connected to database: {database_name}")
        print(f"📁 Using collection: leads")
        
        # Count total leads
        total_leads = await leads_collection.count_documents({})
        print(f"📊 Total leads found: {total_leads}")
        
        # Check if any leads already have the visibility field
        leads_with_visibility = await leads_collection.count_documents({"visible": {"$exists": True}})
        print(f"👁️ Leads with visibility field: {leads_with_visibility}")
        
        if total_leads == 0:
            print("✅ No leads found. Nothing to update.")
            return
        
        # Count leads without visibility field
        leads_without_visibility = await leads_collection.count_documents({
            "visible": {"$exists": False}
        })
        
        print(f"📝 Leads without visibility field: {leads_without_visibility}")
        
        if leads_without_visibility == 0:
            print("✅ All leads already have visibility field. Nothing to update.")
            return
        
        # Update all leads without visibility field to set visible=False
        print("🔄 Adding visibility field to existing leads...")
        
        result = await leads_collection.update_many(
            {"visible": {"$exists": False}},
            {
                "$set": {
                    "visible": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"✅ Successfully updated {result.modified_count} leads")
        print("📋 All existing leads now have visibility=False by default")
        
        # Verify the update
        remaining_without_visibility = await leads_collection.count_documents({
            "visible": {"$exists": False}
        })
        
        if remaining_without_visibility == 0:
            print("✅ Verification successful: All leads now have visibility field")
        else:
            print(f"⚠️  Warning: {remaining_without_visibility} leads still missing visibility field")
        
        # Show summary
        visible_count = await leads_collection.count_documents({"visible": True})
        hidden_count = await leads_collection.count_documents({"visible": False})
        
        print(f"\n📊 Summary:")
        print(f"   - Visible leads: {visible_count}")
        print(f"   - Hidden leads: {hidden_count}")
        print(f"   - Total leads: {total_leads}")
        
    except Exception as e:
        print(f"❌ Error updating leads: {str(e)}")
        raise
    finally:
        # Close the connection
        client.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    print("🚀 Starting visibility field update script...")
    asyncio.run(add_visibility_field())
    print("✨ Script completed!")
