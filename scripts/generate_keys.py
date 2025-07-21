#!/usr/bin/env python3
"""
Script to generate RSA keys for JWT authentication.
Provides multiple secure deployment options.
"""

import os
import subprocess
import base64
from pathlib import Path

def generate_rsa_keys():
    """Generate RSA key pair for JWT signing."""
    
    # Create keys directory if it doesn't exist
    keys_dir = Path("app/keys")
    keys_dir.mkdir(exist_ok=True)
    
    private_key_path = keys_dir / "private_key.pem"
    public_key_path = keys_dir / "public_key.pem"
    
    print("🔐 Generating RSA key pair...")
    
    # Generate private key
    subprocess.run([
        "openssl", "genpkey", 
        "-algorithm", "RSA", 
        "-out", str(private_key_path),
        "-pkeyopt", "rsa_keygen_bits:2048"
    ], check=True)
    
    # Generate public key
    subprocess.run([
        "openssl", "rsa", 
        "-pubout", 
        "-in", str(private_key_path),
        "-out", str(public_key_path)
    ], check=True)
    
    print(f"✅ Keys generated successfully!")
    print(f"📁 Private key: {private_key_path}")
    print(f"📁 Public key: {public_key_path}")
    
    return private_key_path, public_key_path

def show_deployment_options(private_key_path, public_key_path):
    """Show different secure deployment options."""
    
    with open(private_key_path, 'r') as f:
        private_key = f.read()
    
    with open(public_key_path, 'r') as f:
        public_key = f.read()
    
    print("\n" + "="*80)
    print("🚀 SECURE DEPLOYMENT OPTIONS")
    print("="*80)
    
    print("\n1️⃣  ENVIRONMENT VARIABLES (Recommended for containers)")
    print("-" * 50)
    print("Set these environment variables:")
    print(f'export PRIVATE_KEY_CONTENT="{private_key.strip()}"')
    print(f'export PUBLIC_KEY_CONTENT="{public_key.strip()}"')
    
    print("\n2️⃣  BASE64 ENCODED (For easier env var handling)")
    print("-" * 50)
    private_b64 = base64.b64encode(private_key.encode()).decode()
    public_b64 = base64.b64encode(public_key.encode()).decode()
    print(f"export PRIVATE_KEY_B64='{private_b64}'")
    print(f"export PUBLIC_KEY_B64='{public_b64}'")
    print("\n# Then in your app, decode with:")
    print("# import base64")
    print("# private_key = base64.b64decode(os.getenv('PRIVATE_KEY_B64')).decode()")
    
    print("\n3️⃣  FILE PATHS (For traditional deployments)")
    print("-" * 50)
    print("Store keys in secure locations and set:")
    print("export PRIVATE_KEY_PATH='/etc/ssl/private/jwt_private.pem'")
    print("export PUBLIC_KEY_PATH='/etc/ssl/certs/jwt_public.pem'")
    
    print("\n4️⃣  DOCKER SECRETS (For Docker Swarm)")
    print("-" * 50)
    print("# Create secrets:")
    print("docker secret create jwt_private_key private_key.pem")
    print("docker secret create jwt_public_key public_key.pem")
    print("# Then mount in container:")
    print("export PRIVATE_KEY_PATH='/run/secrets/jwt_private_key'")
    print("export PUBLIC_KEY_PATH='/run/secrets/jwt_public_key'")
    
    print("\n5️⃣  KUBERNETES SECRETS")
    print("-" * 50)
    print("# Create secret:")
    print("kubectl create secret generic jwt-keys \\")
    print(f"  --from-literal=private-key='{private_key.strip()}' \\")
    print(f"  --from-literal=public-key='{public_key.strip()}'")
    print("# Then use in deployment as env vars from secret")
    
    print("\n6️⃣  CLOUD SECRET MANAGERS")
    print("-" * 50)
    print("AWS Secrets Manager:")
    print("aws secretsmanager create-secret --name jwt-private-key --secret-string 'private_key_content'")
    print("\nGoogle Secret Manager:")
    print("gcloud secrets create jwt-private-key --data-file=private_key.pem")
    print("\nAzure Key Vault:")
    print("az keyvault secret set --vault-name MyKeyVault --name jwt-private-key --file private_key.pem")
    
    print("\n⚠️  SECURITY BEST PRACTICES")
    print("-" * 50)
    print("✅ Never commit keys to version control")
    print("✅ Use different keys for different environments")
    print("✅ Rotate keys regularly")
    print("✅ Restrict file permissions (chmod 600)")
    print("✅ Use secret management systems in production")
    print("✅ Monitor key access and usage")
    print("❌ Never store keys in application code")
    print("❌ Never log or print private keys")
    print("❌ Never share keys via insecure channels")

def main():
    """Main function."""
    print("🔑 JWT RSA Key Generator for Microservice Authentication")
    print("=" * 60)
    
    try:
        private_key_path, public_key_path = generate_rsa_keys()
        show_deployment_options(private_key_path, public_key_path)
        
        print(f"\n🔒 Remember to:")
        print(f"   1. Add app/keys/ to .gitignore (already done)")
        print(f"   2. Set appropriate file permissions:")
        print(f"      chmod 600 {private_key_path}")
        print(f"      chmod 644 {public_key_path}")
        print(f"   3. Choose a secure deployment method above")
        print(f"   4. Delete local keys after deployment")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating keys: {e}")
        print("Make sure OpenSSL is installed and available in PATH")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 