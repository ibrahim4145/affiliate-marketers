# Category CRUD operations
from app.models.category import category_model
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, BulkCategoryCreate, BulkCategoryResponse
from typing import List, Dict, Any
from bson import ObjectId

def category_helper(category) -> dict:
    """Helper function to format category data."""
    return {
        "id": str(category["_id"]),
        "category_name": category["category_name"],
        "description": category.get("description"),
        "created_at": category.get("created_at"),
        "updated_at": category.get("updated_at")
    }

async def create_category(category_data: CategoryCreate) -> CategoryResponse:
    """Create a new category."""
    try:
        # Check for name conflict
        existing_category = await category_model.check_name_conflict(category_data.category_name)
        if existing_category:
            raise ValueError(f"Category with name '{category_data.category_name}' already exists")
        
        category_doc = category_data.dict()
        created_category = await category_model.create(category_doc)
        return CategoryResponse(**category_helper(created_category))
    except Exception as e:
        raise Exception(f"Failed to create category: {str(e)}")

async def get_categories(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get all categories with pagination."""
    try:
        categories = await category_model.find_all(skip, limit)
        total = await category_model.count_all()
        
        return {
            "categories": [category_helper(cat) for cat in categories],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise Exception(f"Failed to retrieve categories: {str(e)}")

async def get_category_by_id(category_id: str) -> CategoryResponse:
    """Get a specific category by ID."""
    try:
        category = await category_model.find_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        return CategoryResponse(**category_helper(category))
    except Exception as e:
        raise Exception(f"Failed to retrieve category: {str(e)}")

async def update_category(category_id: str, update_data: CategoryUpdate) -> CategoryResponse:
    """Update a category."""
    try:
        # Check if category exists
        existing_category = await category_model.find_by_id(category_id)
        if not existing_category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        # Check for name conflict if name is being updated
        if update_data.category_name:
            conflict = await category_model.check_name_conflict(update_data.category_name, category_id)
            if conflict:
                raise ValueError(f"Category with name '{update_data.category_name}' already exists")
        
        # Prepare update data
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            raise ValueError("No valid fields to update")
        
        updated_category = await category_model.update(category_id, update_dict)
        return CategoryResponse(**category_helper(updated_category))
    except Exception as e:
        raise Exception(f"Failed to update category: {str(e)}")

async def delete_category(category_id: str) -> bool:
    """Delete a category."""
    try:
        # Check if category exists
        existing_category = await category_model.find_by_id(category_id)
        if not existing_category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        result = await category_model.delete(category_id)
        return result.deleted_count > 0
    except Exception as e:
        raise Exception(f"Failed to delete category: {str(e)}")

async def create_categories_bulk(bulk_data: BulkCategoryCreate) -> BulkCategoryResponse:
    """Create multiple categories in bulk."""
    try:
        created_ids = []
        
        for category_data in bulk_data.categories:
            # Check for name conflict
            existing_category = await category_model.check_name_conflict(category_data.category_name)
            if existing_category:
                raise ValueError(f"Category with name '{category_data.category_name}' already exists")
            
            category_doc = category_data.dict()
            created_category = await category_model.create(category_doc)
            created_ids.append(str(created_category["_id"]))
        
        return BulkCategoryResponse(
            created_ids=created_ids,
            message=f"Successfully created {len(created_ids)} categories"
        )
    except Exception as e:
        raise Exception(f"Failed to create categories: {str(e)}")

async def search_categories(search_term: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Search categories by name or description."""
    try:
        # Build search query
        search_query = {
            "$or": [
                {"category_name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        # Get categories matching search
        cursor = category_model.collection.find(search_query).skip(skip).limit(limit).sort("created_at", -1)
        categories = await cursor.to_list(length=limit)
        
        # Count total matching categories
        total = await category_model.collection.count_documents(search_query)
        
        return {
            "categories": [category_helper(cat) for cat in categories],
            "total": total,
            "skip": skip,
            "limit": limit,
            "search_term": search_term
        }
    except Exception as e:
        raise Exception(f"Failed to search categories: {str(e)}")
