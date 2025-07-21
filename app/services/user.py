from typing import Optional, List, Dict, Any
from pymongo.results import InsertOneResult, UpdateResult
from app.models.user import User, UserRole
from app.DB.database import get_database
import datetime

class UserService:
    """
    Base service layer for managing user operations in the database.
    Handles all common user operations for both students and admins.
    """
    def __init__(self):
        """
        Initialize the user service with a database connection.
        Raises an exception if the connection fails.
        """
        self.db = get_database()
        if self.db is None:
            raise Exception("Could not connect to the database")
        self.collection = self.db["users"]  # All users stored in the same collection

    def create_user(self, user_data: User) -> dict:
        """
        Create a new user in the database.
        - Checks if a user with the same email already exists.
        - Returns the inserted user document (with _id as string).
        Raises:
            Exception: If the user already exists.
        """
        # Check for existing user by email
        existing_user = self.get_user_by_email(user_data.correo_electronico)
        if existing_user:
            raise Exception("User with this email already exists")
        
        user_dict = user_data.model_dump()
        result = self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return user_dict

    def _convert_mongo_doc(self, doc: Optional[dict]) -> Optional[dict]:
        """
        Convert MongoDB document to a serializable dictionary.
        Converts ObjectId to string and handles other MongoDB-specific types.
        Adds default created_at if missing for backward compatibility.
        """
        if doc is None:
            return None
            
        # Convert _id from ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        # Add default created_at if missing (for backward compatibility)
        if "created_at" not in doc:
            doc["created_at"] = datetime.utcnow()
            
        return doc

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieve a user by their email address.
        Returns None if no user is found.
        """
        print(f"DEBUG: UserService - Querying MongoDB for email: {email}")
        result = self.collection.find_one({"correo_electronico": email})
        print(f"DEBUG: UserService - MongoDB query result: {result}")
        return self._convert_mongo_doc(result)

    def update_user(self, email: str, update_data: dict) -> UpdateResult:
        """
        Update a user's information by their email.
        Returns the MongoDB update result.
        """
        return self.collection.update_one(
            {"correo_electronico": email},
            {"$set": update_data}
        )

    def delete_user_by_email(self, email: str) -> bool:
        """
        Delete a user by their email address.
        Returns True if successful, False if user not found.
        """
        result = self.collection.delete_one({"correo_electronico": email})
        return result.deleted_count > 0

    def list_users(self, role: Optional[UserRole] = None) -> List[dict]:
        """
        List all users in the database, optionally filtered by role.
        Returns a list of user documents.
        """
        query = {"role": role.value} if role else {}
        users = list(self.collection.find(query))
        # Filter out None values after conversion
        return [doc for doc in (self._convert_mongo_doc(user) for user in users) if doc is not None] 