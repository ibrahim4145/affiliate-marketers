# Niche CRUD operations
from app.models.niche import niche_model
from app.models.category import category_model
from app.schemas.niche import NicheCreate, NicheUpdate, NicheResponse, BulkNicheCreate, BulkNicheResponse, NicheWithCategory
from typing import List, Dict, Any
from bson import ObjectId

def niche_helper(niche) -> dict:
    """Helper function to format niche data."""
    return {
        "id": str(niche["_id"]),
        "niche_name": niche["niche_name"],
        "description": niche.get("description"),
        "category_id": str(niche.get("category_id", "")),
        "created_at": niche.get("created_at"),
        "updated_at": niche.get("updated_at")
    }

def niche_with_category_helper(niche, category=None) -> dict:
    """Helper function to format niche data with category information."""
    result = niche_helper(niche)
    if category:
        result["category"] = {
            "id": str(category["_id"]),
            "category_name": category["category_name"],
            "description": category.get("description")
        }
    return result

async def create_niche(niche_data: NicheCreate) -> NicheResponse:
    """Create a new niche."""
    try:
        # Validate category exists
        category = await category_model.find_by_id(niche_data.category_id)
        if not category:
            raise ValueError(f"Category with ID '{niche_data.category_id}' not found")
        
        # Check for name conflict
        existing_niche = await niche_model.check_name_conflict(niche_data.niche_name)
        if existing_niche:
            raise ValueError(f"Niche with name '{niche_data.niche_name}' already exists")
        
        niche_doc = niche_data.dict()
        niche_doc["category_id"] = ObjectId(niche_data.category_id)
        created_niche = await niche_model.create(niche_doc)
        return NicheResponse(**niche_helper(created_niche))
    except Exception as e:
        raise Exception(f"Failed to create niche: {str(e)}")

async def get_niches(skip: int = 0, limit: int = 100, category_id: str = None) -> Dict[str, Any]:
    """Get all niches with pagination and optional category filter."""
    try:
        if category_id:
            niches = await niche_model.find_by_category(category_id)
            total = len(niches)
        else:
            niches = await niche_model.find_all(skip, limit)
            total = await niche_model.count_all()
        
        return {
            "niches": [niche_helper(niche) for niche in niches],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise Exception(f"Failed to retrieve niches: {str(e)}")

async def get_niche_by_id(niche_id: str, include_category: bool = False) -> NicheResponse:
    """Get a specific niche by ID."""
    try:
        niche = await niche_model.find_by_id(niche_id)
        if not niche:
            raise ValueError(f"Niche with ID '{niche_id}' not found")
        
        if include_category:
            category = await category_model.find_by_id(str(niche.get("category_id", "")))
            return NicheWithCategory(**niche_with_category_helper(niche, category))
        else:
            return NicheResponse(**niche_helper(niche))
    except Exception as e:
        raise Exception(f"Failed to retrieve niche: {str(e)}")

async def update_niche(niche_id: str, update_data: NicheUpdate) -> NicheResponse:
    """Update a niche."""
    try:
        # Check if niche exists
        existing_niche = await niche_model.find_by_id(niche_id)
        if not existing_niche:
            raise ValueError(f"Niche with ID '{niche_id}' not found")
        
        # Validate category if being updated
        if update_data.category_id:
            category = await category_model.find_by_id(update_data.category_id)
            if not category:
                raise ValueError(f"Category with ID '{update_data.category_id}' not found")
        
        # Check for name conflict if name is being updated
        if update_data.niche_name:
            conflict = await niche_model.check_name_conflict(update_data.niche_name, niche_id)
            if conflict:
                raise ValueError(f"Niche with name '{update_data.niche_name}' already exists")
        
        # Prepare update data
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            raise ValueError("No valid fields to update")
        
        # Convert category_id to ObjectId if provided
        if "category_id" in update_dict:
            update_dict["category_id"] = ObjectId(update_dict["category_id"])
        
        updated_niche = await niche_model.update(niche_id, update_dict)
        return NicheResponse(**niche_helper(updated_niche))
    except Exception as e:
        raise Exception(f"Failed to update niche: {str(e)}")

async def delete_niche(niche_id: str) -> bool:
    """Delete a niche."""
    try:
        # Check if niche exists
        existing_niche = await niche_model.find_by_id(niche_id)
        if not existing_niche:
            raise ValueError(f"Niche with ID '{niche_id}' not found")
        
        result = await niche_model.delete(niche_id)
        return result.deleted_count > 0
    except Exception as e:
        raise Exception(f"Failed to delete niche: {str(e)}")

async def create_niches_bulk(bulk_data: BulkNicheCreate) -> BulkNicheResponse:
    """Create multiple niches in bulk."""
    try:
        created_ids = []
        
        for niche_data in bulk_data.niches:
            # Validate category exists
            category = await category_model.find_by_id(niche_data.category_id)
            if not category:
                raise ValueError(f"Category with ID '{niche_data.category_id}' not found")
            
            # Check for name conflict
            existing_niche = await niche_model.check_name_conflict(niche_data.niche_name)
            if existing_niche:
                raise ValueError(f"Niche with name '{niche_data.niche_name}' already exists")
            
            niche_doc = niche_data.dict()
            niche_doc["category_id"] = ObjectId(niche_data.category_id)
            created_niche = await niche_model.create(niche_doc)
            created_ids.append(str(created_niche["_id"]))
        
        return BulkNicheResponse(
            created_ids=created_ids,
            message=f"Successfully created {len(created_ids)} niches"
        )
    except Exception as e:
        raise Exception(f"Failed to create niches: {str(e)}")

async def search_niches(search_term: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Search niches by name or description."""
    try:
        niches = await niche_model.search_niches(search_term, skip, limit)
        total = len(niches)
        
        return {
            "niches": [niche_helper(niche) for niche in niches],
            "total": total,
            "skip": skip,
            "limit": limit,
            "search_term": search_term
        }
    except Exception as e:
        raise Exception(f"Failed to search niches: {str(e)}")

async def get_niches_by_category(category_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get niches by category ID."""
    try:
        # Validate category exists
        category = await category_model.find_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        niches = await niche_model.find_by_category(category_id)
        total = len(niches)
        
        # Apply pagination
        paginated_niches = niches[skip:skip + limit]
        
        return {
            "niches": [niche_helper(niche) for niche in paginated_niches],
            "total": total,
            "skip": skip,
            "limit": limit,
            "category_id": category_id
        }
    except Exception as e:
        raise Exception(f"Failed to retrieve niches by category: {str(e)}")
