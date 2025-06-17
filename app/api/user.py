from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from app.services.auth import AuthService
from app.api.auth import get_auth_service, get_current_user

router = APIRouter()

@router.get("/me", response_model=Dict[str, Any])
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get the current user's details.
    """
    return current_user 