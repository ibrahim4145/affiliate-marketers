from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
import os
from datetime import datetime

router = APIRouter()

# MongoDB connection
async def get_database():
    mongodb_url = os.getenv("MONGO_URI")
    database_name = os.getenv("MONGO_DB")
    client = AsyncIOMotorClient(mongodb_url)
    return client[database_name]

# Pydantic models
class ScraperRunResponse(BaseModel):
    industry_name: str
    query: str
    start_param: int
    scraper_progress_id: str

class UpdateProgressRequest(BaseModel):
    done: bool
    start_param: int
    search_engine_id: Optional[str] = None

class UpdateProgressResponse(BaseModel):
    id: str
    industry_id: str
    query_id: str
    done: bool
    start_param: int
    search_engine_id: Optional[str] = None
    updated_at: datetime

@router.get("/scraper/run", response_model=ScraperRunResponse)
async def run_scraper(db=Depends(get_database)):
    """
    Assigns the next scraping task based on progress tracking.
    """
    try:
        # Get collections
        industries_collection = db.industries
        queries_collection = db.queries
        progress_collection = db.scraped_progress
        
        # Debug: List all collections in the database
        collections = await db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Check if industries and queries exist
        industries_count = await industries_collection.count_documents({})
        queries_count = await queries_collection.count_documents({})
        
        print(f"Industries count: {industries_count}")
        print(f"Queries count: {queries_count}")
        
        # Debug: Try to find any documents in industries
        sample_industries = await industries_collection.find({}).limit(5).to_list(length=5)
        print(f"Sample industries: {sample_industries}")
        
        if industries_count == 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No industries found. Available collections: {collections}. Please add industries first."
            )
        
        if queries_count == 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No queries found. Available collections: {collections}. Please add queries first."
            )
        
        # Get all industries and queries for processing
        industries = await industries_collection.find({}).sort("_id", 1).to_list(length=None)
        queries = await queries_collection.find({}).sort("_id", 1).to_list(length=None)
        
        # Check if scraped_progress is empty
        progress_count = await progress_collection.count_documents({})
        
        if progress_count == 0:
            # First run - pick first industry and first query
            industry = industries[0]
            query = queries[0]
            start_param = 1
            
            # Insert new progress record
            progress_doc = {
                "industry_id": str(industry["_id"]),
                "query_id": str(query["_id"]),
                "done": False,
                "start_param": start_param,
                "search_engine_id": None,
                "created_at": datetime.utcnow()
            }
            result = await progress_collection.insert_one(progress_doc)
            
            # Process query for industry parameter replacement
            processed_query = query["query"]
            if "{{industry}}" in processed_query:
                processed_query = processed_query.replace("{{industry}}", industry["industry_name"])
            
            return ScraperRunResponse(
                industry_name=industry["industry_name"],
                query=processed_query,
                start_param=start_param,
                scraper_progress_id=str(result.inserted_id)
            )
        
        # Get the last progress record
        last_progress = await progress_collection.find({}).sort("_id", -1).limit(1).to_list(length=1)
        
        if not last_progress:
            raise HTTPException(status_code=500, detail="Failed to retrieve progress data")
        
        last_record = last_progress[0]
        
        # If last record is not done, return the same task
        if not last_record.get("done", False):
            # Get the industry and query for the last record (handle both old and new field names)
            industry_id = last_record.get("industry_id") or last_record.get("i_id")
            query_id = last_record.get("query_id") or last_record.get("q_id")
            
            industry = await industries_collection.find_one({"_id": ObjectId(industry_id)})
            query = await queries_collection.find_one({"_id": ObjectId(query_id)})
            
            if not industry or not query:
                raise HTTPException(status_code=500, detail="Referenced industry or query not found")
            
            # Process query for industry parameter replacement
            processed_query = query["query"]
            if "{{industry}}" in processed_query:
                processed_query = processed_query.replace("{{industry}}", industry["industry_name"])
            
            return ScraperRunResponse(
                industry_name=industry["industry_name"],
                query=processed_query,
                start_param=last_record["start_param"],
                scraper_progress_id=str(last_record["_id"])
            )
        
        # Last record is done - determine next task (handle both old and new field names)
        current_industry_id = last_record.get("industry_id") or last_record.get("i_id")
        current_query_id = last_record.get("query_id") or last_record.get("q_id")
        
        # Find current industry and query indices
        current_industry_index = next(
            (i for i, ind in enumerate(industries) if str(ind["_id"]) == current_industry_id), 
            -1
        )
        current_query_index = next(
            (i for i, q in enumerate(queries) if str(q["_id"]) == current_query_id), 
            -1
        )
        
        if current_industry_index == -1 or current_query_index == -1:
            raise HTTPException(status_code=500, detail="Current progress references invalid data")
        
        # Determine next task
        next_industry = None
        next_query = None
        start_param = 1
        
        # Check if we can move to next industry for same query
        if current_industry_index < len(industries) - 1:
            # Move to next industry for same query
            next_industry = industries[current_industry_index + 1]
            next_query = queries[current_query_index]
        else:
            # Current query has been run for all industries
            if current_query_index < len(queries) - 1:
                # Move to next query, first industry
                next_query = queries[current_query_index + 1]
                next_industry = industries[0]
            else:
                # All queries have been run for all industries
                # Start over from the beginning
                # next_industry = industries[0]
                # next_query = queries[0]

                raise HTTPException(
                    status_code=200,
                    detail="All industries and queries have been processed."
                )
        
        # Insert new progress record
        progress_doc = {
            "industry_id": str(next_industry["_id"]),
            "query_id": str(next_query["_id"]),
            "done": False,
            "start_param": start_param,
            "search_engine_id": None,
            "created_at": datetime.utcnow()
        }
        result = await progress_collection.insert_one(progress_doc)
        
        # Process query for industry parameter replacement
        processed_query = next_query["query"]
        if "{{industry}}" in processed_query:
            processed_query = processed_query.replace("{{industry}}", next_industry["industry_name"])
        
        return ScraperRunResponse(
            industry_name=next_industry["industry_name"],
            query=processed_query,
            start_param=start_param,
            scraper_progress_id=str(result.inserted_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.patch("/scraper/update-progress/{scraper_progress_id}", response_model=UpdateProgressResponse)
async def update_progress(
    scraper_progress_id: str,
    request: UpdateProgressRequest,
    db=Depends(get_database)
):
    """
    Updates an existing scraped_progress record.
    """
    try:
        progress_collection = db.scraped_progress
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(scraper_progress_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid scraper progress ID format")
        
        # Check if record exists
        existing_record = await progress_collection.find_one({"_id": object_id})
        if not existing_record:
            raise HTTPException(status_code=404, detail="Progress record not found")
        
        # Prepare update data
        update_data = {
            "done": request.done,
            "start_param": request.start_param,
            "updated_at": datetime.utcnow()
        }
        
        if request.search_engine_id is not None:
            update_data["search_engine_id"] = request.search_engine_id
        
        # Update the record
        await progress_collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        # Get the updated record
        updated_record = await progress_collection.find_one({"_id": object_id})
        
        return UpdateProgressResponse(
            id=str(updated_record["_id"]),
            industry_id=updated_record.get("industry_id") or updated_record.get("i_id"),
            query_id=updated_record.get("query_id") or updated_record.get("q_id"),
            done=updated_record["done"],
            start_param=updated_record["start_param"],
            search_engine_id=updated_record.get("search_engine_id") or updated_record.get("se_id"),
            updated_at=updated_record["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/scraper/debug")
async def debug_database(db=Depends(get_database)):
    """
    Debug endpoint to check database contents.
    """
    try:
        # Simple test to avoid serialization issues
        return {"status": "ok", "message": "Debug endpoint working"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@router.get("/scraper/status")
async def get_scraper_status(db=Depends(get_database)):
    """
    Get current scraper status and statistics.
    """
    try:
        industries_collection = db.industries
        queries_collection = db.queries
        progress_collection = db.scraped_progress
        
        # Get counts
        industries_count = await industries_collection.count_documents({})
        queries_count = await queries_collection.count_documents({})
        total_progress = await progress_collection.count_documents({})
        completed_progress = await progress_collection.count_documents({"done": True})
        
        # Get last progress record - simplified to avoid serialization issues
        last_progress_count = await progress_collection.count_documents({})
        
        return {
            "industries_count": industries_count,
            "queries_count": queries_count,
            "total_progress": total_progress,
            "completed_progress": completed_progress,
            "has_progress": last_progress_count > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
