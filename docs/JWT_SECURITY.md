# JWT Security Guide for Microservice Authentication

## Overview

This service uses RS256 (RSA with SHA-256) asymmetric cryptography for JWT tokens, providing secure authentication across microservices without requiring network calls for token verification.

## Key Management Security

### 🔐 Private Key Security (CRITICAL)

The private key is used to **sign** JWT tokens and must be kept absolutely secure:

- ❌ **NEVER** commit to version control
- ❌ **NEVER** store in application code
- ❌ **NEVER** log or print in application
- ❌ **NEVER** share via insecure channels
- ✅ Store in secure secret management systems
- ✅ Use environment variables for containers
- ✅ Set restrictive file permissions (600)
- ✅ Rotate regularly (recommended: every 90 days)

### 🔓 Public Key Security

The public key is used to **verify** JWT tokens and can be shared:

- ✅ Safe to distribute to other microservices
- ✅ Can be served via `/auth/public-key` endpoint
- ✅ Can be cached by consuming services
- ✅ Should still be transmitted over HTTPS

## Deployment Options

### 1. Environment Variables (Recommended)

```bash
# Direct key content
export PRIVATE_KEY_CONTENT="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC..."
export PUBLIC_KEY_CONTENT="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuGbXWiK..."

# Or Base64 encoded for easier handling
export PRIVATE_KEY_B64="LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t..."
export PUBLIC_KEY_B64="LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0K..."
```

### 2. File Paths

```bash
# Store keys in secure locations
export PRIVATE_KEY_PATH="/etc/ssl/private/jwt_private.pem"
export PUBLIC_KEY_PATH="/etc/ssl/certs/jwt_public.pem"

# Set proper permissions
chmod 600 /etc/ssl/private/jwt_private.pem
chmod 644 /etc/ssl/certs/jwt_public.pem
chown app:app /etc/ssl/private/jwt_private.pem
```

### 3. Docker Secrets

```bash
# Create secrets
docker secret create jwt_private_key private_key.pem
docker secret create jwt_public_key public_key.pem

# Use in docker-compose.yml
services:
  auth-service:
    secrets:
      - jwt_private_key
      - jwt_public_key
    environment:
      - PRIVATE_KEY_PATH=/run/secrets/jwt_private_key
      - PUBLIC_KEY_PATH=/run/secrets/jwt_public_key
```

### 4. Kubernetes Secrets

```yaml
# Create secret
apiVersion: v1
kind: Secret
metadata:
  name: jwt-keys
type: Opaque
data:
  private-key: <base64-encoded-private-key>
  public-key: <base64-encoded-public-key>

---
# Use in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  template:
    spec:
      containers:
      - name: auth-service
        env:
        - name: PRIVATE_KEY_CONTENT
          valueFrom:
            secretKeyRef:
              name: jwt-keys
              key: private-key
        - name: PUBLIC_KEY_CONTENT
          valueFrom:
            secretKeyRef:
              name: jwt-keys
              key: public-key
```

### 5. Cloud Secret Managers

#### AWS Secrets Manager
```bash
# Store secret
aws secretsmanager create-secret \
  --name "jwt-private-key" \
  --secret-string "$(cat private_key.pem)"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id jwt-private-key \
  --query SecretString --output text
```

#### Google Secret Manager
```bash
# Store secret
gcloud secrets create jwt-private-key --data-file=private_key.pem

# Retrieve in application
gcloud secrets versions access latest --secret="jwt-private-key"
```

#### Azure Key Vault
```bash
# Store secret
az keyvault secret set \
  --vault-name MyKeyVault \
  --name jwt-private-key \
  --file private_key.pem

# Retrieve in application
az keyvault secret show \
  --vault-name MyKeyVault \
  --name jwt-private-key \
  --query value --output tsv
```

## Token Verification for Other Services

Other microservices can verify tokens independently:

```python
from jose import jwt
import requests

# Get public key from auth service
response = requests.get("https://auth-service/auth/public-key")
public_key_data = response.json()

def verify_token(token: str) -> dict:
    """Verify JWT token using public key."""
    try:
        payload = jwt.decode(
            token,
            public_key_data["public_key"],
            algorithms=[public_key_data["algorithm"]]
        )
        return payload
    except jwt.JWTError:
        raise ValueError("Invalid token")

# Use in FastAPI dependency
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = verify_token(token.credentials)
        return payload
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Security Best Practices

### Key Rotation
- Rotate keys every 90 days
- Support multiple public keys during rotation
- Use key IDs in JWT headers for multi-key support

### Monitoring
- Monitor key access patterns
- Log authentication failures
- Set up alerts for unusual activity
- Track token usage patterns

### Network Security
- Always use HTTPS for token transmission
- Implement rate limiting on auth endpoints
- Use API gateways for additional security layers
- Implement proper CORS policies

### Token Management
- Use short token lifetimes (15-30 minutes)
- Implement refresh token mechanism
- Consider token blacklisting for immediate revocation
- Include necessary claims only

## Development vs Production

### Development
- Keys can be stored locally in `app/keys/`
- Use longer token lifetimes for convenience
- Less strict monitoring requirements

### Production
- Must use secure secret management
- Implement proper key rotation
- Use short token lifetimes
- Comprehensive monitoring and alerting
- Regular security audits

## Quick Start

1. Generate keys:
   ```bash
   python scripts/generate_keys.py
   ```

2. Choose deployment method from the script output

3. Set environment variables:
   ```bash
   export PRIVATE_KEY_CONTENT="your-private-key"
   export PUBLIC_KEY_CONTENT="your-public-key"
   ```

4. Other services get public key:
   ```bash
   curl https://your-auth-service/auth/public-key
   ```

## Troubleshooting

### Common Issues
- **"Private key not found"**: Check environment variables and file paths
- **"Invalid key format"**: Ensure proper PEM formatting with line breaks
- **"Algorithm mismatch"**: Verify all services use RS256
- **"Token verification failed"**: Check clock synchronization between services

### Debugging
```bash
# Check key format
openssl rsa -in private_key.pem -text -noout

# Verify key pair
openssl rsa -in private_key.pem -pubout | diff - public_key.pem

# Test token generation
python -c "from app.services.auth import AuthService; print(AuthService().create_access_token({'sub': 'test'}))"
``` 