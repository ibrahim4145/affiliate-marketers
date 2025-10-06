from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Industry Schemas
class IndustryBase(BaseModel):
    industry_name: str
    description: Optional[str] = None

class IndustryCreate(IndustryBase):
    pass

class IndustryUpdate(BaseModel):
    industry_name: Optional[str] = None
    description: Optional[str] = None

class IndustryOut(IndustryBase):
    id: str
    created_at: datetime
    updated_at: datetime
