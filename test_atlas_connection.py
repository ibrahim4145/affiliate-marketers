#!/usr/bin/env python3
"""
Test script to check MongoDB Atlas connection and data
"""

from pymongo import MongoClient
import os

def test_atlas_connection():
    """Test connection to MongoDB Atlas and show actual data"""
    
    # You need to replace this with your actual Atlas connection string
    # Format: mongodb+srv://username:password@cluster.mongodb.net/
    mongodb_url = input("Enter your MongoDB Atlas connection string: ")
    
    # You need to replace this with your actual database name
    database_name = input("Enter your database name: ")
    
    print(f"Connecting to: {mongodb_url}")
    print(f"Database: {database_name}")
    
    try:
        client = MongoClient(mongodb_url)
        db = client[database_name]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # List all collections
        collections = db.list_collection_names()
        print(f"\n📁 Available collections: {collections}")
        
        # Check industries
        if 'industries' in collections:
            industries_count = db.industries.count_documents({})
            print(f"\n🏭 Industries count: {industries_count}")
            
            if industries_count > 0:
                print("📝 Sample industries:")
                for industry in db.industries.find({}).limit(5):
                    print(f"  - {industry}")
        
        # Check queries
        if 'queries' in collections:
            queries_count = db.queries.count_documents({})
            print(f"\n🔍 Queries count: {queries_count}")
            
            if queries_count > 0:
                print("📝 Sample queries:")
                for query in db.queries.find({}).limit(5):
                    print(f"  - {query}")
        
        # Check progress
        if 'scraped_progress' in collections:
            progress_count = db.scraped_progress.count_documents({})
            print(f"\n📊 Progress records: {progress_count}")
        
        print(f"\n🎉 Database connection successful!")
        print("💡 You can now test the API endpoints with your actual data.")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure:")
        print("  1. Your Atlas connection string is correct")
        print("  2. Your IP is whitelisted in Atlas")
        print("  3. Your database name is correct")
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Testing MongoDB Atlas Connection")
    print("=" * 50)
    test_atlas_connection()
