from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_database
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/scraper", tags=["Scraper"])

# Scraper Schemas
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

@router.get("/run", response_model=ScraperRunResponse)
async def run_scraper(
    db=Depends(get_database)
):
    """Assigns the next scraping task based on progress tracking."""
    try:
        # Get collections
        from app.models.industry import industry_model
        from app.models.query import query_model
        from app.models.scraper import scraper_progress_model
        
        industries_collection = industry_model.collection
        queries_collection = query_model.collection
        progress_collection = scraper_progress_model.collection
        
        # Find the next incomplete progress record
        progress_record = await progress_collection.find_one({"done": False})
        
        if not progress_record:
            raise HTTPException(status_code=404, detail="No pending scraping tasks found")
        
        # Get industry and query details
        industry = await industries_collection.find_one({"_id": progress_record["industry_id"]})
        query = await queries_collection.find_one({"_id": progress_record["query_id"]})
        
        if not industry or not query:
            raise HTTPException(status_code=404, detail="Associated industry or query not found")
        
        return ScraperRunResponse(
            industry_name=industry["industry_name"],
            query=query["query"],
            start_param=progress_record["start_param"],
            scraper_progress_id=str(progress_record["_id"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scraper task: {str(e)}")

@router.put("/progress/{progress_id}", response_model=UpdateProgressResponse)
async def update_progress(
    progress_id: str,
    update_data: UpdateProgressRequest,
    db=Depends(get_database)
):
    """Update scraper progress."""
    try:
        from app.models.scraper import scraper_progress_model
        progress_collection = scraper_progress_model.collection
        
        # Check if progress record exists
        progress_record = await progress_collection.find_one({"_id": ObjectId(progress_id)})
        if not progress_record:
            raise HTTPException(status_code=404, detail="Progress record not found")
        
        # Prepare update data
        update_fields = {
            "done": update_data.done,
            "start_param": update_data.start_param,
            "updated_at": datetime.utcnow()
        }
        
        if update_data.search_engine_id is not None:
            update_fields["search_engine_id"] = update_data.search_engine_id
        
        # Update the progress record
        await progress_collection.update_one(
            {"_id": ObjectId(progress_id)},
            {"$set": update_fields}
        )
        
        # Return updated record
        updated_record = await progress_collection.find_one({"_id": ObjectId(progress_id)})
        return UpdateProgressResponse(
            id=str(updated_record["_id"]),
            industry_id=str(updated_record["industry_id"]),
            query_id=str(updated_record["query_id"]),
            done=updated_record["done"],
            start_param=updated_record["start_param"],
            search_engine_id=updated_record.get("search_engine_id"),
            updated_at=updated_record["updated_at"]
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid progress ID")

@router.get("/progress")
async def get_progress(
    db=Depends(get_database)
):
    """Get all scraper progress records."""
    try:
        from app.models.scraper import scraper_progress_model
        progress_collection = scraper_progress_model.collection
        progress_records = await progress_collection.find({}).sort("created_at", -1).to_list(length=None)
        
        return [progress_helper(record) for record in progress_records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve progress: {str(e)}")

def progress_helper(progress) -> dict:
    """Convert MongoDB document to progress response."""
    return {
        "id": str(progress["_id"]),
        "industry_id": str(progress["industry_id"]),
        "query_id": str(progress["query_id"]),
        "done": progress["done"],
        "start_param": progress["start_param"],
        "search_engine_id": progress.get("search_engine_id"),
        "created_at": progress.get("created_at"),
        "updated_at": progress.get("updated_at")
    }
