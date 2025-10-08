from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_database
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/scraper", tags=["Scraper"])

async def create_next_progress_record():
    """Create the next progress record in the sequence: niche -> query -> sub-query."""
    from app.models.query import query_model
    from app.models.niche import niche_model
    from app.models.sub_query import sub_query_model
    from app.models.scraper import scraper_progress_model
    
    # Get all niches and queries
    niches = await niche_model.collection.find({}).sort("created_at", 1).to_list(length=None)
    queries = await query_model.collection.find({}).sort("created_at", 1).to_list(length=None)
    
    if not niches or not queries:
        return None
    
    # Find the next combination to process
    for niche in niches:
        for query in queries:
            # Check if main query progress exists
            main_progress = await scraper_progress_model.collection.find_one({
                "niche_id": niche["_id"],
                "query_id": query["_id"],
                "$or": [
                    {"sub_query_id": {"$exists": False}},
                    {"sub_query_id": None}
                ]
            })
            
            if not main_progress:
                # Create main query progress
                progress_data = {
                    "niche_id": niche["_id"],
                    "query_id": query["_id"],
                    "sub_query_id": None,
                    "done": False,
                    "page_num": 1,
                    "search_engine_id": None
                }
                return await scraper_progress_model.create(progress_data)
            
            # Check if main query is done
            if main_progress.get("done", False):
                # Main query is done, check for sub-queries
                sub_queries = await sub_query_model.find_by_query_id(str(query["_id"]))
                
                for sub_query in sub_queries:
                    # Check if sub-query progress exists
                    sub_progress = await scraper_progress_model.collection.find_one({
                        "niche_id": niche["_id"],
                        "query_id": query["_id"],
                        "sub_query_id": sub_query["_id"]
                    })
                    
                    if not sub_progress:
                        # Create sub-query progress
                        progress_data = {
                            "niche_id": niche["_id"],
                            "query_id": query["_id"],
                            "sub_query_id": sub_query["_id"],
                            "done": False,
                            "page_num": 1,
                            "search_engine_id": None
                        }
                        return await scraper_progress_model.create(progress_data)
                    
                    # Check if sub-query is done
                    if not sub_progress.get("done", False):
                        return sub_progress
            else:
                # Main query not done, return it
                return main_progress
    
    return None


# Scraper Schemas
class ScraperRunResponse(BaseModel):
    niche_name: str
    query: str
    page_num: int
    scraper_progress_id: str

class UpdateProgressRequest(BaseModel):
    done: bool
    page_num: int
    search_engine_id: Optional[str] = None

class UpdateProgressResponse(BaseModel):
    id: str
    niche_id: str
    query_id: str
    done: bool
    page_num: int
    search_engine_id: Optional[str] = None
    updated_at: datetime

@router.get("/run", response_model=ScraperRunResponse)
async def run_scraper(
    db=Depends(get_database)
):
    """Assigns the next scraping task based on progress tracking."""
    try:
        # Get collections
        from app.models.niche import niche_model
        from app.models.query import query_model
        from app.models.scraper import scraper_progress_model
        
        niches_collection = niche_model.collection
        queries_collection = query_model.collection
        progress_collection = scraper_progress_model.collection
        
        # Check if there are any progress records
        progress_record = await progress_collection.find_one({"done": False})
        
        if not progress_record:
            # No progress records exist, create the first one
            progress_record = await create_next_progress_record()
            if not progress_record:
                raise HTTPException(status_code=404, detail="No queries or niches found")
        
        # Get niche and query details
        niche = await niches_collection.find_one({"_id": progress_record["niche_id"]})
        query = await queries_collection.find_one({"_id": progress_record["query_id"]})
        
        if not niche or not query:
            raise HTTPException(status_code=404, detail="Associated niche or query not found")
        
        # Build the query string with placeholder replacement
        if progress_record.get("sub_query_id"):
            from app.models.sub_query import sub_query_model
            sub_query = await sub_query_model.find_by_id(str(progress_record["sub_query_id"]))
            if sub_query:
                # Replace {{niche}} in the parent query, then inject into sub-query via {{query}}
                parent_query_text = query["query"].replace("{{niche}}", niche["niche_name"])  # main query resolved with niche
                modified_query = sub_query["sub_query"].replace("{{query}}", parent_query_text)
            else:
                modified_query = query["query"].replace("{{niche}}", niche["niche_name"]) 
        else:
            # Main query: replace {{niche}} with the niche name if present
            modified_query = query["query"].replace("{{niche}}", niche["niche_name"]) 
        
        # Ensure backward compatibility for existing records with start_param
        effective_page_num = progress_record.get("page_num") if progress_record.get("page_num") is not None else progress_record.get("start_param", 1)
        if "start_param" in progress_record and "page_num" not in progress_record:
            # Persist migration for this record: set page_num and unset start_param
            try:
                await progress_collection.update_one(
                    {"_id": progress_record["_id"]},
                    {"$set": {"page_num": effective_page_num}, "$unset": {"start_param": ""}}
                )
            except Exception:
                pass

        return ScraperRunResponse(
            niche_name=niche["niche_name"],
            query=modified_query,
            page_num=effective_page_num,
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
        
        # Prepare update data (store page_num; remove legacy start_param if present)
        update_fields = {
            "done": update_data.done,
            "page_num": update_data.page_num,
            "updated_at": datetime.utcnow()
        }
        
        if update_data.search_engine_id is not None:
            update_fields["search_engine_id"] = update_data.search_engine_id
        
        # Update the progress record
        await progress_collection.update_one(
            {"_id": ObjectId(progress_id)},
            {"$set": update_fields, "$unset": {"start_param": ""}}
        )
        
        # Return updated record
        updated_record = await progress_collection.find_one({"_id": ObjectId(progress_id)})
        return UpdateProgressResponse(
            id=str(updated_record["_id"]),
            niche_id=str(updated_record["niche_id"]),
            query_id=str(updated_record["query_id"]),
            done=updated_record["done"],
            page_num=updated_record.get("page_num", updated_record.get("start_param", 1)),
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
        "niche_id": str(progress["niche_id"]),
        "query_id": str(progress["query_id"]),
        "done": progress["done"],
        "page_num": progress.get("page_num", progress.get("start_param", 1)),
        "search_engine_id": progress.get("search_engine_id"),
        "created_at": progress.get("created_at"),
        "updated_at": progress.get("updated_at")
    }
