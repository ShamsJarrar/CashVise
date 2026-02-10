from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    country: str
    city: Optional[str] = None
    preferred_currency: str

class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    name: str
    country: str
    city: Optional[str] = None
    preferred_currency: str
    #TODO: check if need to add is_verified

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str