from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import UserCreate, UserOut
from bson import ObjectId

router = APIRouter(prefix="/users", tags=["Users"])

# Helper: Convert MongoDB document to dict
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"]
    }

@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate):
    # check if user exists
    existing = await db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = user.dict()
    result = await db["users"].insert_one(new_user)
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    return user_helper(created_user)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_helper(user)
