from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token response model with both access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiration in seconds

class TokenData(BaseModel):
    """Token payload data."""
    email: str | None = None
    role: str | None = None

class RefreshTokenRequest(BaseModel):
    """Request model for refresh token endpoint."""
    refresh_token: str

class RefreshTokenData(BaseModel):
    """Refresh token data stored in database."""
    user_email: str
    refresh_token: str
    expires_at: datetime
    is_active: bool = True
    created_at: datetime
    last_used: datetime | None = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str 