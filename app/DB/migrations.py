"""
Database migration functions for RavenCode Users API
"""

from datetime import datetime
from app.DB.database import get_database
import logging

logger = logging.getLogger(__name__)

def add_created_at_to_users():
    """
    Add created_at field to all existing users who don't have it.
    Sets a default value for existing users.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("Could not connect to database for migration")
            return False
        
        users_collection = db["users"]
        
        # Find users without created_at field
        users_without_created_at = users_collection.find({
            "created_at": {"$exists": False}
        })
        
        updated_count = 0
        default_date = datetime.utcnow()
        
        for user in users_without_created_at:
            try:
                email = user.get("correo_electronico", "Unknown")
                
                # Update user with created_at field
                result = users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"created_at": default_date}}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ Added created_at to user: {email}")
                    updated_count += 1
                else:
                    logger.warning(f"⚠️  Failed to update user: {email}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing user {user.get('correo_electronico', 'Unknown')}: {e}")
        
        logger.info(f"🎯 Migration completed: Added created_at to {updated_count} users")
        return updated_count >= 0
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def run_all_migrations():
    """
    Run all pending migrations.
    """
    logger.info("🚀 Starting database migrations...")
    
    migrations = [
        ("add_created_at_to_users", add_created_at_to_users),
    ]
    
    success_count = 0
    
    for migration_name, migration_func in migrations:
        logger.info(f"⚡ Running migration: {migration_name}")
        try:
            if migration_func():
                logger.info(f"✅ Migration {migration_name} completed successfully")
                success_count += 1
            else:
                logger.error(f"❌ Migration {migration_name} failed")
        except Exception as e:
            logger.error(f"❌ Migration {migration_name} failed with error: {e}")
    
    logger.info(f"🎯 Migrations completed: {success_count}/{len(migrations)} successful")
    return success_count == len(migrations) 