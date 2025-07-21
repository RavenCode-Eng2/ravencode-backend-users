#!/usr/bin/env python3
"""
Refresh Token Example for Client Applications
This demonstrates how to handle access and refresh tokens in client apps.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

class AuthClient:
    """
    Client class that handles authentication with refresh tokens.
    This simulates how a frontend or mobile app would handle tokens.
    """
    
    def __init__(self, auth_service_url: str = "http://localhost:8000"):
        self.auth_service_url = auth_service_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def login(self, email: str, password: str) -> bool:
        """
        Login and store tokens.
        """
        try:
            response = requests.post(
                f"{self.auth_service_url}/auth/login",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 1800)  # Default 30 minutes
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"✅ Login successful!")
            print(f"   Access token expires at: {self.token_expires_at}")
            print(f"   Refresh token: {self.refresh_token[:20]}...")
            
            return True
            
        except requests.RequestException as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def is_token_expired(self) -> bool:
        """
        Check if access token is expired or will expire soon.
        """
        if not self.token_expires_at:
            return True
        
        # Consider token expired if it expires in the next 5 minutes
        buffer_time = timedelta(minutes=5)
        return datetime.now() + buffer_time >= self.token_expires_at
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token.
        """
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            response = requests.post(
                f"{self.auth_service_url}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]  # New refresh token
            
            # Update expiration time
            expires_in = token_data.get("expires_in", 1800)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"✅ Token refreshed successfully!")
            print(f"   New access token expires at: {self.token_expires_at}")
            
            return True
            
        except requests.RequestException as e:
            print(f"❌ Token refresh failed: {e}")
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            return False
    
    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        This is the key method that client apps should use.
        """
        # Check if we have a token and it's not expired
        if self.access_token and not self.is_token_expired():
            return self.access_token
        
        # Try to refresh the token
        if self.refresh_token and self.refresh_access_token():
            return self.access_token
        
        # No valid token available
        print("❌ No valid token available. Please login again.")
        return None
    
    def make_authenticated_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        Make an authenticated request, handling token refresh automatically.
        """
        token = self.get_valid_token()
        if not token:
            return None
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        try:
            response = requests.request(method, f"{self.auth_service_url}{endpoint}", **kwargs)
            
            # If we get 401, try refreshing token once
            if response.status_code == 401 and self.refresh_token:
                print("🔄 Access token expired, refreshing...")
                if self.refresh_access_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.request(method, f"{self.auth_service_url}{endpoint}", **kwargs)
            
            return response
            
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def logout(self) -> bool:
        """
        Logout by revoking the refresh token.
        """
        if not self.refresh_token:
            print("❌ No refresh token to revoke")
            return False
        
        try:
            response = requests.post(
                f"{self.auth_service_url}/auth/logout",
                json={"refresh_token": self.refresh_token}
            )
            response.raise_for_status()
            
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            
            print("✅ Logged out successfully!")
            return True
            
        except requests.RequestException as e:
            print(f"❌ Logout failed: {e}")
            return False
    
    def logout_all_devices(self) -> bool:
        """
        Logout from all devices by revoking all refresh tokens.
        """
        response = self.make_authenticated_request("/auth/logout-all", "POST")
        if response and response.status_code == 200:
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            print("✅ Logged out from all devices!")
            return True
        else:
            print("❌ Failed to logout from all devices")
            return False


def demonstrate_refresh_token_flow():
    """
    Demonstrate the complete refresh token flow.
    """
    print("🔄 Refresh Token Flow Demonstration")
    print("=" * 50)
    
    client = AuthClient()
    
    # Step 1: Login
    print("\n1️⃣ Login")
    if not client.login("mateoavivas@gmail.com", "your_password"):
        print("❌ Cannot proceed without login")
        return
    
    # Step 2: Make authenticated requests
    print("\n2️⃣ Making authenticated requests")
    
    # Test /user/me endpoint
    response = client.make_authenticated_request("/user/me")
    if response and response.status_code == 200:
        user_data = response.json()
        print(f"✅ User data: {user_data.get('nombre', 'Unknown')}")
    else:
        print("❌ Failed to get user data")
    
    # Step 3: Simulate token expiration and refresh
    print("\n3️⃣ Simulating token expiration")
    
    # Manually expire the token for demonstration
    client.token_expires_at = datetime.now() - timedelta(minutes=1)
    print(f"   Token expired: {client.is_token_expired()}")
    
    # Make another request - should automatically refresh
    response = client.make_authenticated_request("/user/me")
    if response and response.status_code == 200:
        print("✅ Token automatically refreshed and request succeeded")
    else:
        print("❌ Token refresh or request failed")
    
    # Step 4: Test logout
    print("\n4️⃣ Testing logout")
    client.logout()
    
    # Try to make a request after logout - should fail
    response = client.make_authenticated_request("/user/me")
    if response is None or response.status_code == 401:
        print("✅ Logout successful - requests now fail as expected")
    else:
        print("❌ Logout may have failed - request still succeeded")


def show_token_security_benefits():
    """
    Show the security benefits of refresh tokens.
    """
    print("\n🔒 Security Benefits of Refresh Tokens")
    print("=" * 50)
    
    print("✅ Short-lived access tokens (30 minutes)")
    print("   - Reduces window of opportunity if token is stolen")
    print("   - Limits damage from compromised tokens")
    
    print("\n✅ Long-lived refresh tokens (7 days)")
    print("   - Better user experience - no frequent logins")
    print("   - Can be revoked immediately if compromised")
    
    print("\n✅ Token rotation")
    print("   - New refresh token issued on each refresh")
    print("   - Prevents replay attacks")
    
    print("\n✅ Selective revocation")
    print("   - Logout from single device: revoke one refresh token")
    print("   - Logout from all devices: revoke all refresh tokens")
    
    print("\n✅ Automatic token management")
    print("   - Client apps handle refresh automatically")
    print("   - Seamless user experience")


def show_client_implementation_patterns():
    """
    Show common patterns for implementing refresh tokens in client apps.
    """
    print("\n📱 Client Implementation Patterns")
    print("=" * 50)
    
    print("1️⃣ Token Storage:")
    print("   - Access token: Memory only (security)")
    print("   - Refresh token: Secure storage (keychain/keystore)")
    
    print("\n2️⃣ Automatic Refresh:")
    print("   - Check token expiry before each request")
    print("   - Refresh if expired or expiring soon")
    print("   - Retry failed requests after refresh")
    
    print("\n3️⃣ Error Handling:")
    print("   - 401 Unauthorized → Try refresh once")
    print("   - Refresh fails → Redirect to login")
    print("   - Network errors → Retry with backoff")
    
    print("\n4️⃣ Background Refresh:")
    print("   - Refresh tokens proactively")
    print("   - Use timers or background tasks")
    print("   - Avoid interrupting user experience")


if __name__ == "__main__":
    print("🔄 Refresh Token System Guide")
    print("=" * 60)
    
    # Demonstrate the flow
    demonstrate_refresh_token_flow()
    
    # Show security benefits
    show_token_security_benefits()
    
    # Show implementation patterns
    show_client_implementation_patterns()
    
    print("\n🚀 Ready for Production!")
    print("Your auth system now supports:")
    print("   ✅ Short-lived access tokens")
    print("   ✅ Long-lived refresh tokens")
    print("   ✅ Automatic token refresh")
    print("   ✅ Secure logout functionality")
    print("   ✅ Multi-device session management") 