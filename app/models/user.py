from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum

class UserRole(str, Enum):
    """
    Enum for user roles in the system.
    """
    ADMIN = "admin"
    STUDENT = "student"

class User(BaseModel):
    """
    Base Pydantic model representing a user entity.
    Used for data validation and serialization in API requests and responses.
    
    Attributes:
        nombre (str): Full name of the user.
        correo_electronico (EmailStr): Email address of the user.
        contrasena (str): Password for the user account.
        foto_de_perfil (Optional[str]): URL to the user's profile picture (optional).
        fecha_de_nacimiento (date): Date of birth of the user.
        created_at (datetime): Timestamp when the user was created.
        role (UserRole): Role of the user in the system.
    """
    nombre: str = Field(..., description="Full name of the user")
    correo_electronico: EmailStr = Field(..., description="Email address of the user")
    contrasena: str = Field(..., description="Password for the user account")
    foto_de_perfil: Optional[str] = Field(None, description="URL to the user's profile picture (optional)")
    fecha_de_nacimiento: date = Field(..., description="Date of birth of the user")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the user was created")
    role: UserRole = Field(..., description="Role of the user in the system")

class Student(User):
    """
    Pydantic model representing a student entity, inheriting from User.
    Adds student-specific fields to the base user model.
    
    Additional Attributes:
        institucion_educativa (str): Educational institution the student attends.
        grado_academico (str): Academic grade the student is currently in.
    """
    institucion_educativa: str = Field(..., description="Educational institution the student attends")
    grado_academico: str = Field(..., description="Academic grade the student is currently in")
    role: Literal[UserRole.STUDENT] = Field(default=UserRole.STUDENT, description="Role is always student for this model")

class Admin(User):
    """
    Pydantic model representing an admin entity, inheriting from User.
    Adds admin-specific fields to the base user model.
    
    Additional Attributes:
        departamento (str): Department or area the admin manages.
        nivel_acceso (str): Access level of the admin.
    """
    departamento: str = Field(..., description="Department or area the admin manages")
    nivel_acceso: str = Field(..., description="Access level of the admin")
    role: Literal[UserRole.ADMIN] = Field(default=UserRole.ADMIN, description="Role is always admin for this model")

# Update models for partial updates
class UserUpdate(BaseModel):
    """
    Pydantic model for updating user information.
    All fields are optional to allow partial updates.
    Note: created_at is typically not updated by users.
    """
    nombre: Optional[str] = Field(None, description="Full name of the user")
    correo_electronico: Optional[EmailStr] = Field(None, description="Email address of the user")
    contrasena: Optional[str] = Field(None, description="Password for the user account")
    foto_de_perfil: Optional[str] = Field(None, description="URL to the user's profile picture")
    fecha_de_nacimiento: Optional[date] = Field(None, description="Date of birth of the user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Juan Carlos Pérez",
                "correo_electronico": "juan.perez@universidad.edu",
                "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                "fecha_de_nacimiento": "1990-05-15"
            }
        }
    }

class StudentUpdate(UserUpdate):
    """
    Pydantic model for updating student information.
    Extends UserUpdate with student-specific fields.
    """
    institucion_educativa: Optional[str] = Field(None, description="Educational institution the student attends")
    grado_academico: Optional[str] = Field(None, description="Academic grade the student is currently in")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "María González López",
                "correo_electronico": "maria.gonzalez@universidad.edu",
                "fecha_de_nacimiento": "1999-03-22",
                "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                "institucion_educativa": "Universidad Tecnológica Nacional",
                "grado_academico": "Ingeniería en Sistemas"
            }
        }
    }

class AdminUpdate(UserUpdate):
    """
    Pydantic model for updating admin information.
    Extends UserUpdate with admin-specific fields.
    """
    departamento: Optional[str] = Field(None, description="Department or area the admin manages")
    nivel_acceso: Optional[str] = Field(None, description="Access level of the admin")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Carlos Administrador",
                "correo_electronico": "carlos.admin@empresa.com",
                "foto_de_perfil": "https://ejemplo.com/admin.jpg",
                "departamento": "Tecnología",
                "nivel_acceso": "Super Admin",
                "fecha_de_nacimiento": "1980-05-15"
            }
        }
    }