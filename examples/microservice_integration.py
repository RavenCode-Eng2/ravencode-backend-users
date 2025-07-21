#!/usr/bin/env python3
"""
Microservice JWT Integration Examples
This shows how to integrate JWT verification in different frameworks.
"""

import requests
from jose import jwt, JWTError
from datetime import datetime
from typing import Dict, Optional, Callable
import functools

class JWTVerifier:
    """Reusable JWT verification class for microservices."""
    
    def __init__(self, auth_service_url: str = "http://localhost:8000"):
        self.auth_service_url = auth_service_url
        self.public_key = None
        self.algorithm = None
        self._fetch_public_key()
    
    def _fetch_public_key(self):
        """Fetch public key from auth service."""
        response = requests.get(f"{self.auth_service_url}/auth/public-key")
        response.raise_for_status()
        
        key_data = response.json()
        self.public_key = key_data["public_key"]
        self.algorithm = key_data["algorithm"]
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload."""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm]
            )
            
            return payload
            
        except JWTError:
            return None


# 1. FastAPI Integration
def create_fastapi_app():
    """Create a FastAPI app with JWT authentication."""
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer
    
    app = FastAPI(title="Protected Microservice")
    security = HTTPBearer()
    verifier = JWTVerifier()
    
    async def get_current_user(token: str = Depends(security)):
        """FastAPI dependency for JWT verification."""
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
    
    async def require_admin(current_user: dict = Depends(get_current_user)):
        """Require admin role."""
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    @app.get("/")
    async def public_endpoint():
        return {"message": "This is a public endpoint"}
    
    @app.get("/protected")
    async def protected_endpoint(current_user: dict = Depends(get_current_user)):
        return {
            "message": f"Hello {current_user['email']}!",
            "role": current_user["role"],
            "protected_data": "This is protected content"
        }
    
    @app.get("/admin")
    async def admin_endpoint(admin_user: dict = Depends(require_admin)):
        return {
            "message": "Admin access granted",
            "admin_data": "Top secret admin information",
            "user": admin_user
        }
    
    return app


# 2. Flask Integration
def create_flask_app():
    """Create a Flask app with JWT authentication."""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    verifier = JWTVerifier()
    
    def require_auth(f):
        """Flask decorator for JWT verification."""
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header required'}), 401
            
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
        """Flask decorator for admin access."""
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # First apply auth requirement
            auth_decorator = require_auth(f)
            result = auth_decorator(*args, **kwargs)
            
            # Check if auth failed
            if hasattr(result, 'status_code') and result.status_code != 200:
                return result
            
            # Check admin role
            if request.current_user['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    def public_endpoint():
        return jsonify({"message": "This is a public endpoint"})
    
    @app.route('/protected')
    @require_auth
    def protected_endpoint():
        return jsonify({
            "message": f"Hello {request.current_user['email']}!",
            "role": request.current_user["role"],
            "protected_data": "This is protected content"
        })
    
    @app.route('/admin')
    @require_admin
    def admin_endpoint():
        return jsonify({
            "message": "Admin access granted",
            "admin_data": "Top secret admin information",
            "user": request.current_user
        })
    
    return app


# 3. Django Integration (simplified)
def create_django_middleware():
    """Create Django middleware for JWT authentication."""
    
    class JWTAuthenticationMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response
            self.verifier = JWTVerifier()
        
        def __call__(self, request):
            # Add JWT verification to request
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header:
                payload = self.verifier.verify_token(auth_header)
                if payload:
                    request.jwt_user = {
                        'email': payload.get('sub'),
                        'role': payload.get('role'),
                        'expires_at': datetime.fromtimestamp(payload.get('exp', 0))
                    }
                else:
                    request.jwt_user = None
            else:
                request.jwt_user = None
            
            response = self.get_response(request)
            return response
    
    return JWTAuthenticationMiddleware


# 4. Generic Python Function
def verify_request_token(request_headers: Dict[str, str]) -> Optional[Dict]:
    """Generic function to verify JWT from request headers."""
    verifier = JWTVerifier()
    
    # Get Authorization header
    auth_header = request_headers.get('Authorization') or request_headers.get('authorization')
    if not auth_header:
        return None
    
    # Verify token
    payload = verifier.verify_token(auth_header)
    if not payload:
        return None
    
    return {
        'email': payload.get('sub'),
        'role': payload.get('role'),
        'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
        'is_admin': payload.get('role') == 'admin'
    }


# 5. Testing Examples
def test_with_your_token():
    """Test with your actual token."""
    
    # Your token
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXRlb2F2aXZhc0BnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTI1NTQ4OTB9.A57ipXEL0dh0rgkFPAsmETWw-FkDZ_Yf6-7Se7uGKunfouh8lr_U-X9mTnuYC-B8D3Zc670xTF881kHCCfJ0_DsZpm-fptSo9fnS4h3_cw2Ru2PsT_hTS6Wm76CnJzCLHpfhUq1FT7cM4JPtNWFSRym0Pz8B87ImmE_RTBAPzCqi8f0nH_otDWsTENFvjtlWZLphv-ty5Dtc7PAt34hHKxxpj0RVT7RhYW2ZjDSvuOP5QjGyl9eLsDQagdAw_s95cSu3U3DimxaiwCZ8L2Md2HM1oVma8AnUkHvCVS1SYZjWgqdXa9Je9LjpZu5srRxIO_BVfWD9SFU4LQ9oSpKoGw"
    
    print("🧪 Testing JWT Verification")
    print("=" * 40)
    
    # Test 1: Direct verification
    verifier = JWTVerifier()
    payload = verifier.verify_token(token)
    
    if payload:
        print("✅ Direct verification successful")
        print(f"   Email: {payload.get('sub')}")
        print(f"   Role: {payload.get('role')}")
    else:
        print("❌ Direct verification failed")
        return
    
    # Test 2: Generic function
    headers = {'Authorization': f'Bearer {token}'}
    user_info = verify_request_token(headers)
    
    if user_info:
        print("✅ Generic function test successful")
        print(f"   User: {user_info}")
    else:
        print("❌ Generic function test failed")
    
    # Test 3: Simulated HTTP requests
    print("\n📡 Simulated HTTP Requests:")
    
    # Simulate different endpoints
    endpoints = [
        ("GET /", "Public endpoint - no auth needed"),
        ("GET /protected", "Protected endpoint - requires valid token"),
        ("GET /admin", "Admin endpoint - requires admin role")
    ]
    
    for endpoint, description in endpoints:
        print(f"\n{endpoint}:")
        print(f"   {description}")
        
        if "public" in endpoint.lower():
            print("   ✅ Access granted (public)")
        elif user_info:
            if "admin" in endpoint.lower() and user_info['is_admin']:
                print("   ✅ Access granted (admin)")
            elif "admin" not in endpoint.lower():
                print("   ✅ Access granted (authenticated)")
            else:
                print("   ❌ Access denied (not admin)")
        else:
            print("   ❌ Access denied (not authenticated)")


if __name__ == "__main__":
    print("🔐 Microservice JWT Integration Examples")
    print("=" * 50)
    
    # Test with your token
    test_with_your_token()
    
    print("\n🚀 Framework Integration Available:")
    print("   - FastAPI: create_fastapi_app()")
    print("   - Flask: create_flask_app()")
    print("   - Django: create_django_middleware()")
    print("   - Generic: verify_request_token()")
    
    print("\n📝 Usage Examples:")
    print("   # FastAPI")
    print("   app = create_fastapi_app()")
    print("   # uvicorn microservice_integration:app")
    print()
    print("   # Flask")
    print("   app = create_flask_app()")
    print("   # flask --app microservice_integration:app run")
    print()
    print("   # Generic verification")
    print("   user = verify_request_token(request.headers)")
    print("   if user and user['is_admin']: # admin logic") 