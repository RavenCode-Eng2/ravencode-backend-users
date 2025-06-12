from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from app.models.student import Student
from app.services.student import StudentService
from app.core.guards import require_admin, require_student, require_any_authenticated
from app.models.role import Permission, require_permissions

router = APIRouter()

def get_student_service():
    """
    Dependency injector for the StudentService.
    Returns an instance of the service to interact with the database.
    """
    return StudentService()

@router.post(
    "/register/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED
)
async def create_student(
    student: Student, 
    student_service: StudentService = Depends(get_student_service)
):
    """
    Register a new student in the database.
    Public endpoint - no authentication required.
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
    "/obtener/{student_email}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_any_authenticated)]
)
async def get_student(
    student_email: str, 
    student_service: StudentService = Depends(get_student_service),
    current_user: User = Depends(require_any_authenticated)
):
    """
    Get a student by their email address.
    Requires authentication.
    Students can only view their own profile.
    Admins can view any profile.
    """
    try:
        # Check if user has permission to view this profile
        if current_user.role == Role.STUDENT and current_user.email != student_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )

        student = student_service.get_student_by_email(student_email)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/modificacion/{student_email}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_any_authenticated)]
)
async def update_student(
    student_email: str, 
    updated_student: Student, 
    student_service: StudentService = Depends(get_student_service),
    current_user: User = Depends(require_any_authenticated)
):
    """
    Update a student's information in the database.
    Students can only update their own profile.
    Admins can update any profile.
    """
    try:
        # Check if user has permission to update this profile
        if current_user.role == Role.STUDENT and current_user.email != student_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )

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
    "/eliminar/{student_email}",
    response_model=Dict[str, str],
    dependencies=[Depends(require_admin)]
)
async def delete_student(
    student_email: str, 
    student_service: StudentService = Depends(get_student_service)
):
    """
    Delete a student by their email address.
    Only admins can delete students.
    """
    try:
        student_service.delete_student_by_email(student_email)
        return {"message": "Student deleted successfully"}
    except Exception as e:
        if "Student not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/listar/",
    response_model=List[Dict[str, Any]],
    dependencies=[Depends(require_admin)]
)
async def list_students(
    student_service: StudentService = Depends(get_student_service)
):
    """
    List all students in the database.
    Only admins can list all students.
    """
    try:
        return student_service.list_students()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# You might want to add more endpoints like deleting a student, getting all students, etc.