# Categories router with CRUD endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse,
    BulkCategoryCreate, BulkCategoryResponse
)
from app.crud.category import (
    create_category, get_categories, get_category_by_id, update_category,
    delete_category, create_categories_bulk, search_categories
)
from app.dependencies import get_database
from typing import Optional

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryResponse)
async def create_category_endpoint(
    category: CategoryCreate,
    db=Depends(get_database)
):
    """Create a new category."""
    try:
        return await create_category(category)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=CategoryListResponse)
async def get_categories_endpoint(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    search: Optional[str] = Query(None, description="Search term for category name or description"),
    db=Depends(get_database)
):
    """Get all categories with optional search and pagination."""
    try:
        if search:
            result = await search_categories(search, skip, limit)
            return CategoryListResponse(
                categories=result["categories"],
                total=result["total"],
                skip=result["skip"],
                limit=result["limit"]
            )
        else:
            result = await get_categories(skip, limit)
            return CategoryListResponse(
                categories=result["categories"],
                total=result["total"],
                skip=result["skip"],
                limit=result["limit"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_endpoint(
    category_id: str,
    db=Depends(get_database)
):
    """Get a specific category by ID."""
    try:
        return await get_category_by_id(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category_endpoint(
    category_id: str,
    category: CategoryUpdate,
    db=Depends(get_database)
):
    """Update a category."""
    try:
        return await update_category(category_id, category)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{category_id}")
async def delete_category_endpoint(
    category_id: str,
    db=Depends(get_database)
):
    """Delete a category."""
    try:
        success = await delete_category(category_id)
        if success:
            return {"message": "Category deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete category")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk", response_model=BulkCategoryResponse)
async def create_categories_bulk_endpoint(
    bulk_data: BulkCategoryCreate,
    db=Depends(get_database)
):
    """Create multiple categories in bulk."""
    try:
        return await create_categories_bulk(bulk_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/{search_term}")
async def search_categories_endpoint(
    search_term: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db=Depends(get_database)
):
    """Search categories by name or description."""
    try:
        return await search_categories(search_term, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
