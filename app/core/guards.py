from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from ..models.role import Role, Permission, ROLE_PERMISSIONS
from ..services.auth import get_current_user
from ..models.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def require_roles(required_roles: List[Role]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: List[Permission]):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if not all(permission in user_permissions for permission in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker

# Common role combinations
require_admin = require_roles([Role.ADMIN])
require_student = require_roles([Role.STUDENT])
require_any_authenticated = require_roles([Role.ADMIN, Role.STUDENT]) 