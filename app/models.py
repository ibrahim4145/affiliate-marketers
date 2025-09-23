# # backend/app/models.py
# from pydantic import BaseModel
# from typing import List, Optional, Dict

# class Contact(BaseModel):
#     domain: str
#     emails: List[str] = []
#     socials: Dict[str, List[str]] = {}
#     name: Optional[str] = None


from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str   # storing plain password only for testing (use hashing later)

class UserOut(UserBase):
    id: str
