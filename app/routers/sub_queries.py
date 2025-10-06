from fastapi import APIRouter, HTTPException, Depends
from app.schemas.sub_query import SubQueryCreate, SubQueryUpdate, SubQueryResponse, SubQueryListResponse, SubQueryWithQueryInfo
from app.crud.sub_query import (
    create_sub_query, get_sub_query_by_id, get_sub_queries_by_query_id,
    get_all_sub_queries, get_sub_queries_with_query_info, update_sub_query, delete_sub_query
)
from app.dependencies import get_database
from typing import List, Optional

router = APIRouter(prefix="/sub-queries", tags=["Sub Queries"])

@router.post("/", response_model=SubQueryResponse)
async def create_sub_query_endpoint(
    sub_query: SubQueryCreate,
    db=Depends(get_database)
):
    """Create a new sub query."""
    try:
        return await create_sub_query(sub_query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sub query: {str(e)}")

@router.get("/", response_model=SubQueryListResponse)
async def get_sub_queries(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_database)
):
    """Get all sub queries with pagination."""
    try:
        return await get_all_sub_queries(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sub queries: {str(e)}")

@router.get("/with-query-info", response_model=List[SubQueryWithQueryInfo])
async def get_sub_queries_with_query_info_endpoint(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_database)
):
    """Get all sub queries with parent query information."""
    try:
        return await get_sub_queries_with_query_info(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sub queries with query info: {str(e)}")

@router.get("/by-query/{query_id}", response_model=List[SubQueryResponse])
async def get_sub_queries_by_query(
    query_id: str,
    db=Depends(get_database)
):
    """Get all sub queries for a specific query."""
    try:
        return await get_sub_queries_by_query_id(query_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sub queries for query: {str(e)}")

@router.get("/{sub_query_id}", response_model=SubQueryResponse)
async def get_sub_query(
    sub_query_id: str,
    db=Depends(get_database)
):
    """Get sub query by ID."""
    try:
        sub_query = await get_sub_query_by_id(sub_query_id)
        if not sub_query:
            raise HTTPException(status_code=404, detail="Sub query not found")
        return sub_query
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sub query: {str(e)}")

@router.put("/{sub_query_id}", response_model=SubQueryResponse)
async def update_sub_query_endpoint(
    sub_query_id: str,
    sub_query_update: SubQueryUpdate,
    db=Depends(get_database)
):
    """Update sub query."""
    try:
        updated_sub_query = await update_sub_query(sub_query_id, sub_query_update)
        if not updated_sub_query:
            raise HTTPException(status_code=404, detail="Sub query not found")
        return updated_sub_query
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update sub query: {str(e)}")

@router.delete("/{sub_query_id}")
async def delete_sub_query_endpoint(
    sub_query_id: str,
    db=Depends(get_database)
):
    """Delete sub query."""
    try:
        deleted = await delete_sub_query(sub_query_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Sub query not found")
        return {"message": "Sub query deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete sub query: {str(e)}")
