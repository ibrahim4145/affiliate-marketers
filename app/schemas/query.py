from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Query Schemas
class QueryBase(BaseModel):
    query: str
    description: Optional[str] = None

class QueryCreate(QueryBase):
    pass

class QueryUpdate(BaseModel):
    query: Optional[str] = None
    description: Optional[str] = None

class QueryOut(QueryBase):
    id: str
    created_at: datetime
    updated_at: datetime
