from pymongo import MongoClient, ASCENDING, IndexModel
from app.DB.database import get_database
import logging

logger = logging.getLogger(__name__)

def normalize_field_names():
    """
    Normalize field names in the users collection to ensure consistency.
    Converts inconsistent field names to the standard lowercase format.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("Could not connect to database for field normalization")
            return False
        
        users_collection = db["users"]
        
        # Define field mappings (old_name -> new_name)
        field_mappings = {
            "Nombre": "nombre",
            "Correo_electronico": "correo_electronico", 
            "Contrasena": "contrasena",
            "Fecha_de_nacimiento": "fecha_de_nacimiento",
            "Foto_de_perfil": "foto_de_perfil",
            "Institucion_educativa": "institucion_educativa",
            "Grado_academico": "grado_academico"
        }
        
        normalized_count = 0
        
        # Process each field mapping
        for old_field, new_field in field_mappings.items():
            # Find documents with the old field name
            documents_with_old_field = users_collection.find({old_field: {"$exists": True}})
            
            for doc in documents_with_old_field:
                try:
                    # Update the document to use the new field name
                    update_operations = {
                        "$set": {new_field: doc[old_field]},
                        "$unset": {old_field: ""}
                    }
                    
                    users_collection.update_one(
                        {"_id": doc["_id"]},
                        update_operations
                    )
                    normalized_count += 1
                    
                except Exception as e:
                    logger.error(f"Error normalizing document {doc['_id']}: {e}")
        
        if normalized_count > 0:
            logger.info(f"✅ Normalized {normalized_count} field names in user documents")
        else:
            logger.info("✅ All field names already normalized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error normalizing field names: {e}")
        return False

def clean_invalid_users():
    """
    Clean up invalid user documents that might prevent index creation.
    Removes users with null or missing email addresses.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("Could not connect to database for cleanup")
            return False
        
        users_collection = db["users"]
        
        # Find documents with null or missing email
        invalid_users = users_collection.find({
            "$or": [
                {"correo_electronico": {"$exists": False}},
                {"correo_electronico": None},
                {"correo_electronico": ""}
            ]
        })
        
        invalid_count = users_collection.count_documents({
            "$or": [
                {"correo_electronico": {"$exists": False}},
                {"correo_electronico": None},
                {"correo_electronico": ""}
            ]
        })
        
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} users with invalid email addresses")
            
            # Delete invalid users
            result = users_collection.delete_many({
                "$or": [
                    {"correo_electronico": {"$exists": False}},
                    {"correo_electronico": None},
                    {"correo_electronico": ""}
                ]
            })
            
            logger.info(f"✅ Cleaned up {result.deleted_count} invalid user documents")
        else:
            logger.info("✅ No invalid users found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning invalid users: {e}")
        return False

