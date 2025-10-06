from typing import Optional
from bson import ObjectId
from datetime import datetime
from app.models.user import user_model
from app.schemas.user import UserCreate, UserOut
from app.utils.authentication import get_password_hash

async def create_user(user: UserCreate) -> UserOut:
    """Create a new user."""
    # Check if user exists
    existing = await user_model.find_by_email(user.email)
    if existing:
        raise ValueError("Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    }
    
    created_user = await user_model.create(user_data)
    return user_helper(created_user)

async def get_user_by_id(user_id: str) -> Optional[UserOut]:
    """Get user by ID."""
    try:
        user = await user_model.find_by_id(user_id)
        if not user:
            return None
        return user_helper(user)
    except Exception:
        return None

async def get_user_by_email(email: str) -> Optional[UserOut]:
    """Get user by email."""
    user = await user_model.find_by_email(email)
    if not user:
        return None
    return user_helper(user)

def user_helper(user) -> UserOut:
    """Convert MongoDB document to UserOut."""
    return UserOut(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        created_at=user.get("created_at", datetime.utcnow()),
        updated_at=user.get("updated_at", datetime.utcnow())
    )
