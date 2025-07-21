from typing import Optional, List, Dict, Any
from pymongo.results import InsertOneResult, UpdateResult
from app.models.user import Admin, UserRole
from app.services.user import UserService
from app.DB.database import get_database

class AdminService(UserService):
    """
    Service layer for managing admin operations in the database.
    Inherits from UserService for common user operations.
    """
    def __init__(self):
        """
        Initialize the admin service with the users collection.
        """
        super().__init__()

    def create_admin(self, admin_data: Admin) -> dict:
        """
        Create a new admin in the database.
        Returns the inserted admin document (with _id as string).
        Raises:
            Exception: If the admin already exists.
        """
        return self.create_user(admin_data)

    def get_admin_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieve an admin by their email address.
        Returns None if no admin is found.
        """
        user = self.get_user_by_email(email)
        if user and user.get("role") == UserRole.ADMIN.value:
            return user
        return None

    def update_admin(self, email: str, update_data: dict) -> UpdateResult:
        """
        Update an admin's information by their email.
        Returns the MongoDB update result.
        """
        # Verify the user is an admin before updating
        admin = self.get_admin_by_email(email)
        if not admin:
            raise Exception("Admin not found")
        return self.update_user(email, update_data)

    def delete_admin_by_email(self, email: str) -> bool:
        """
        Delete an admin by their email address.
        Returns True if successful, False if admin not found.
        """
        # Verify the user is an admin before deleting
        admin = self.get_admin_by_email(email)
        if not admin:
            return False
        return self.delete_user_by_email(email)

    def list_admins(self) -> List[dict]:
        """
        List all admins in the database.
        Returns a list of admin documents.
        """
        return self.list_users(role=UserRole.ADMIN) 