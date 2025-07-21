"""
Token Validation Service Integration Examples

This file demonstrates how to integrate with RavenCode's centralized token validation service
from different microservice frameworks. The validation service provides caching, detailed
error reporting, and performance metrics.

Author: RavenCode Team
Date: January 2025
"""

import requests
import time
from typing import Optional, Dict, Any
from functools import wraps

# Configuration
AUTH_SERVICE_URL = "http://localhost:8001"
VALIDATE_TOKEN_ENDPOINT = f"{AUTH_SERVICE_URL}/auth/validate-token"
CACHE_STATS_ENDPOINT = f"{AUTH_SERVICE_URL}/auth/cache-stats"


class TokenValidationClient:
    """
    Client for interacting with RavenCode's token validation service.
    Provides methods for validating tokens and monitoring cache performance.
    """
    
    def __init__(self, auth_service_url: str = AUTH_SERVICE_URL):
        self.auth_service_url = auth_service_url
        self.validate_endpoint = f"{auth_service_url}/auth/validate-token"
        self.cache_stats_endpoint = f"{auth_service_url}/auth/cache-stats"
    
    def validate_token(self, token: str, skip_cache: bool = False) -> Dict[str, Any]:
        """
        Validate a JWT token using the centralized validation service.
        
        Args:
            token: JWT token (without 'Bearer ' prefix)
            skip_cache: If True, bypass cache for real-time validation
            
        Returns:
            Dict with validation result, user data, and performance metrics
        """
        try:
            response = requests.post(
                self.validate_endpoint,
                json={
                    "token": token,
                    "skip_cache": skip_cache
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {
                "is_valid": False,
                "user": None,
                "error": f"Network error: {str(e)}",
                "expires_at": None,
                "cached": False,
                "validation_time": 0.0
            }
    
    def validate_bearer_token(self, authorization_header: str) -> Dict[str, Any]:
        """
        Validate a Bearer token from Authorization header.
        """
        if not authorization_header or not authorization_header.startswith("Bearer "):
            return {
                "is_valid": False,
                "user": None,
                "error": "Invalid Authorization header format",
                "expires_at": None,
                "cached": False,
                "validation_time": 0.0
            }
        
        token = authorization_header[7:]  # Remove "Bearer " prefix
        return self.validate_token(token)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        """
        try:
            response = requests.get(self.cache_stats_endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {"cache_enabled": False, "error": "Failed to get stats"}


# =============================================================================
# FastAPI Integration
# =============================================================================

def fastapi_integration_example():
    """
    Example of integrating token validation service with FastAPI.
    """
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.security import HTTPBearer
    
    app = FastAPI(title="Microservice with Token Validation")
    security = HTTPBearer()
    
    # Global validation client
    validation_client = TokenValidationClient()
    
    async def get_current_user(request: Request):
        """Dependency for validating tokens via the validation service."""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Validate token using the centralized service
        result = validation_client.validate_bearer_token(auth_header)
        
        if not result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        # Add performance metrics to the request for monitoring
        request.state.validation_time = result["validation_time"]
        request.state.cached_result = result["cached"]
        
        return result["user"]
    
    @app.get("/protected")
    async def protected_route(
        request: Request,
        current_user: dict = Depends(get_current_user)
    ):
        """Protected route that requires valid JWT token."""
        return {
            "message": f"Hello {current_user['nombre']}!",
            "user_role": current_user["role"],
            "validation_metrics": {
                "validation_time_ms": request.state.validation_time,
                "result_cached": request.state.cached_result
            }
        }
    
    @app.get("/admin")
    async def admin_route(current_user: dict = Depends(get_current_user)):
        """Admin-only route."""
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return {
            "message": "Admin access granted",
            "cache_stats": validation_client.get_cache_stats()
        }
    
    return app


# =============================================================================
# Flask Integration
# =============================================================================

def flask_integration_example():
    """
    Example of integrating token validation service with Flask.
    """
    from flask import Flask, request, jsonify, g
    import functools
    
    app = Flask(__name__)
    validation_client = TokenValidationClient()
    
    def require_auth(f):
        """Decorator for requiring authentication via validation service."""
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({'error': 'Authorization header required'}), 401
            
            # Validate token
            result = validation_client.validate_bearer_token(auth_header)
            
            if not result["is_valid"]:
                return jsonify({'error': result["error"]}), 401
            
            # Store user and metrics in g for access in route
            g.current_user = result["user"]
            g.validation_metrics = {
                "validation_time_ms": result["validation_time"],
                "cached": result["cached"]
            }
            
            return f(*args, **kwargs)
        return decorated_function
    
    def require_admin(f):
        """Decorator for requiring admin privileges."""
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or g.current_user["role"] != "admin":
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/protected')
    @require_auth
    def protected():
        """Protected route."""
        return jsonify({
            "message": f"Hello {g.current_user['nombre']}!",
            "user_role": g.current_user["role"],
            "validation_metrics": g.validation_metrics
        })
    
    @app.route('/admin/cache-stats')
    @require_auth
    @require_admin
    def admin_cache_stats():
        """Admin route for cache statistics."""
        return jsonify(validation_client.get_cache_stats())
    
    return app


# =============================================================================
# Django Integration
# =============================================================================

def django_integration_example():
    """
    Example middleware and decorators for Django integration.
    """
    from django.http import JsonResponse
    from django.utils.decorators import method_decorator
    from django.views.decorators.csrf import csrf_exempt
    from django.views import View
    import json
    
    validation_client = TokenValidationClient()
    
    class TokenValidationMiddleware:
        """Django middleware for token validation."""
        
        def __init__(self, get_response):
            self.get_response = get_response
        
        def __call__(self, request):
            # Skip validation for certain paths
            skip_paths = ['/health', '/docs', '/login']
            if any(request.path.startswith(path) for path in skip_paths):
                return self.get_response(request)
            
            # Get authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            
            if auth_header:
                result = validation_client.validate_bearer_token(auth_header)
                
                if result["is_valid"]:
                    request.user_data = result["user"]
                    request.validation_metrics = {
                        "validation_time_ms": result["validation_time"],
                        "cached": result["cached"]
                    }
                else:
                    return JsonResponse(
                        {'error': result["error"]}, 
                        status=401
                    )
            
            return self.get_response(request)
    
    def require_auth(view_func):
        """Decorator for requiring authentication."""
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user_data'):
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return view_func(request, *args, **kwargs)
        return wrapper
    
    @method_decorator(csrf_exempt, name='dispatch')
    class ProtectedView(View):
        """Example protected Django view."""
        
        @require_auth
        def get(self, request):
            return JsonResponse({
                "message": f"Hello {request.user_data['nombre']}!",
                "user_role": request.user_data["role"],
                "validation_metrics": request.validation_metrics
            })
    
    return TokenValidationMiddleware, ProtectedView


# =============================================================================
# Performance Testing & Monitoring
# =============================================================================

def performance_test():
    """
    Test the performance difference between cached and non-cached validation.
    """
    client = TokenValidationClient()
    
    # First, you need a valid token - get it from login
    print("🧪 Performance Testing - Token Validation Service")
    print("=" * 60)
    
    # Example token (you would get this from actual login)
    test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  # Replace with real token
    
    print("📊 Testing validation performance...")
    
    # Test 1: Fresh validation (no cache)
    start_time = time.time()
    result1 = client.validate_token(test_token, skip_cache=True)
    fresh_time = (time.time() - start_time) * 1000
    
    print(f"   Fresh validation: {fresh_time:.2f}ms")
    print(f"   Service reported: {result1.get('validation_time', 0):.2f}ms")
    print(f"   Cached: {result1.get('cached', False)}")
    
    # Test 2: Cached validation
    start_time = time.time()
    result2 = client.validate_token(test_token, skip_cache=False)
    cached_time = (time.time() - start_time) * 1000
    
    print(f"   Cached validation: {cached_time:.2f}ms")
    print(f"   Service reported: {result2.get('validation_time', 0):.2f}ms")
    print(f"   Cached: {result2.get('cached', False)}")
    
    # Get cache statistics
    cache_stats = client.get_cache_stats()
    print(f"\n📈 Cache Statistics:")
    for key, value in cache_stats.items():
        print(f"   {key}: {value}")
    
    # Performance improvement calculation
    if fresh_time > 0 and cached_time > 0:
        improvement = ((fresh_time - cached_time) / fresh_time) * 100
        print(f"\n⚡ Performance improvement with cache: {improvement:.1f}%")


def monitoring_dashboard_data():
    """
    Example of collecting monitoring data for dashboards.
    """
    client = TokenValidationClient()
    
    # Collect cache statistics
    stats = client.get_cache_stats()
    
    # Calculate cache hit ratio
    if stats.get("cache_enabled") and stats.get("total_entries", 0) > 0:
        active_ratio = (stats["active_entries"] / stats["total_entries"]) * 100
        
        dashboard_data = {
            "cache_health": {
                "enabled": stats["cache_enabled"],
                "hit_ratio": active_ratio,
                "total_entries": stats["total_entries"],
                "active_entries": stats["active_entries"],
                "expired_entries": stats["expired_entries"]
            },
            "performance_metrics": {
                "cache_ttl_seconds": stats.get("cache_ttl", 0),
                "estimated_cache_hit_speed": "~2ms",
                "estimated_fresh_validation_speed": "~50ms"
            }
        }
        
        return dashboard_data
    
    return {"cache_health": {"enabled": False}}


# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    print("🔐 RavenCode Token Validation Service - Integration Examples")
    print("=" * 65)
    
    print("\n1️⃣ Basic Token Validation")
    client = TokenValidationClient()
    
    # Example of validating a token
    print("   Creating validation client...")
    print(f"   Validation endpoint: {client.validate_endpoint}")
    
    print("\n2️⃣ Framework Integration Examples")
    print("   ✅ FastAPI - Advanced async integration with dependencies")
    print("   ✅ Flask - Decorator-based middleware pattern")
    print("   ✅ Django - Middleware with request enhancement")
    
    print("\n3️⃣ Performance Testing")
    print("   🧪 Run performance_test() to compare cache vs fresh validation")
    
    print("\n4️⃣ Monitoring Integration")
    print("   📊 Use monitoring_dashboard_data() for observability")
    
    print("\n🚀 Quick Start:")
    print("   1. Start the auth service: uvicorn app.main:app --port 8001")
    print("   2. Get a token via POST /auth/login")
    print("   3. Use client.validate_token(your_token) to validate")
    
    print("\n📖 Full documentation available in README.md") 