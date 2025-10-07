# Niches router with CRUD endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from app.schemas.niche import (
    NicheCreate, NicheUpdate, NicheResponse, NicheListResponse,
    BulkNicheCreate, BulkNicheResponse, NicheWithCategory
)
from app.crud.niche import (
    create_niche, get_niches, get_niche_by_id, update_niche,
    delete_niche, create_niches_bulk, search_niches, get_niches_by_category
)
from app.dependencies import get_database
from typing import Optional

router = APIRouter(prefix="/niches", tags=["Niches"])

@router.post("/", response_model=NicheResponse)
async def create_niche_endpoint(
    niche: NicheCreate,
    db=Depends(get_database)
):
    """Create a new niche."""
    try:
        return await create_niche(niche)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=NicheListResponse)
async def get_niches_endpoint(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search term for niche name or description"),
    db=Depends(get_database)
):
    """Get all niches with optional search, pagination, and category filter."""
    try:
        if search:
            result = await search_niches(search, skip, limit)
            return NicheListResponse(
                niches=result["niches"],
                total=result["total"],
                skip=result["skip"],
                limit=result["limit"]
            )
        elif category_id:
            result = await get_niches_by_category(category_id, skip, limit)
            return NicheListResponse(
                niches=result["niches"],
                total=result["total"],
                skip=result["skip"],
                limit=result["limit"]
            )
        else:
            result = await get_niches(skip, limit)
            return NicheListResponse(
                niches=result["niches"],
                total=result["total"],
                skip=result["skip"],
                limit=result["limit"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{niche_id}", response_model=NicheWithCategory)
async def get_niche_endpoint(
    niche_id: str,
    include_category: bool = Query(True, description="Include category information"),
    db=Depends(get_database)
):
    """Get a specific niche by ID."""
    try:
        return await get_niche_by_id(niche_id, include_category)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{niche_id}", response_model=NicheResponse)
async def update_niche_endpoint(
    niche_id: str,
    niche: NicheUpdate,
    db=Depends(get_database)
):
    """Update a niche."""
    try:
        return await update_niche(niche_id, niche)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{niche_id}")
async def delete_niche_endpoint(
    niche_id: str,
    db=Depends(get_database)
):
    """Delete a niche."""
    try:
        success = await delete_niche(niche_id)
        if success:
            return {"message": "Niche deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete niche")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk", response_model=BulkNicheResponse)
async def create_niches_bulk_endpoint(
    bulk_data: BulkNicheCreate,
    db=Depends(get_database)
):
    """Create multiple niches in bulk."""
    try:
        return await create_niches_bulk(bulk_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/{search_term}")
async def search_niches_endpoint(
    search_term: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db=Depends(get_database)
):
    """Search niches by name or description."""
    try:
        return await search_niches(search_term, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category_id}")
async def get_niches_by_category_endpoint(
    category_id: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db=Depends(get_database)
):
    """Get niches by category ID."""
    try:
        return await get_niches_by_category(category_id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
