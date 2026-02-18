from pydantic import BaseModel, EmailStr
from typing import Optional
from .token import TokenResponse

# auth schemas
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

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenWithUserResponse(TokenResponse):
    user: UserResponse

# settings schemas
class UserUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    preferred_currency: Optional[str] = None

class UserEmailChange(BaseModel):
    new_email: EmailStr
    current_password: str

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str
