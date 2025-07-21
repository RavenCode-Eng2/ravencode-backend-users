#!/usr/bin/env python3
"""
Simple JWT Token Verification Test
"""

import requests
from jose import jwt, JWTError
from datetime import datetime

def test_token_verification():
    """Test JWT token verification with your token."""
    
    # Your token from the auth service
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXRlb2F2aXZhc0BnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTI1NTQ4OTB9.A57ipXEL0dh0rgkFPAsmETWw-FkDZ_Yf6-7Se7uGKunfouh8lr_U-X9mTnuYC-B8D3Zc670xTF881kHCCfJ0_DsZpm-fptSo9fnS4h3_cw2Ru2PsT_hTS6Wm76CnJzCLHpfhUq1FT7cM4JPtNWFSRym0Pz8B87ImmE_RTBAPzCqi8f0nH_otDWsTENFvjtlWZLphv-ty5Dtc7PAt34hHKxxpj0RVT7RhYW2ZjDSvuOP5QjGyl9eLsDQagdAw_s95cSu3U3DimxaiwCZ8L2Md2HM1oVma8AnUkHvCVS1SYZjWgqdXa9Je9LjpZu5srRxIO_BVfWD9SFU4LQ9oSpKoGw"
    
    print("🔐 JWT Token Verification Test")
    print("=" * 50)
    
    try:
        # Step 1: Get public key from auth service
        print("\n1️⃣ Fetching public key from auth service...")
        response = requests.get("http://localhost:8000/auth/public-key")
        response.raise_for_status()
        
        key_data = response.json()
        public_key = key_data["public_key"]
        algorithm = key_data["algorithm"]
        
        print(f"✅ Public key fetched successfully")
        print(f"Algorithm: {algorithm}")
        print(f"Public key preview: {public_key[:50]}...")
        
        # Step 2: Verify the token
        print("\n2️⃣ Verifying JWT token...")
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[algorithm]
        )
        
        print("✅ Token verified successfully!")
        print(f"📧 Email: {payload.get('sub')}")
        print(f"👤 Role: {payload.get('role')}")
        print(f"⏰ Expires: {datetime.fromtimestamp(payload.get('exp', 0))}")
        
        # Step 3: Check if token is expired
        exp_timestamp = payload.get('exp', 0)
        is_expired = datetime.now() > datetime.fromtimestamp(exp_timestamp)
        print(f"🕐 Token expired: {is_expired}")
        
        # Step 4: Show complete payload
        print("\n3️⃣ Complete token payload:")
        for key, value in payload.items():
            if key == 'exp':
                print(f"   {key}: {value} ({datetime.fromtimestamp(value)})")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Error fetching public key: {e}")
        return False
    except JWTError as e:
        print(f"❌ Token verification failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_token_verification()
    if success:
        print("\n🎉 Token verification successful!")
        print("\n💡 To use this in your microservice:")
        print("   1. Fetch the public key from /auth/public-key")
        print("   2. Use jose.jwt.decode() to verify tokens")
        print("   3. Extract user info from the payload")
    else:
        print("\n❌ Token verification failed!") 