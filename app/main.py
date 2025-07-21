import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, user
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.metrics import REQUEST_COUNT, RESPONSE_TIME, ERROR_COUNT

app = FastAPI(
    title="API de Gestión de Usuarios RavenCode",
    description="""
API completa para la gestión de usuarios, autenticación y perfiles en la plataforma RavenCode

Esta API proporciona endpoints para:

🔐 AUTENTICACIÓN
• Registro de usuarios - Crear nuevas cuentas de estudiante
• Inicio de sesión - Autenticación con JWT tokens
• Recuperación de contraseña - Proceso completo de recuperación
• Verificación de tokens - Validar tokens JWT

👤 GESTIÓN DE USUARIOS
• CRUD completo - Crear, leer, actualizar y eliminar usuarios (estudiantes y administradores)
• Búsqueda por email - Obtener usuarios específicos
• Actualización de perfiles - Modificar información personal
• Listado de usuarios - Obtener todos los usuarios del sistema


👤 PERFIL DE USUARIO
• Información personal - Obtener datos del usuario autenticado
• Gestión de perfil - Administrar información del usuario

🔒 SEGURIDAD
• Autenticación JWT con tokens de acceso y renovación
• Validación de datos con Pydantic
• Encriptación de contraseñas con bcrypt
• Protección CORS configurada

📊 FORMATOS DE RESPUESTA
Todas las respuestas siguen estándares REST con códigos de estado HTTP apropiados y mensajes de error descriptivos en español.

Esta documentación está completamente en español para facilitar su uso por desarrolladores hispanohablantes.
    """,
    version="1.0.0",
    contact={
        "name": "Equipo RavenCode",
        "email": "support@ravencode.com",
    },
    license_info={
        "name": "MIT",
    },
    terms_of_service="/terms",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operaciones de autenticación y autorización. Incluye registro, inicio de sesión, recuperación de contraseña y verificación de tokens.",
        },
        {
            "name": "Users",
            "description": "Operaciones CRUD para usuarios. Gestión completa de perfiles de usuarios (estudiantes y administradores) incluyendo creación, consulta, actualización, eliminación y listado.",
        }
    ]
    title="API de Gestión de Usuarios RavenCode",
    description="""
API completa para la gestión de usuarios, autenticación y perfiles en la plataforma RavenCode

Esta API proporciona endpoints para:

🔐 AUTENTICACIÓN
• Registro de usuarios - Crear nuevas cuentas de estudiante
• Inicio de sesión - Autenticación con JWT tokens
• Recuperación de contraseña - Proceso completo de recuperación
• Verificación de tokens - Validar tokens JWT

👤 GESTIÓN DE USUARIOS
• CRUD completo - Crear, leer, actualizar y eliminar usuarios (estudiantes y administradores)
• Búsqueda por email - Obtener usuarios específicos
• Actualización de perfiles - Modificar información personal
• Listado de usuarios - Obtener todos los usuarios del sistema


👤 PERFIL DE USUARIO
• Información personal - Obtener datos del usuario autenticado
• Gestión de perfil - Administrar información del usuario

🔒 SEGURIDAD
• Autenticación JWT con tokens de acceso y renovación
• Validación de datos con Pydantic
• Encriptación de contraseñas con bcrypt
• Protección CORS configurada

📊 FORMATOS DE RESPUESTA
Todas las respuestas siguen estándares REST con códigos de estado HTTP apropiados y mensajes de error descriptivos en español.

Esta documentación está completamente en español para facilitar su uso por desarrolladores hispanohablantes.
    """,
    version="1.0.0",
    contact={
        "name": "Equipo RavenCode",
        "email": "support@ravencode.com",
    },
    license_info={
        "name": "MIT",
    },
    terms_of_service="/terms",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operaciones de autenticación y autorización. Incluye registro, inicio de sesión, recuperación de contraseña y verificación de tokens.",
        },
        {
            "name": "Users",
            "description": "Operaciones CRUD para usuarios. Gestión completa de perfiles de usuarios (estudiantes y administradores) incluyendo creación, consulta, actualización, eliminación y listado.",
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/users", tags=["Users"])


# Middleware para registrar métricas
@app.middleware("http")
async def record_metrics(request, call_next):
    method = request.method
    endpoint = request.url.path

    # Registrar la hora de inicio para medir el tiempo de respuesta
    start_time = time.time()

    # Continuar con la solicitud
    response = await call_next(request)

    # Medir tiempo de respuesta
    duration = time.time() - start_time
    RESPONSE_TIME.labels(method=method, endpoint=endpoint).observe(duration)

    # Incrementar contador de peticiones
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    # Si hay un error (código de estado >= 400), aumentar el contador de errores
    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()

    return response

# Ruta para exponer las métricas en formato Prometheus
@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Middleware para registrar métricas
@app.middleware("http")
async def record_metrics(request, call_next):
    method = request.method
    endpoint = request.url.path

    # Registrar la hora de inicio para medir el tiempo de respuesta
    start_time = time.time()

    # Continuar con la solicitud
    response = await call_next(request)

    # Medir tiempo de respuesta
    duration = time.time() - start_time
    RESPONSE_TIME.labels(method=method, endpoint=endpoint).observe(duration)

    # Incrementar contador de peticiones
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    # Si hay un error (código de estado >= 400), aumentar el contador de errores
    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()

    return response

# Ruta para exponer las métricas en formato Prometheus
@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get(
    "/",
    summary="Página de inicio de la API",
    description="Endpoint raíz que proporciona información básica sobre la API y enlaces útiles",
    response_description="Mensaje de bienvenida y enlaces de documentación",
    tags=["General"]
)
async def root():
    """
    Endpoint de Bienvenida
    
    Proporciona información básica sobre la API y enlaces a la documentación.
    
    Respuesta:
    - message: Mensaje de bienvenida
    - docs_url: URL de la documentación Swagger UI
    - redoc_url: URL de la documentación ReDoc
    """
    return {
        "message": "Bienvenido a la API de Gestión de Usuarios RavenCode",
        "description": "API para gestión de usuarios, autenticación y perfiles",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get(
    "/health",
    summary="Estado de salud de la API",
    description="Endpoint para verificar el estado de la API y la conectividad de la base de datos",
    response_description="Estado de la API y sus dependencias",
    tags=["General"]
)
async def health():
    """
    Endpoint de Salud
    
    Verifica que la API esté funcionando correctamente y que pueda conectarse a la base de datos.
    
    Respuesta:
    - status: Estado general de la API
    - database: Estado de la conexión a MongoDB
    - timestamp: Momento de la verificación
    """
    from app.DB.database import test_connection
    from datetime import datetime
    
    database_status = "healthy" if test_connection() else "unhealthy"
    overall_status = "healthy" if database_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "database": database_status,
        "service": "RavenCode Users API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
