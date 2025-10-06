from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from app.schemas.user import UserCreate, UserOut, UserLogin, Token
from app.crud.user import create_user, get_user_by_id
from app.utils.authentication import get_password_hash, verify_password, create_access_token, get_current_user, authenticate_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate):
    """Register a new user."""
    try:
        # Validate password
        if not user.password or len(user.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Create user using CRUD
        created_user = await create_user(user)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Login user and return access token."""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user.get("created_at"),
        updated_at=current_user.get("updated_at")
    )

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user by ID (admin only for now)."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
