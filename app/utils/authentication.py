from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import TokenData
from app.models.user import user_model
from bson import ObjectId
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Truncate password to 72 bytes if necessary (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes, but be careful with UTF-8 encoding
            truncated_bytes = password_bytes[:72]
            # Find the last complete character boundary
            while truncated_bytes and truncated_bytes[-1] & 0x80 and not (truncated_bytes[-1] & 0x40):
                truncated_bytes = truncated_bytes[:-1]
            plain_password = truncated_bytes.decode('utf-8', errors='ignore')
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password."""
    try:
        # Ensure password is a string
        if not isinstance(password, str):
            password = str(password)
        
        # Truncate password to 72 bytes if necessary (bcrypt limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes, but be careful with UTF-8 encoding
            truncated_bytes = password_bytes[:72]
            # Find the last complete character boundary
            while truncated_bytes and truncated_bytes[-1] & 0x80 and not (truncated_bytes[-1] & 0x40):
                truncated_bytes = truncated_bytes[:-1]
            password = truncated_bytes.decode('utf-8', errors='ignore')
        
        # Hash the password
        hashed = pwd_context.hash(password)
        
        # Verify the hash works
        if not pwd_context.verify(password, hashed):
            raise Exception("Hash verification failed")
            
        return hashed
    except Exception as e:
        print(f"Password hashing error: {e}")
        print(f"Password type: {type(password)}")
        print(f"Password length: {len(password) if password else 'None'}")
        raise HTTPException(status_code=500, detail=f"Password hashing failed: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str):
    """Get user by email from database."""
    user = await user_model.find_by_email(email)
    return user

async def authenticate_user(email: str, password: str):
    """Authenticate a user with email and password."""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
