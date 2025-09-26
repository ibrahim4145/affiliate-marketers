from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Models
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Industry Models
class IndustryBase(BaseModel):
    industry_name: str
    description: Optional[str] = None

class IndustryCreate(IndustryBase):
    pass

class IndustryUpdate(BaseModel):
    industry_name: Optional[str] = None
    description: Optional[str] = None

class IndustryOut(IndustryBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Query Models
class QueryBase(BaseModel):
    query: str
    description: Optional[str] = None

class QueryCreate(QueryBase):
    pass

class QueryUpdate(BaseModel):
    query: Optional[str] = None
    description: Optional[str] = None

class QueryOut(QueryBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
