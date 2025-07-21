# 🦉 RavenCode – Módulo de Usuarios

Este repositorio forma parte del proyecto **RavenCode**, una plataforma de aprendizaje interactiva diseñada para enseñar programación a adolescentes de 12 a 16 años. Aquí se encuentra exclusivamente el **módulo de Usuarios**, que gestiona el registro, inicio de sesión, perfiles, roles y preferencias del usuario.

## 🚀 ¿Cómo ejecutar el módulo?

### 🧠 Backend – FastAPI

1. Ir a la carpeta del backend:
```bash
   cd ravencode-backend-users
```
2. Crear entorno virtual:
```bash
   python -m venv venv
```
3. Activar enorno
* En Windows
```bash
   venv\Scripts\activate
```
* En Mac/Linux
```bash
   source venv/bin/activate
```
4. Instalar dependencias
```bash
   pip install -r requirements.txt
```
5. Ejecutar el servidor
```bash
   uvicorn app.main:app --reload --port 8001
```
6. Verificar en el navegador:
http://localhost:8001/api

## 🔑 Generación de Claves JWT

Este módulo utiliza autenticación JWT con criptografía asimétrica RSA para permitir que otros microservicios verifiquen tokens de forma independiente.

### 📝 Generar Claves

Ejecuta el script automático de generación de claves:

```bash
python scripts/generate_keys.py
```

Este script:
- ✅ Genera un par de claves RSA de 2048 bits
- ✅ Crea archivos `private_key.pem` y `public_key.pem` en `app/keys/`
- ✅ Muestra múltiples opciones de despliegue seguro
- ✅ Proporciona mejores prácticas de seguridad

### 🛡️ Opciones de Despliegue Seguro

#### 1. Variables de Entorno (Recomendado para contenedores)
```bash
export PRIVATE_KEY_CONTENT="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC..."
export PUBLIC_KEY_CONTENT="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuGbXWiK..."
```

#### 2. Variables Codificadas en Base64
```bash
export PRIVATE_KEY_B64="LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t..."
export PUBLIC_KEY_B64="LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0K..."
```

#### 3. Docker Secrets
```bash
# Crear secretos
docker secret create jwt_private_key private_key.pem
docker secret create jwt_public_key public_key.pem

# Usar en docker-compose.yml
services:
  auth-service:
    secrets:
      - jwt_private_key
      - jwt_public_key
    environment:
      - PRIVATE_KEY_PATH=/run/secrets/jwt_private_key
      - PUBLIC_KEY_PATH=/run/secrets/jwt_public_key
```

#### 4. Kubernetes Secrets
```bash
# Crear secreto
kubectl create secret generic jwt-keys \
  --from-literal=private-key="$(cat app/keys/private_key.pem)" \
  --from-literal=public-key="$(cat app/keys/public_key.pem)"
```

### ⚠️ Mejores Prácticas de Seguridad

**Clave Privada (CRÍTICA):**
- ❌ NUNCA commitear al control de versiones
- ❌ NUNCA almacenar en código de aplicación
- ❌ NUNCA loggear o imprimir en aplicación
- ✅ Usar sistemas de gestión de secretos
- ✅ Rotar cada 90 días
- ✅ Permisos restrictivos (`chmod 600`)

**Clave Pública:**
- ✅ Segura para distribuir a otros microservicios
- ✅ Disponible en endpoint `/auth/public-key`
- ✅ Puede ser cacheada por servicios consumidores

## 🔐 Autenticación JWT para Microservicios

RavenCode ofrece **dos métodos principales** para autenticación entre microservicios:

### 🎯 Método 1: Validación Centralizada (Recomendado)
- **Endpoint**: `/auth/validate-token`
- **Ventajas**: Caché inteligente, métricas detalladas, validación en tiempo real
- **Uso**: Perfecto para microservicios que requieren validación confiable

### 🎯 Método 2: Validación Independiente 
- **Endpoint**: `/auth/public-key`
- **Ventajas**: Sin dependencias de red, verificación autónoma
- **Uso**: Ideal para sistemas distribuidos con alta disponibilidad

## 🔄 Método 1: Validación Centralizada con Caché

### 🚀 Validar Token (Recomendado)

**Endpoint principal para microservicios:**

```bash
curl -X POST http://localhost:8001/auth/validate-token \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "skip_cache": false
  }'
```

**Respuesta detallada:**
```json
{
  "is_valid": true,
  "user": {
    "nombre": "Juan Pérez",
    "correo_electronico": "juan@ejemplo.com",
    "role": "student",
    "_id": "60c72b2f9b1e8b3f8c8e4b1a"
  },
  "error": null,
  "expires_at": "2025-01-15T10:30:00",
  "cached": false,
  "validation_time": 45.2
}
```

### ⚡ Características del Sistema de Caché

