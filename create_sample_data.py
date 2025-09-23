#!/usr/bin/env python3
"""
Simple script to create sample data for the scraper API
"""

from pymongo import MongoClient
import os

def create_sample_data():
    """Create sample data in MongoDB"""
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "scraper_db")
    
    print(f"Connecting to: {mongodb_url}")
    print(f"Database: {database_name}")
    
    client = MongoClient(mongodb_url)
    db = client[database_name]
    
    try:
        # Create sample industries
        industries_data = [
            {"industry_name": "Technology"},
            {"industry_name": "Finance"},
            {"industry_name": "Healthcare"},
            {"industry_name": "Education"}
        ]
        
        # Clear existing data
        db.industries.drop()
        db.queries.drop()
        db.scraped_progress.drop()
        
        # Insert new data
        result = db.industries.insert_many(industries_data)
        print(f"✅ Created {len(result.inserted_ids)} industries")
        
        # Create sample queries
        queries_data = [
            {"query": "best SaaS tools for startups"},
            {"query": "crypto investment trends"},
            {"query": "AI solutions for healthcare"},
            {"query": "edtech platforms"}
        ]
        
        result = db.queries.insert_many(queries_data)
        print(f"✅ Created {len(result.inserted_ids)} queries")
        
        # Verify data
        industries_count = db.industries.count_documents({})
        queries_count = db.queries.count_documents({})
        
        print(f"\n📊 Verification:")
        print(f"  Industries: {industries_count}")
        print(f"  Queries: {queries_count}")
        
        # Show sample data
        print(f"\n📝 Sample Industries:")
        for industry in db.industries.find({}):
            print(f"  - {industry['industry_name']}")
        
        print(f"\n📝 Sample Queries:")
        for query in db.queries.find({}):
            print(f"  - {query['query']}")
        
        print("\n🎉 Sample data created successfully!")
        print("\n💡 You can now test the API endpoints:")
        print("  - POST http://localhost:8000/api/scraper/run")
        print("  - GET http://localhost:8000/api/scraper/status")
        print("  - GET http://localhost:8000/api/scraper/debug")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Creating Sample Data for Scraper API")
    print("=" * 50)
    create_sample_data()
