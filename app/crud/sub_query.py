from typing import List, Optional
from bson import ObjectId
from app.models.sub_query import sub_query_model
from app.models.query import query_model
from app.schemas.sub_query import SubQueryCreate, SubQueryUpdate, SubQueryResponse, SubQueryListResponse, SubQueryWithQueryInfo

def sub_query_helper(sub_query) -> dict:
    """Convert MongoDB document to sub query response."""
    return {
        "id": str(sub_query["_id"]),
        "query_id": str(sub_query["query_id"]),
        "sub_query": sub_query["sub_query"],
        "added_by": sub_query["added_by"],
        "description": sub_query.get("description"),
        "created_at": sub_query["created_at"],
        "updated_at": sub_query["updated_at"]
    }

async def create_sub_query(sub_query: SubQueryCreate) -> SubQueryResponse:
    """Create a new sub query."""
    # Validate that the parent query exists
    parent_query = await query_model.find_by_id(sub_query.query_id)
    if not parent_query:
        raise ValueError("Parent query not found")
    
    # Check for duplicate sub query for the same parent query
    existing = await sub_query_model.collection.find_one({
        "query_id": ObjectId(sub_query.query_id),
        "sub_query": sub_query.sub_query
    })
    if existing:
        raise ValueError("Sub query already exists for this parent query")
    
    sub_query_data = {
        "query_id": ObjectId(sub_query.query_id),
        "sub_query": sub_query.sub_query,
        "added_by": sub_query.added_by,
        "description": sub_query.description
    }
    
    created_sub_query = await sub_query_model.create(sub_query_data)
    return SubQueryResponse(**sub_query_helper(created_sub_query))

async def get_sub_query_by_id(sub_query_id: str) -> Optional[SubQueryResponse]:
    """Get sub query by ID."""
    sub_query = await sub_query_model.find_by_id(sub_query_id)
    if not sub_query:
        return None
    return SubQueryResponse(**sub_query_helper(sub_query))

async def get_sub_queries_by_query_id(query_id: str) -> List[SubQueryResponse]:
    """Get all sub queries for a specific query."""
    sub_queries = await sub_query_model.find_by_query_id(query_id)
    return [SubQueryResponse(**sub_query_helper(sq)) for sq in sub_queries]

async def get_all_sub_queries(skip: int = 0, limit: int = 100) -> SubQueryListResponse:
    """Get all sub queries with pagination."""
    sub_queries = await sub_query_model.find_all(skip, limit)
    total = await sub_query_model.count()
    
    return SubQueryListResponse(
        sub_queries=[SubQueryResponse(**sub_query_helper(sq)) for sq in sub_queries],
        total=total,
        skip=skip,
        limit=limit
    )

async def get_sub_queries_with_query_info(skip: int = 0, limit: int = 100) -> List[SubQueryWithQueryInfo]:
    """Get all sub queries with parent query information."""
    sub_queries = await sub_query_model.find_all(skip, limit)
    result = []
    
    for sq in sub_queries:
        # Get parent query info
        parent_query = await query_model.find_by_id(str(sq["query_id"]))
        
        sub_query_data = sub_query_helper(sq)
        sub_query_data["parent_query"] = {
            "id": str(parent_query["_id"]),
            "query": parent_query["query"],
            "description": parent_query.get("description")
        } if parent_query else None
        
        result.append(SubQueryWithQueryInfo(**sub_query_data))
    
    return result

async def update_sub_query(sub_query_id: str, sub_query_update: SubQueryUpdate) -> Optional[SubQueryResponse]:
    """Update sub query."""
    # Check if sub query exists
    existing = await sub_query_model.find_by_id(sub_query_id)
    if not existing:
        return None
    
    # If updating query_id, validate the new parent query exists
    if sub_query_update.query_id:
        parent_query = await query_model.find_by_id(sub_query_update.query_id)
        if not parent_query:
            raise ValueError("Parent query not found")
    
    # Prepare update data
    update_data = {}
    if sub_query_update.query_id is not None:
        update_data["query_id"] = ObjectId(sub_query_update.query_id)
    if sub_query_update.sub_query is not None:
        update_data["sub_query"] = sub_query_update.sub_query
    if sub_query_update.added_by is not None:
        update_data["added_by"] = sub_query_update.added_by
    if sub_query_update.description is not None:
        update_data["description"] = sub_query_update.description
    
    updated_sub_query = await sub_query_model.update(sub_query_id, update_data)
    if not updated_sub_query:
        return None
    
    return SubQueryResponse(**sub_query_helper(updated_sub_query))

async def delete_sub_query(sub_query_id: str) -> bool:
    """Delete sub query."""
    return await sub_query_model.delete(sub_query_id)
