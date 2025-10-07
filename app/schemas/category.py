# Category schemas for validation and serialization
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    category_name: str = Field(..., description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")

class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass

class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    category_name: Optional[str] = Field(None, description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")

class CategoryResponse(CategoryBase):
    """Schema for category response."""
    id: str = Field(..., description="Category ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class CategoryListResponse(BaseModel):
    """Schema for category list response."""
    categories: list[CategoryResponse] = Field(..., description="List of categories")
    total: int = Field(..., description="Total number of categories")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")

class BulkCategoryCreate(BaseModel):
    """Schema for creating multiple categories."""
    categories: list[CategoryCreate] = Field(..., description="List of categories to create")

class BulkCategoryResponse(BaseModel):
    """Schema for bulk category creation response."""
    created_ids: list[str] = Field(..., description="IDs of created categories")
    message: str = Field(..., description="Response message")
