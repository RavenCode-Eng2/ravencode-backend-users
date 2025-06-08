from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "ravencode_db"

def get_database():
    """
    Create and return a connection to the MongoDB database.
    Connects to the database specified by DATABASE_NAME using the MONGODB_URL.
    Returns:
        db (Database): The MongoDB database object if connection is successful, None otherwise.
    Also prints a message indicating the connection status.
    """
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def test_connection():
    """
    Test the MongoDB connection and return True if successful, False otherwise.
    Prints a message indicating the result of the connection attempt.
    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        client = MongoClient(MONGODB_URL)
        # Test the connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def close_database(client: MongoClient):
    """
    Close the MongoDB database connection.
    Args:
        client (MongoClient): The MongoClient instance to close.
    Prints a message when the connection is closed.
    """
    if client:
        client.close()
        print("MongoDB connection closed.")
