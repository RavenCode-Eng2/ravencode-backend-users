from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any

from app.models.student import Student
from app.services.student import StudentService

router = APIRouter()

def get_student_service():
    """
    Dependency injector for the StudentService.
    Returns an instance of the service to interact with the database.
    """
    return StudentService()

@router.post(
    "/students/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Student created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Student created successfully",
                        "student": {
                            "Nombre": "Jorge",
                            "Correo_electronico": "user@example.com",
                            "Contrasena": "string",
                            "Fecha_de_nacimiento": "2025-06-08",
                            "Foto_de_perfil": "string",
                            "Institucion_educativa": "string",
                            "Grado_academico": "string",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        }
                    }
                }
            }
        },
        400: {"description": "Student already exists or invalid data"}
    }
)
async def create_student(student: Student, student_service: StudentService = Depends(get_student_service)):
    """
    Create a new student in the database.
    - **student**: Student data to be created
    - **returns**: Confirmation message and the created student
    """
    try:
        created_student = student_service.create_student(student)
        return {
            "message": "Student created successfully",
            "student": created_student
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/students/{student_email}",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Student found",
            "content": {
                "application/json": {
                    "example": {
                        "Nombre": "Jorge",
                        "Correo_electronico": "user@example.com",
                        "Contrasena": "string",
                        "Fecha_de_nacimiento": "2025-06-08",
                        "Foto_de_perfil": "string",
                        "Institucion_educativa": "string",
                        "Grado_academico": "string",
                        "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                    }
                }
            }
        },
        404: {"description": "Student not found"}
    }
)
async def get_student(student_email: str, student_service: StudentService = Depends(get_student_service)):
    """
    Get a student by their email address.
    - **student_email**: Email of the student to retrieve
    - **returns**: Student data if found
    """
    try:
        student = student_service.get_student_by_email(student_email)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/students/{student_email}",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Student updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Student updated successfully",
                        "student": {
                            "Nombre": "Jorge",
                            "Correo_electronico": "user@example.com",
                            "Contrasena": "string",
                            "Fecha_de_nacimiento": "2025-06-08",
                            "Foto_de_perfil": "string",
                            "Institucion_educativa": "string",
                            "Grado_academico": "string",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        }
                    }
                }
            }
        },
        404: {"description": "Student not found"},
        400: {"description": "Invalid data or no changes made"}
    }
)
async def update_student(student_email: str, updated_student: Student, student_service: StudentService = Depends(get_student_service)):
    """
    Update a student's information in the database.
    - **student_email**: Email of the student to update
    - **updated_student**: New data for the student
    - **returns**: Confirmation message and the updated student
    """
    try:
        updated_student_data = student_service.update_student(student_email, updated_student)
        return {
            "message": "Student updated successfully",
            "student": updated_student_data
        }
    except Exception as e:
        if "Student not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/students/{student_email}",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Student deleted successfully", "content": {"application/json": {"example": {"message": "Student deleted successfully"}}}},
        404: {"description": "Student not found"}
    }
)
async def delete_student(student_email: str, student_service: StudentService = Depends(get_student_service)):
    """
    Delete a student by their email address.
    - **student_email**: Email of the student to delete
    - **returns**: Confirmation message
    """
    try:
        student_service.delete_student_by_email(student_email)
        return {"message": "Student deleted successfully"}
    except Exception as e:
        if "Student not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/students/",
    response_model=List[Dict[str, Any]],
    responses={
        200: {
            "description": "List of all students",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "Nombre": "Jorge",
                            "Correo_electronico": "user@example.com",
                            "Contrasena": "string",
                            "Fecha_de_nacimiento": "2025-06-08",
                            "Foto_de_perfil": "string",
                            "Institucion_educativa": "string",
                            "Grado_academico": "string",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        }
                    ]
                }
            }
        }
    }
)
async def list_students(student_service: StudentService = Depends(get_student_service)):
    """
    List all students in the database.
    - **returns**: List of all students
    """
    try:
        return student_service.list_students()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# You might want to add more endpoints like deleting a student, getting all students, etc.