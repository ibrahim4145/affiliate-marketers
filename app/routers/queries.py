from fastapi import APIRouter, HTTPException, Depends
from app.schemas.query import QueryCreate, QueryUpdate, QueryOut
from app.crud.query import create_query, get_query_by_id, get_all_queries, update_query, delete_query
from app.utils.authentication import get_current_user
from typing import List

router = APIRouter(prefix="/queries", tags=["Queries"])

@router.post("/", response_model=QueryOut)
async def create_query_endpoint(
    query: QueryCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create a new query."""
    try:
        return await create_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query: {str(e)}")

@router.get("/", response_model=List[QueryOut])
async def get_queries(current_user: dict = Depends(get_current_user)):
    """Get all queries."""
    return await get_all_queries()

@router.get("/{query_id}", response_model=QueryOut)
async def get_query(
    query_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Get a specific query by ID."""
    query = await get_query_by_id(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query

@router.put("/{query_id}", response_model=QueryOut)
async def update_query_endpoint(
    query_id: str,
    query_update: QueryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a query."""
    try:
        updated_query = await update_query(query_id, query_update)
        if not updated_query:
            raise HTTPException(status_code=404, detail="Query not found")
        return updated_query
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update query: {str(e)}")

@router.delete("/{query_id}")
async def delete_query_endpoint(
    query_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a query."""
    success = await delete_query(query_id)
    if not success:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return {"message": "Query deleted successfully"}
