from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Sub Query Schemas
class SubQueryBase(BaseModel):
    query_id: str = Field(..., description="ID of the parent query")
    sub_query: str = Field(..., description="Sub query text")
    added_by: str = Field(..., description="Name of the user who added this sub query")
    description: Optional[str] = Field(None, description="Optional description for the sub query")

class SubQueryCreate(SubQueryBase):
    pass

class SubQueryUpdate(BaseModel):
    query_id: Optional[str] = None
    sub_query: Optional[str] = None
    added_by: Optional[str] = None
    description: Optional[str] = None

class SubQueryResponse(SubQueryBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class SubQueryListResponse(BaseModel):
    sub_queries: List[SubQueryResponse]
    total: int
    skip: int
    limit: int

class SubQueryWithQueryInfo(SubQueryResponse):
    """Sub query with parent query information."""
    parent_query: Optional[dict] = None
