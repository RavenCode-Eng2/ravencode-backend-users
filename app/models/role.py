from enum import Enum
from typing import List

class Role(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"

class Permission(str, Enum):
    # Student permissions
    VIEW_OWN_PROFILE = "view_own_profile"
    UPDATE_OWN_PROFILE = "update_own_profile"
    
    # Admin permissions
    VIEW_ALL_STUDENTS = "view_all_students"
    MANAGE_STUDENTS = "manage_students"
    MANAGE_ADMINS = "manage_admins"

# Define role-permission mappings
ROLE_PERMISSIONS = {
    Role.STUDENT: [
        Permission.VIEW_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
    ],
    Role.ADMIN: [
        Permission.VIEW_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
        Permission.VIEW_ALL_STUDENTS,
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_ADMINS,
    ]
} 