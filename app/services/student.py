from typing import Optional, List
from pymongo.results import InsertOneResult, UpdateResult
from app.models.student import Student
from app.DB.database import get_database
import datetime

class StudentService:
    """
    Service layer for managing student operations in the database.
    Handles all business logic and database interactions for students.
    """
    def __init__(self):
        """
        Initialize the student service with a database connection.
        Raises an exception if the connection fails.
        """
        self.db = get_database()
        if self.db is None:
            raise Exception("Could not connect to the database")
        self.collection = self.db["students"]

    def create_student(self, student_data: Student) -> dict:
        """
        Create a new student in the database.
        - Checks if a student with the same email already exists.
        - Converts Fecha_de_nacimiento to ISO string for MongoDB compatibility.
        - Returns the inserted student document (with _id as string).
        Raises:
            Exception: If the student already exists.
        """
        # Check for existing student by email
        existing_student = self.get_student_by_email(student_data.Correo_electronico)
        if existing_student:
            raise Exception("Student with this email already exists")
        
        student_dict = student_data.model_dump()
        # Convert Fecha_de_nacimiento to ISO string for MongoDB
        if isinstance(student_dict["Fecha_de_nacimiento"], datetime.date):
            student_dict["Fecha_de_nacimiento"] = student_dict["Fecha_de_nacimiento"].isoformat()
        result = self.collection.insert_one(student_dict)
        student_dict["_id"] = str(result.inserted_id)
        return student_dict

    def get_student_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieve a student from the database by their email address.
        Returns the student document as a dict, or None if not found.
        """
        student_data = self.collection.find_one({"Correo_electronico": email})
        if student_data:
            student_data["_id"] = str(student_data["_id"])
        return student_data

    def update_student(self, email: str, student_data: Student) -> dict:
        """
        Update an existing student's information in the database.
        - Checks if the student exists.
        - Updates only the provided fields.
        - Returns the updated student document.
        Raises:
            Exception: If the student does not exist or no changes were made.
        """
        # Check if the student exists
        existing_student = self.get_student_by_email(email)
        if not existing_student:
            raise Exception("Student not found")
        
        update_data = student_data.model_dump(exclude_unset=True)
        # Convert Fecha_de_nacimiento to ISO string if present
        if "Fecha_de_nacimiento" in update_data and isinstance(update_data["Fecha_de_nacimiento"], datetime.date):
            update_data["Fecha_de_nacimiento"] = update_data["Fecha_de_nacimiento"].isoformat()
        result = self.collection.update_one(
            {"Correo_electronico": email},
            {"$set": update_data}
        )
        if result.modified_count == 0:
            raise Exception("No changes were made")
        return self.get_student_by_email(email)

    def delete_student_by_email(self, email: str) -> bool:
        """
        Delete a student from the database by their email address.
        - Checks if the student exists before attempting deletion.
        - Returns True if the student was deleted, False otherwise.
        Raises:
            Exception: If the student does not exist.
        """
        # Check if the student exists
        existing_student = self.get_student_by_email(email)
        if not existing_student:
            raise Exception("Student not found")
        result = self.collection.delete_one({"Correo_electronico": email})
        return result.deleted_count > 0

    def list_students(self) -> List[dict]:
        """
        List all students in the database.
        Returns a list of student documents (with _id as string).
        """
        students = list(self.collection.find())
        return [{**student, "_id": str(student["_id"])} for student in students]

if __name__ == '__main__':
    # Example usage (replace with your MongoDB connection details and data)
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "student_db"
    collection_name = "students"

    student_service = StudentService()

    # Example of creating a student
    # new_student = StudentCreate(
    #     nombre="Juan Perez",
    #     correo_electronico="juan.perez@example.com",
    #     contrasena="securepassword123",
    #     fecha_de_nacimiento="2000-01-01",
    #     institucion_educativa="Universidad Nacional",
    #     grado_academico="Grado"
    # )
    # create_result = student_service.create_student(new_student)
    # print(f"Created student with ID: {create_result.inserted_id}")

    # Example of getting a student
    # retrieved_student = student_service.get_student_by_email("juan.perez@example.com")
    # if retrieved_student:
    #     print(f"Retrieved student: {retrieved_student.nombre}")
    # else:
    #     print("Student not found.")

    # Example of updating a student
    # update_result = student_service.update_student("juan.perez@example.com", {"institucion_educativa": "Otra Universidad"})
    # print(f"Matched count: {update_result.matched_count}, Modified count: {update_result.modified_count}")

    # Example of deleting a student
    # delete_result = student_service.delete_student_by_email("juan.perez@example.com")
    # print(f"Deleted student: {delete_result}")

    # Example of listing all students
    # all_students = student_service.list_students()
    # for student in all_students:
    #     print(f"Student: {student.nombre}")