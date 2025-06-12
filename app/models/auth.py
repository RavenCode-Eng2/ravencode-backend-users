from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .role import Role

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    role: Role = Role.STUDENT  # Default role is student

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[Role] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str 