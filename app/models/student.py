from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class Student(BaseModel):
    """
    Pydantic model representing a student entity.
    Used for data validation and serialization in API requests and responses.
    
    Attributes:
        Nombre (str): Full name of the student.
        Correo_electronico (EmailStr): Email address of the student.
        Contrasena (str): Password for the student account.
        Fecha_de_nacimiento (date): Date of birth of the student.
        Foto_de_perfil (Optional[str]): URL to the student's profile picture (optional).
        Institucion_educativa (str): Educational institution the student attends.
        Grado_academico (str): Academic grade the student is currently in.
    """
    Nombre: str = Field(..., description="Full name of the student")
    Correo_electronico: EmailStr = Field(..., description="Email address of the student")
    Contrasena: str = Field(..., description="Password for the student account")
    Fecha_de_nacimiento: date = Field(..., description="Date of birth of the student")
    Foto_de_perfil: Optional[str] = Field(None, description="URL to the student's profile picture (optional)")
    Institucion_educativa: str = Field(..., description="Educational institution the student attends")
    Grado_academico: str = Field(..., description="Academic grade the student is currently in")