from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.models import QueryCreate, QueryUpdate, QueryOut
from app.auth import get_current_user
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/queries", tags=["Queries"])

# Helper: Convert MongoDB document to dict
def query_helper(query) -> dict:
    return {
        "id": str(query["_id"]),
        "query": query["query"],
        "description": query.get("description"),
        "created_at": query.get("created_at", datetime.utcnow()),
        "updated_at": query.get("updated_at", datetime.utcnow())
    }

@router.post("/", response_model=QueryOut)
async def create_query(
    query: QueryCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create a new query."""
    # Check if query already exists
    existing = await db["queries"].find_one({"query": query.query})
    if existing:
        raise HTTPException(status_code=400, detail="Query already exists")
    
    query_data = {
        "query": query.query,
        "description": query.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db["queries"].insert_one(query_data)
    created_query = await db["queries"].find_one({"_id": result.inserted_id})
    return query_helper(created_query)

@router.get("/", response_model=List[QueryOut])
async def get_queries(current_user: dict = Depends(get_current_user)):
    """Get all queries."""
    queries = await db["queries"].find({}).sort("created_at", -1).to_list(length=None)
    return [query_helper(query) for query in queries]

@router.get("/{query_id}", response_model=QueryOut)
async def get_query(
    query_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Get a specific query by ID."""
    try:
        query = await db["queries"].find_one({"_id": ObjectId(query_id)})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        return query_helper(query)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query ID")

@router.put("/{query_id}", response_model=QueryOut)
async def update_query(
    query_id: str,
    query_update: QueryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a query."""
    try:
        # Check if query exists
        existing_query = await db["queries"].find_one({"_id": ObjectId(query_id)})
        if not existing_query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Check if new query conflicts with existing query
        if query_update.query:
            query_conflict = await db["queries"].find_one({
                "query": query_update.query,
                "_id": {"$ne": ObjectId(query_id)}
            })
            if query_conflict:
                raise HTTPException(status_code=400, detail="Query already exists")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        if query_update.query is not None:
            update_data["query"] = query_update.query
        if query_update.description is not None:
            update_data["description"] = query_update.description
        
        # Update the query
        await db["queries"].update_one(
            {"_id": ObjectId(query_id)},
            {"$set": update_data}
        )
        
        # Return updated query
        updated_query = await db["queries"].find_one({"_id": ObjectId(query_id)})
        return query_helper(updated_query)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query ID")

@router.delete("/{query_id}")
async def delete_query(
    query_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a query."""
    try:
        # Check if query exists
        query = await db["queries"].find_one({"_id": ObjectId(query_id)})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Delete the query
        await db["queries"].delete_one({"_id": ObjectId(query_id)})
        
        return {"message": "Query deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query ID")