- **Caché automático**: Resultados válidos se almacenan por 5 minutos
- **Rendimiento optimizado**: ~2ms para tokens cacheados vs ~50ms validación completa
- **TTL inteligente**: Caché se ajusta automáticamente según expiración del token
- **Invalidación**: Limpieza automática de tokens expirados

### 📊 Monitoreo del Caché

```bash
# Obtener estadísticas del caché
curl http://localhost:8001/auth/cache-stats

# Limpiar caché (requiere permisos de admin)
curl -X DELETE http://localhost:8001/auth/cache \
  -H "Authorization: Bearer {admin_token}"
```

## 🔄 Método 2: Validación Independiente

### 📡 Obtener Clave Pública

Los microservicios pueden obtener la clave pública desde:

```bash
curl http://localhost:8001/auth/public-key
```

Respuesta:
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG...",
  "algorithm": "RS256"
}
```

### 🐍 Integración con FastAPI

Crear un microservicio protegido con FastAPI:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
import requests

app = FastAPI(title="Microservicio Protegido")
security = HTTPBearer()

# Obtener clave pública del servicio de auth
response = requests.get("http://localhost:8001/auth/public-key")
key_data = response.json()
PUBLIC_KEY = key_data["public_key"]
ALGORITHM = key_data["algorithm"]

async def get_current_user(token: str = Depends(security)):
    """Dependency para verificar tokens JWT."""
    try:
        payload = jwt.decode(
            token.credentials,
            PUBLIC_KEY,
            algorithms=[ALGORITHM]
        )
        return {
            "email": payload.get("sub"),
            "role": payload.get("role")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

@app.get("/protegido")
async def ruta_protegida(current_user: dict = Depends(get_current_user)):
    return {
        "mensaje": f"¡Hola {current_user['email']}!",
        "rol": current_user["role"],
        "datos_protegidos": "Contenido protegido"
    }

@app.get("/admin")
async def ruta_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acceso de admin requerido")
    
    return {
        "mensaje": "Acceso de administrador concedido",
        "usuario": current_user
    }
```

### 🌶️ Integración con Flask

Crear decoradores para proteger rutas en Flask:

```python
from flask import Flask, request, jsonify
from jose import jwt, JWTError
import requests
import functools

app = Flask(__name__)

# Obtener clave pública
response = requests.get("http://localhost:8001/auth/public-key")
key_data = response.json()
PUBLIC_KEY = key_data["public_key"]
ALGORITHM = key_data["algorithm"]

def require_auth(f):
    """Decorador para requerir autenticación."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Header de autorización requerido'}), 401
        
        try:
            token = auth_header.replace('Bearer ', '')
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
            request.current_user = {
                'email': payload.get('sub'),
                'role': payload.get('role')
            }
        except JWTError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/protegido')
@require_auth
def ruta_protegida():
    return jsonify({
        "mensaje": f"¡Hola {request.current_user['email']}!",
        "datos_protegidos": "Contenido protegido"
    })
```

### 📱 Uso desde el Cliente

Para autenticar requests desde un cliente:

```bash
# 1. Obtener token del servicio de auth
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123"
  }'

# 2. Usar token en otros microservicios
curl http://localhost:8002/protegido \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 📚 Ejemplos Completos

Revisa los archivos de ejemplo para implementaciones completas:

- **`examples/microservice_integration.py`** - Integración con FastAPI, Flask y Django
- **`examples/microservice_token_verification.py`** - Verificación avanzada de tokens
- **`docs/JWT_SECURITY.md`** - Guía completa de seguridad JWT

### 🔄 Flujo de Autenticación Completo

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant Auth as Servicio Auth
    participant MS as Microservicio
    
    Client->>Auth: POST /auth/login (email, password)
    Auth->>Auth: Validar credenciales
    Auth->>Auth: Generar JWT con clave privada
    Auth->>Client: JWT token
    
    Client->>MS: GET /protegido (Authorization: Bearer JWT)
    MS->>Auth: GET /auth/public-key (solo una vez)
    Auth->>MS: Clave pública + algoritmo
    MS->>MS: Verificar JWT con clave pública
    MS->>Client: Datos protegidos
```

### 🔐 Funcionalidades del módulo
Registro de usuarios con validación de campos.

Inicio de sesión con autenticación segura.

Perfiles de usuario con información editable.

Gestión de roles: estudiante, administrador.

Preferencias de interfaz (modo oscuro, notificaciones, etc).

### 👥 Equipo de desarrollo
Proyecto desarrollado por el equipo Cuervos en el curso Ingeniería de Software II – Universidad Nacional de Colombia.

* Diego Felipe Solorzano Aponte

* Laura Valentina Pabon Cabezas

* Diana Valentina Chicuasuque Rodríguez

* Carlos Arturo Murcia Andrade

* Sergio Esteban Rendon Umbarila

* Mateo Andrés Vivas Acosta

* Jorge Andrés Torres Leal

#### Docente: Ing. Camilo Ernesto Vargas Romero
#### Semestre: 2025-1
