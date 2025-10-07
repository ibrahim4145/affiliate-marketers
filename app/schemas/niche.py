# Niche schemas for validation and serialization
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NicheBase(BaseModel):
    """Base niche schema with common fields."""
    niche_name: str = Field(..., description="Name of the niche")
    description: Optional[str] = Field(None, description="Description of the niche")
    category_id: str = Field(..., description="ID of the associated category")

class NicheCreate(NicheBase):
    """Schema for creating a new niche."""
    pass

class NicheUpdate(BaseModel):
    """Schema for updating a niche."""
    niche_name: Optional[str] = Field(None, description="Name of the niche")
    description: Optional[str] = Field(None, description="Description of the niche")
    category_id: Optional[str] = Field(None, description="ID of the associated category")

class NicheResponse(NicheBase):
    """Schema for niche response."""
    id: str = Field(..., description="Niche ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class NicheListResponse(BaseModel):
    """Schema for niche list response."""
    niches: list[NicheResponse] = Field(..., description="List of niches")
    total: int = Field(..., description="Total number of niches")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")

class BulkNicheCreate(BaseModel):
    """Schema for creating multiple niches."""
    niches: list[NicheCreate] = Field(..., description="List of niches to create")

class BulkNicheResponse(BaseModel):
    """Schema for bulk niche creation response."""
    created_ids: list[str] = Field(..., description="IDs of created niches")
    message: str = Field(..., description="Response message")

class NicheWithCategory(NicheResponse):
    """Schema for niche response with category information."""
    category: Optional[dict] = Field(None, description="Category information")
