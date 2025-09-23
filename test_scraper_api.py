#!/usr/bin/env python3
"""
Test script for the Scraper Allocator API
Run this after starting the FastAPI server to test the endpoints.
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api"

def test_scraper_endpoints():
    """Test the scraper API endpoints"""
    
    print("🧪 Testing Scraper Allocator API")
    print("=" * 50)
    
    # Test 1: Get scraper status (should work even with empty collections)
    print("\n1. Testing GET /scraper/status")
    try:
        response = requests.get(f"{BASE_URL}/scraper/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Try to run scraper (should fail if no data)
    print("\n2. Testing POST /scraper/run (without data)")
    try:
        response = requests.post(f"{BASE_URL}/scraper/run")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Update progress (should fail with invalid ID)
    print("\n3. Testing PATCH /scraper/update-progress/invalid-id")
    try:
        update_data = {
            "done": True,
            "start_param": 10,
            "se_id": "test_session_123"
        }
        response = requests.patch(f"{BASE_URL}/scraper/update-progress/invalid-id", json=update_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Sample MongoDB commands to create test data:")
    print("=" * 50)
    
    print("""
# Connect to MongoDB and run these commands:

# 1. Create sample industries
db.industries.insertMany([
    { "industry_name": "Technology" },
    { "industry_name": "Finance" },
    { "industry_name": "Healthcare" },
    { "industry_name": "Education" }
]);

# 2. Create sample queries
db.queries.insertMany([
    { "query": "best SaaS tools for startups" },
    { "query": "crypto investment trends" },
    { "query": "AI solutions for healthcare" },
    { "query": "edtech platforms" }
]);

# 3. Check the data
db.industries.find({});
db.queries.find({});
""")

def show_api_usage():
    """Show how to use the API"""
    print("\n📚 API Usage Examples:")
    print("=" * 50)
    
    print("""
# 1. Get next scraping task
curl -X POST "http://localhost:8000/api/scraper/run"

# 2. Update progress
curl -X PATCH "http://localhost:8000/api/scraper/update-progress/{progress_id}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "done": true,
    "start_param": 15,
    "se_id": "session_abc123"
  }'

# 3. Get scraper status
curl -X GET "http://localhost:8000/api/scraper/status"
""")

if __name__ == "__main__":
    print("🚀 Scraper Allocator API Test Suite")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Start the server with: uvicorn app.main:app --reload")
    print()
    
    # Run tests
    test_scraper_endpoints()
    
    # Show sample data creation
    create_sample_data()
    
    # Show API usage
    show_api_usage()
    
    print("\n✅ Test completed!")
    print("💡 Tip: Create sample data in MongoDB first, then test the endpoints again.")
