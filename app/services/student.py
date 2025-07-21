from typing import Optional, List, Dict, Any
from pymongo.results import InsertOneResult, UpdateResult
from app.models.user import Student, UserRole
from app.services.user import UserService
from app.DB.database import get_database
import datetime

class StudentService(UserService):
    """
    Service layer for managing student operations in the database.
    Inherits from UserService for common user operations.
    """
    def __init__(self):
        """
        Initialize the student service with the users collection.
        """
        super().__init__()

    def create_student(self, student_data: Student) -> dict:
        """
        Create a new student in the database.
        - Checks if a student with the same email already exists.
        - Converts fecha_de_nacimiento to ISO string for MongoDB compatibility.
        - Returns the inserted student document (with _id as string).
        Raises:
            Exception: If the student already exists.
        """
        # Convert fecha_de_nacimiento to ISO string for MongoDB
        student_dict = student_data.model_dump()
        if isinstance(student_dict["fecha_de_nacimiento"], datetime.date):
            student_dict["fecha_de_nacimiento"] = student_dict["fecha_de_nacimiento"].isoformat()
        
        # Use UserService.create_user directly with the converted dict
        # Check for existing user by email
        existing_user = self.get_user_by_email(student_data.correo_electronico)
        if existing_user:
            raise Exception("User with this email already exists")
        
        result = self.collection.insert_one(student_dict)
        student_dict["_id"] = str(result.inserted_id)
        return student_dict

    def get_student_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieve a student by their email address.
        Returns None if no student is found.
        """
        print(f"DEBUG: StudentService - Looking up user with email: {email}")
        user = self.get_user_by_email(email)
        print(f"DEBUG: StudentService - User lookup result: {user}")
        
        if user and user.get("role") == UserRole.STUDENT.value:
            print("DEBUG: StudentService - Found student with matching role")
            return user
            
        print(f"DEBUG: StudentService - No student found or role mismatch. User role: {user.get('role') if user else None}")
        return None

    def update_student(self, email: str, update_data: dict) -> UpdateResult:
        """
        Update a student's information by their email.
        Returns the MongoDB update result.
        """
        # Verify the user is a student before updating
        student = self.get_student_by_email(email)
        if not student:
            raise Exception("Student not found")
        return self.update_user(email, update_data)

    def delete_student_by_email(self, email: str) -> bool:
        """
        Delete a student by their email address.
        Returns True if successful, False if student not found.
        """
        # Verify the user is a student before deleting
        student = self.get_student_by_email(email)
        if not student:
            return False
        return self.delete_user_by_email(email)

    def list_students(self) -> List[dict]:
        """
        List all students in the database.
        Returns a list of student documents.
        """
        return self.list_users(role=UserRole.STUDENT)