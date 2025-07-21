#!/usr/bin/env python3
"""
Startup script for RavenCode Users API

This script:
1. Tests database connection
2. Creates necessary indexes
3. Validates RSA keys for JWT authentication
4. Starts the API server

Usage: python startup.py
"""

import sys
import time
import os
from app.DB.database import test_connection
from app.DB.initialize import optimize_database
from app.DB.migrations import run_all_migrations
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rsa_keys():
    """Check if RSA keys are available for JWT authentication"""
    try:
        from app.core.config import settings
        # Try to access the keys to validate they exist
        private_key = settings.PRIVATE_KEY
        public_key = settings.PUBLIC_KEY
        
        if private_key and public_key:
            logger.info("✅ RSA keys loaded successfully")
            return True
        else:
            logger.error("❌ RSA keys not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error loading RSA keys: {e}")
        logger.error("Please generate RSA keys using: python scripts/generate_keys.py")
        return False

def check_environment():
    """Check if required environment variables and files are present"""
    logger.info("🔍 Checking environment setup...")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.warning("⚠️  .env file not found. Using default configuration.")
    else:
        logger.info("✅ .env file found")
    
    # Check MongoDB URL
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    logger.info(f"📡 MongoDB URL: {mongodb_url}")
    
    return True

def main():
    """Main startup function"""
    logger.info("🚀 Starting RavenCode Users API v1.0.0")
    
    # Check environment setup
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Test database connection
    logger.info("📡 Testing database connection...")
    if not test_connection():
        logger.error("❌ Database connection failed. Please check your MongoDB configuration.")
        logger.error("Make sure MongoDB is running and MONGODB_URL is correct in your .env file")
        logger.error("Default MongoDB URL: mongodb://localhost:27017")
        sys.exit(1)
    
    # Check RSA keys for JWT authentication
    logger.info("🔐 Checking RSA keys for JWT authentication...")
    if not check_rsa_keys():
        logger.error("❌ RSA keys check failed.")
        logger.error("Generate keys with: python scripts/generate_keys.py")
        sys.exit(1)
    
    # Run database migrations
    logger.info("📦 Running database migrations...")
    if not run_all_migrations():
        logger.warning("⚠️  Some migrations failed, but continuing...")
    else:
        logger.info("✅ All migrations completed successfully")
    
    # Initialize database
    logger.info("🗄️  Initializing database indexes...")
    if not optimize_database():
        logger.warning("⚠️  Database optimization failed, but continuing...")
    else:
        logger.info("✅ Database optimization completed")
    
    # Start the API server
    logger.info("🌟 Starting API server on http://localhost:8001")
    logger.info("📚 API Documentation available at: http://localhost:8001/docs")
    logger.info("🔧 Alternative docs at: http://localhost:8001/redoc")
    logger.info("❤️  Health check at: http://localhost:8001/health")
    logger.info("🔑 Generate RSA keys with: python scripts/generate_keys.py")
    logger.info("🧪 Test JWT token validation with: python test_token_verification.py")
    
    try:
        # Start uvicorn server
        from app.main import app
        import uvicorn
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001,
            log_level="info",
            reload=False  # Set to True for development
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 