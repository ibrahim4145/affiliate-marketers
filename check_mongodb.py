#!/usr/bin/env python3
"""
Script to check MongoDB data and help debug the scraper API
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_mongodb():
    """Check MongoDB contents"""
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "scraper_db")
    
    print(f"Connecting to: {mongodb_url}")
    print(f"Database: {database_name}")
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    
    try:
        # List all databases
        print("\n📊 Available databases:")
        databases = await client.list_database_names()
        for db_name in databases:
            print(f"  - {db_name}")
        
        # List collections in current database
        print(f"\n📁 Collections in '{database_name}':")
        collections = await db.list_collection_names()
        for collection in collections:
            print(f"  - {collection}")
        
        # Check industries collection
        print(f"\n🏭 Industries collection:")
        try:
            industries_count = await db.industries.count_documents({})
            print(f"  Count: {industries_count}")
            
            if industries_count > 0:
                industries = await db.industries.find({}).limit(5).to_list(length=5)
                print("  Sample documents:")
                for i, industry in enumerate(industries):
                    print(f"    {i+1}. {industry}")
            else:
                print("  No documents found")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check queries collection
        print(f"\n🔍 Queries collection:")
        try:
            queries_count = await db.queries.count_documents({})
            print(f"  Count: {queries_count}")
            
            if queries_count > 0:
                queries = await db.queries.find({}).limit(5).to_list(length=5)
                print("  Sample documents:")
                for i, query in enumerate(queries):
                    print(f"    {i+1}. {query}")
            else:
                print("  No documents found")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check progress collection
        print(f"\n📈 Progress collection:")
        try:
            progress_count = await db.scraped_progress.count_documents({})
            print(f"  Count: {progress_count}")
            
            if progress_count > 0:
                progress = await db.scraped_progress.find({}).limit(5).to_list(length=5)
                print("  Sample documents:")
                for i, prog in enumerate(progress):
                    print(f"    {i+1}. {prog}")
            else:
                print("  No documents found")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check if data exists in other possible collections
        print(f"\n🔍 Checking for data in other collections:")
        for collection_name in collections:
            if collection_name not in ['industries', 'queries', 'scraped_progress']:
                try:
                    count = await db[collection_name].count_documents({})
                    if count > 0:
                        print(f"  {collection_name}: {count} documents")
                        sample = await db[collection_name].find({}).limit(1).to_list(length=1)
                        if sample:
                            print(f"    Sample: {sample[0]}")
                except Exception as e:
                    print(f"  {collection_name}: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
    finally:
        client.close()

async def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "scraper_db")
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    
    try:
        # Create sample industries
        industries_data = [
            {"industry_name": "Technology"},
            {"industry_name": "Finance"},
            {"industry_name": "Healthcare"},
            {"industry_name": "Education"}
        ]
        
        result = await db.industries.insert_many(industries_data)
        print(f"✅ Created {len(result.inserted_ids)} industries")
        
        # Create sample queries
        queries_data = [
            {"query": "best SaaS tools for startups"},
            {"query": "crypto investment trends"},
            {"query": "AI solutions for healthcare"},
            {"query": "edtech platforms"}
        ]
        
        result = await db.queries.insert_many(queries_data)
        print(f"✅ Created {len(result.inserted_ids)} queries")
        
        print("\n🎉 Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🔍 MongoDB Data Checker")
    print("=" * 50)
    
    # Check current data
    asyncio.run(check_mongodb())
    
    # Ask if user wants to create sample data
    print("\n" + "=" * 50)
    response = input("Do you want to create sample data? (y/n): ").lower().strip()
    
    if response == 'y':
        asyncio.run(create_sample_data())
        print("\n🔄 Re-checking data after creation:")
        asyncio.run(check_mongodb())
    
    print("\n✅ Check complete!")
    print("\n💡 Next steps:")
    print("1. Make sure your MongoDB is running")
    print("2. Check the database name in your environment variables")
    print("3. Test the API endpoints:")
    print("   - GET http://localhost:8000/api/scraper/debug")
    print("   - POST http://localhost:8000/api/scraper/run")
