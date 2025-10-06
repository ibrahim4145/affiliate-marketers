from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.models.query import query_model
from app.schemas.query import QueryCreate, QueryUpdate, QueryOut

async def create_query(query: QueryCreate) -> QueryOut:
    """Create a new query."""
    # Check if query already exists
    existing = await query_model.find_by_query(query.query)
    if existing:
        raise ValueError("Query already exists")
    
    query_data = {
        "query": query.query,
        "description": query.description
    }
    
    created_query = await query_model.create(query_data)
    return query_helper(created_query)

async def get_query_by_id(query_id: str) -> Optional[QueryOut]:
    """Get query by ID."""
    try:
        query = await query_model.find_by_id(query_id)
        if not query:
            return None
        return query_helper(query)
    except Exception:
        return None

async def get_all_queries() -> List[QueryOut]:
    """Get all queries."""
    queries = await query_model.find_all()
    return [query_helper(query) for query in queries]

async def update_query(query_id: str, query_update: QueryUpdate) -> Optional[QueryOut]:
    """Update a query."""
    try:
        # Check if query exists
        existing_query = await query_model.find_by_id(query_id)
        if not existing_query:
            return None
        
        # Check if new query conflicts with existing query
        if query_update.query:
            query_conflict = await query_model.check_query_conflict(
                query_update.query, query_id
            )
            if query_conflict:
                raise ValueError("Query already exists")
        
        # Prepare update data
        update_data = {}
        if query_update.query is not None:
            update_data["query"] = query_update.query
        if query_update.description is not None:
            update_data["description"] = query_update.description
        
        # Update the query
        updated_query = await query_model.update(query_id, update_data)
        return query_helper(updated_query)
    except Exception:
        return None

async def delete_query(query_id: str) -> bool:
    """Delete a query."""
    try:
        # Check if query exists
        query = await query_model.find_by_id(query_id)
        if not query:
            return False
        
        # Delete the query
        result = await query_model.delete(query_id)
        return True
    except Exception:
        return False

def query_helper(query) -> QueryOut:
    """Convert MongoDB document to QueryOut."""
    return QueryOut(
        id=str(query["_id"]),
        query=query["query"],
        description=query.get("description"),
        created_at=query.get("created_at", datetime.utcnow()),
        updated_at=query.get("updated_at", datetime.utcnow())
    )
