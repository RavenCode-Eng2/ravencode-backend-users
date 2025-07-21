#!/usr/bin/env python3
"""
Example: JWT Token Verification for Other Microservices
This demonstrates how to verify tokens issued by the auth service.
"""

import requests
from jose import jwt, JWTError
from typing import Dict, Optional
import json
from datetime import datetime

class AuthTokenVerifier:
    """
    Token verification class for microservices.
    Fetches public key from auth service and verifies tokens.
    """
    
    def __init__(self, auth_service_url: str = "http://localhost:8000"):
        self.auth_service_url = auth_service_url
        self.public_key = None
        self.algorithm = None
        self._fetch_public_key()
    
    def _fetch_public_key(self):
        """Fetch public key from auth service."""
        try:
            response = requests.get(f"{self.auth_service_url}/auth/public-key")
            response.raise_for_status()
            
            key_data = response.json()
            self.public_key = key_data["public_key"]
            self.algorithm = key_data["algorithm"]
            
            print("✅ Public key fetched successfully")
            print(f"Algorithm: {self.algorithm}")
            
        except requests.RequestException as e:
            print(f"❌ Error fetching public key: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm]
            )
            
            print("✅ Token verified successfully")
            return payload
            
        except JWTError as e:
            print(f"❌ Token verification failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def get_user_info(self, token: str) -> Optional[Dict]:
        """
        Extract user information from token.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: User information if token is valid
        """
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # Extract user info from token payload
        user_info = {
            "email": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
            "is_expired": datetime.now() > datetime.fromtimestamp(payload.get("exp", 0))
        }
        
        return user_info


# FastAPI Integration Example
def create_fastapi_auth_dependency():
    """
    Create a FastAPI dependency for token verification.
    Use this in your FastAPI microservice.
    """
    from fastapi import HTTPException, Depends, status
    from fastapi.security import HTTPBearer
    
    security = HTTPBearer()
    verifier = AuthTokenVerifier()
    
    async def get_current_user(token: str = Depends(security)):
        """FastAPI dependency to get current user from token."""
        try:
            payload = verifier.verify_token(token.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return {
                "email": payload.get("sub"),
                "role": payload.get("role"),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0))
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    return get_current_user


# Example FastAPI route using the dependency
def example_fastapi_routes():
    """
    Example FastAPI routes that use token verification.
    """
    from fastapi import FastAPI, Depends
    
    app = FastAPI()
    get_current_user = create_fastapi_auth_dependency()
    
    @app.get("/protected")
    async def protected_route(current_user: dict = Depends(get_current_user)):
        return {
            "message": f"Hello {current_user['email']}!",
            "role": current_user['role'],
            "access_granted": True
        }
    
    @app.get("/admin-only")
    async def admin_only_route(current_user: dict = Depends(get_current_user)):
        if current_user['role'] != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return {
            "message": "Admin access granted",
            "user": current_user
        }
    
    return app


# Flask Integration Example
def create_flask_auth_decorator():
    """
    Create a Flask decorator for token verification.
    Use this in your Flask microservice.
    """
    from functools import wraps
    from flask import request, jsonify
    
    verifier = AuthTokenVerifier()
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header required'}), 401
            
            # Verify token
            payload = verifier.verify_token(auth_header)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Add user info to request context
            request.current_user = {
                'email': payload.get('sub'),
                'role': payload.get('role'),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0))
            }
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_admin(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            auth_result = require_auth(f)
            if hasattr(auth_result, 'status_code') and auth_result.status_code != 200:
                return auth_result
            
            # Check admin role
            if request.current_user['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return require_auth, require_admin


def main():
    """
    Main function to demonstrate token verification.
    """
    print("🔐 JWT Token Verification Example")
    print("=" * 50)
    
    # Your token from the auth service
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXRlb2F2aXZhc0BnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTI1NTQ4OTB9.A57ipXEL0dh0rgkFPAsmETWw-FkDZ_Yf6-7Se7uGKunfouh8lr_U-X9mTnuYC-B8D3Zc670xTF881kHCCfJ0_DsZpm-fptSo9fnS4h3_cw2Ru2PsT_hTS6Wm76CnJzCLHpfhUq1FT7cM4JPtNWFSRym0Pz8B87ImmE_RTBAPzCqi8f0nH_otDWsTENFvjtlWZLphv-ty5Dtc7PAt34hHKxxpj0RVT7RhYW2ZjDSvuOP5QjGyl9eLsDQagdAw_s95cSu3U3DimxaiwCZ8L2Md2HM1oVma8AnUkHvCVS1SYZjWgqdXa9Je9LjpZu5srRxIO_BVfWD9SFU4LQ9oSpKoGw"
    
    try:
        # Initialize verifier
        verifier = AuthTokenVerifier()
        
        # Test 1: Verify token
        print("\n1️⃣ Testing Token Verification:")
        payload = verifier.verify_token(token)
        if payload:
            print(f"✅ Token is valid!")
            print(f"📧 Email: {payload.get('sub')}")
            print(f"👤 Role: {payload.get('role')}")
            print(f"⏰ Expires: {datetime.fromtimestamp(payload.get('exp', 0))}")
        else:
            print("❌ Token verification failed")
            return
        
        # Test 2: Get user info
        print("\n2️⃣ Testing User Info Extraction:")
        user_info = verifier.get_user_info(token)
        if user_info:
            print(f"✅ User info extracted:")
            for key, value in user_info.items():
                print(f"   {key}: {value}")
        
        # Test 3: Test with Bearer prefix
        print("\n3️⃣ Testing with Bearer prefix:")
        bearer_token = f"Bearer {token}"
        payload = verifier.verify_token(bearer_token)
        if payload:
            print("✅ Bearer token verification successful")
        
        # Test 4: Show token structure
        print("\n4️⃣ Token Structure Analysis:")
        parts = token.split('.')
        print(f"   Header: {parts[0][:50]}...")
        print(f"   Payload: {parts[1][:50]}...")
        print(f"   Signature: {parts[2][:50]}...")
        
        print("\n🚀 Integration Examples:")
        print("   - FastAPI: Use create_fastapi_auth_dependency()")
        print("   - Flask: Use create_flask_auth_decorator()")
        print("   - Custom: Use AuthTokenVerifier class directly")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 