def create_indexes():
    """
    Create necessary database indexes for optimal performance.
    Returns True if successful, False otherwise.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("Could not connect to database for index creation")
            return False
        
        # Normalize field names first
        if not normalize_field_names():
            logger.warning("⚠️  Could not normalize field names, but continuing...")
        
        # Clean up invalid data
        if not clean_invalid_users():
            logger.warning("⚠️  Could not clean invalid users, but continuing...")
        
        # Create indexes for users collection
        users_collection = db["users"]
        
        # Check if email_unique index already exists
        existing_indexes = list(users_collection.list_indexes())
        existing_index_names = [idx["name"] for idx in existing_indexes]
        
        if "email_unique" not in existing_index_names:
            try:
                # Email index (unique) - most common query
                users_collection.create_index([("correo_electronico", ASCENDING)], unique=True, name="email_unique")
                logger.info("✅ Created unique email index")
            except Exception as e:
                if "duplicate key error" in str(e).lower():
                    logger.warning("⚠️  Unique email index creation failed due to duplicate emails")
                    logger.info("Creating non-unique email index instead...")
                    try:
                        users_collection.create_index([("correo_electronico", ASCENDING)], name="email_index")
                        logger.info("✅ Created non-unique email index")
                    except Exception as e2:
                        logger.error(f"❌ Failed to create email index: {e2}")
                else:
                    raise e
        else:
            logger.info("✅ Email index already exists")
        
        # Role index - for filtering by user type
        if "role_index" not in existing_index_names:
            users_collection.create_index([("role", ASCENDING)], name="role_index")
            logger.info("✅ Created role index")
        else:
            logger.info("✅ Role index already exists")
        
        # Compound index for role + email queries
        if "role_email_compound" not in existing_index_names:
            users_collection.create_index([("role", ASCENDING), ("correo_electronico", ASCENDING)], name="role_email_compound")
            logger.info("✅ Created role-email compound index")
        else:
            logger.info("✅ Role-email compound index already exists")
        
        # Create indexes for recovery_codes collection
        recovery_codes_collection = db["recovery_codes"]
        recovery_indexes = list(recovery_codes_collection.list_indexes())
        recovery_index_names = [idx["name"] for idx in recovery_indexes]
        
        # Email + code compound index for recovery operations
        if "recovery_email_code" not in recovery_index_names:
            recovery_codes_collection.create_index([("email", ASCENDING), ("code", ASCENDING)], name="recovery_email_code")
            logger.info("✅ Created recovery email-code index")
        
        # Expiration index for automatic cleanup
        if "recovery_expiration" not in recovery_index_names:
            recovery_codes_collection.create_index([("expires_at", ASCENDING)], name="recovery_expiration")
            logger.info("✅ Created recovery expiration index")
        
        # Create indexes for refresh_tokens collection
        refresh_tokens_collection = db["refresh_tokens"]
        refresh_indexes = list(refresh_tokens_collection.list_indexes())
        refresh_index_names = [idx["name"] for idx in refresh_indexes]
        
        # User email index for token lookup
        if "refresh_user_email" not in refresh_index_names:
            refresh_tokens_collection.create_index([("user_email", ASCENDING)], name="refresh_user_email")
            logger.info("✅ Created refresh token user email index")
        
        # Token index for validation
        if "refresh_token_unique" not in refresh_index_names:
            try:
                refresh_tokens_collection.create_index([("refresh_token", ASCENDING)], unique=True, name="refresh_token_unique")
                logger.info("✅ Created unique refresh token index")
            except Exception as e:
                if "duplicate key error" in str(e).lower():
                    logger.warning("⚠️  Duplicate refresh tokens found, creating non-unique index")
                    refresh_tokens_collection.create_index([("refresh_token", ASCENDING)], name="refresh_token_index")
                else:
                    raise e
        
        # Expiration index for automatic cleanup
        if "refresh_expiration" not in refresh_index_names:
            refresh_tokens_collection.create_index([("expires_at", ASCENDING)], name="refresh_expiration")
            logger.info("✅ Created refresh token expiration index")
        
        logger.info("✅ Database indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating database indexes: {e}")
        return False

def optimize_database():
    """
    Optimize database by creating indexes and performing maintenance tasks.
    Returns True if successful, False otherwise.
    """
    try:
        # Create all necessary indexes
        if not create_indexes():
            return False
        
        logger.info("✅ Database optimization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        return False

def verify_database_setup():
    """
    Verify that the database is properly set up with all collections and indexes.
    Returns True if everything is properly configured, False otherwise.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("Could not connect to database for verification")
            return False
        
        # Check required collections exist (they will be created on first insert)
        required_collections = ["users", "recovery_codes", "refresh_tokens"]
        existing_collections = db.list_collection_names()
        
        for collection_name in required_collections:
            if collection_name not in existing_collections:
                logger.warning(f"Collection '{collection_name}' doesn't exist yet (will be created on first use)")
        
        # Verify indexes on users collection if it exists
        if "users" in existing_collections:
            users_collection = db["users"]
            indexes = list(users_collection.list_indexes())
            index_names = [idx["name"] for idx in indexes]
            
            required_indexes = ["email_unique", "role_index"]
            missing_indexes = [idx for idx in required_indexes if idx not in index_names]
            
            if missing_indexes:
                logger.warning(f"Missing indexes on users collection: {missing_indexes}")
                return False
        
        logger.info("✅ Database setup verification completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False 