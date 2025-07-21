from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import hashlib
import json
from jose import JWTError, jwt
from app.core.config import settings
from app.services.user import UserService
from app.models.user import UserRole


class TokenValidationCache:
    """
    Simple in-memory cache for token validation results.
    In production, consider using Redis or Memcached.
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, token: str) -> str:
        """Generate a cache key from token."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result."""
        key = self._generate_key(token)
        if key in self._cache:
            entry = self._cache[key]
            if datetime.utcnow() < entry['expires_at']:
                return entry['data']
            else:
                # Remove expired entry
                del self._cache[key]
        return None
    
    def set(self, token: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache validation result."""
        key = self._generate_key(token)
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            'data': data,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def remove(self, token: str) -> None:
        """Remove specific token from cache."""
        key = self._generate_key(token)
        self._cache.pop(key, None)


class TokenValidationService:
    """
    Service for validating JWT tokens with caching support.
    Designed for microservice authentication scenarios.
    """
    
    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 300):
        self.user_service = UserService()
        self.cache_enabled = cache_enabled
        self.cache: Optional[TokenValidationCache] = TokenValidationCache(cache_ttl) if cache_enabled else None
    
    def validate_token(self, token: str, skip_cache: bool = False) -> Dict[str, Any]:
        """
        Validate JWT token and return comprehensive result.
        
        Args:
            token: JWT token string (without 'Bearer ' prefix)
            skip_cache: If True, bypass cache and validate directly
            
        Returns:
            Dictionary with validation result:
            {
                "is_valid": bool,
                "user": dict or None,
                "error": str or None,
                "expires_at": datetime or None,
                "cached": bool
            }
        """
        # Check cache first (if enabled and not skipped)
        if self.cache_enabled and self.cache and not skip_cache:
            cached_result = self.cache.get(token)
            if cached_result is not None:
                cached_result["cached"] = True
                return cached_result
        
        # Perform actual validation
        result = self._validate_token_direct(token)
        result["cached"] = False
        
        # Cache the result (if enabled and token is valid)
        if self.cache_enabled and self.cache and result["is_valid"]:
            # Calculate TTL based on token expiration
            ttl = self._calculate_cache_ttl(result.get("expires_at"))
            self.cache.set(token, result, ttl)
        
        return result
    
    def _validate_token_direct(self, token: str) -> Dict[str, Any]:
        """
        Perform direct token validation without caching.
        """
        try:
            # Decode the JWT token using the public key
            payload = jwt.decode(
                token, 
                settings.PUBLIC_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            email = payload.get("sub")
            role = payload.get("role")
            exp = payload.get("exp")
            
            if email is None or role is None:
                return {
                    "is_valid": False,
                    "user": None,
                    "error": "Token missing required fields (sub or role)",
                    "expires_at": None
                }
            
            # Convert expiration timestamp to datetime
            expires_at = datetime.utcfromtimestamp(exp) if exp else None
            
            # Get user from database
            user = self.user_service.get_user_by_email(email)
            if user is None:
                return {
                    "is_valid": False,
                    "user": None,
                    "error": f"User not found: {email}",
                    "expires_at": expires_at
                }
            
            # Verify role matches
            if user.get("role") != role:
                return {
                    "is_valid": False,
                    "user": None,
                    "error": f"Role mismatch: token role '{role}' != user role '{user.get('role')}'",
                    "expires_at": expires_at
                }
            
            # Remove sensitive information
            user_data = user.copy()
            user_data.pop("contrasena", None)
            
            return {
                "is_valid": True,
                "user": user_data,
                "error": None,
                "expires_at": expires_at
            }
            
        except JWTError as e:
            return {
                "is_valid": False,
                "user": None,
                "error": f"JWT validation failed: {str(e)}",
                "expires_at": None
            }
        except Exception as e:
            return {
                "is_valid": False,
                "user": None,
                "error": f"Unexpected error: {str(e)}",
                "expires_at": None
            }
    
    def _calculate_cache_ttl(self, expires_at: Optional[datetime]) -> int:
        """
        Calculate appropriate cache TTL based on token expiration.
        Returns TTL in seconds, with a maximum of cache default TTL.
        """
        default_ttl = self.cache.default_ttl if self.cache else 300
        
        if expires_at is None:
            return default_ttl
        
        now = datetime.utcnow()
        time_until_expiry = (expires_at - now).total_seconds()
        
        # Use the minimum of remaining token time and default cache TTL
        # Also ensure we don't cache for more than 80% of remaining time
        max_cache_time = min(
            default_ttl,
            int(time_until_expiry * 0.8)
        )
        
        return max(60, max_cache_time)  # Minimum 1 minute cache
    
    def validate_bearer_token(self, authorization_header: str) -> Dict[str, Any]:
        """
        Validate Bearer token from Authorization header.
        
        Args:
            authorization_header: Full Authorization header value
            
        Returns:
            Same format as validate_token()
        """
        if not authorization_header:
            return {
                "is_valid": False,
                "user": None,
                "error": "No authorization header provided",
                "expires_at": None,
                "cached": False
            }
        
        if not authorization_header.startswith("Bearer "):
            return {
                "is_valid": False,
                "user": None,
                "error": "Invalid authorization header format. Expected 'Bearer <token>'",
                "expires_at": None,
                "cached": False
            }
        
        token = authorization_header[7:]  # Remove "Bearer " prefix
        return self.validate_token(token)
    
    def invalidate_token_cache(self, token: str) -> None:
        """
        Remove token from cache. Useful when a token is explicitly revoked.
        """
        if self.cache_enabled and self.cache:
            self.cache.remove(token)
    
    def clear_cache(self) -> None:
        """
        Clear all cached validation results.
        """
        if self.cache_enabled and self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        """
        if not self.cache_enabled or not self.cache:
            return {"cache_enabled": False}
        
        cache_size = len(self.cache._cache)
        now = datetime.utcnow()
        expired_count = sum(
            1 for entry in self.cache._cache.values() 
            if now >= entry['expires_at']
        )
        
        return {
            "cache_enabled": True,
            "total_entries": cache_size,
            "expired_entries": expired_count,
            "active_entries": cache_size - expired_count,
            "cache_ttl": self.cache.default_ttl
        }


# Global instance for easy access
_token_validation_service = None

def get_token_validation_service() -> TokenValidationService:
    """
    Get the global token validation service instance.
    """
    global _token_validation_service
    if _token_validation_service is None:
        _token_validation_service = TokenValidationService()
    return _token_validation_service 