from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
from app.services.auth import AuthService
from app.services.token_validation import get_token_validation_service, TokenValidationService
from app.models.auth import Token, RefreshTokenRequest
from app.models.user import Student, Admin, User, UserRole
from datetime import date, datetime
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class LoginRequest(BaseModel):
    """Modelo de solicitud para el inicio de sesión"""
    email: EmailStr = Field(description="Dirección de correo electrónico del usuario")
    password: str = Field(description="Contraseña del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "estudiante@ejemplo.com",
                "password": "mi_contraseña_segura"
            }
        }

class RegisterRequest(BaseModel):
    """Modelo de solicitud para el registro de nuevos estudiantes"""
    nombre: str = Field(description="Nombre completo del estudiante")
    email: EmailStr = Field(description="Dirección de correo electrónico")
    password: str = Field(min_length=6, description="Contraseña (mínimo 6 caracteres)")
    fecha_de_nacimiento: date = Field(description="Fecha de nacimiento del estudiante")
    institucion_educativa: str = Field(description="Institución educativa donde estudia")
    grado_academico: str = Field(description="Grado académico actual")
    foto_de_perfil: Optional[str] = Field(None, description="URL de la foto de perfil (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez García",
                "email": "juan.perez@universidad.edu",
                "password": "contraseña123",
                "fecha_de_nacimiento": "2000-05-15",
                "institucion_educativa": "Universidad Nacional",
                "grado_academico": "Licenciatura en Ingeniería",
                "foto_de_perfil": "https://ejemplo.com/foto.jpg"
            }
        }

class TokenData(BaseModel):
    email: str | None = None

class PasswordRecoveryRequest(BaseModel):
    """Modelo de solicitud para recuperación de contraseña"""
    email: EmailStr = Field(description="Correo electrónico para recuperación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com"
            }
        }

class PasswordRecoveryVerify(BaseModel):
    """Modelo para verificar código de recuperación y establecer nueva contraseña"""
    email: EmailStr = Field(description="Correo electrónico del usuario")
    code: str = Field(description="Código de verificación recibido por email")
    new_password: str = Field(min_length=6, description="Nueva contraseña (mínimo 6 caracteres)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com",
                "code": "123456",
                "new_password": "nueva_contraseña_segura"
            }
        }

class TokenVerifyResponse(BaseModel):
    """Modelo de respuesta para verificación de tokens"""
    is_valid: bool = Field(..., description="Indica si el token es válido")
    user: Optional[Dict[str, Any]] = Field(None, description="Información del usuario si el token es válido")
    message: str = Field(..., description="Mensaje descriptivo del resultado")

class TokenValidationResponse(BaseModel):
    """Modelo de respuesta avanzado para validación de tokens en microservicios"""
    is_valid: bool = Field(..., description="Indica si el token es válido")
    user: Optional[Dict[str, Any]] = Field(None, description="Información del usuario si el token es válido")
    error: Optional[str] = Field(None, description="Descripción del error si el token es inválido")
    expires_at: Optional[datetime] = Field(None, description="Fecha y hora de expiración del token")
    cached: bool = Field(..., description="Indica si el resultado proviene de cache")
    validation_time: float = Field(..., description="Tiempo de validación en milisegundos")

class TokenValidationRequest(BaseModel):
    """Modelo de solicitud para validación de tokens"""
    token: str = Field(..., description="Token JWT a validar (sin prefijo 'Bearer')")
    skip_cache: bool = Field(False, description="Si es True, omite el cache y valida directamente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "skip_cache": False
            }
        }

def get_auth_service():
    """Inyector de dependencias para AuthService."""
    return AuthService()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Obtiene el usuario actual desde el token JWT.
    Verifica el token usando la clave pública.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token using the public key
        payload = jwt.decode(
            token, 
            settings.PUBLIC_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        role = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
    except JWTError as e:
        print(f"Error de verificación JWT: {str(e)}")
        raise credentials_exception
    
    # Get the user from the database using the unified user service
    user = auth_service.user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario no encontrado con email: {email}"
        )
    
    # Verify the user's role matches the token
    if user.get("role") != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol de usuario no coincide"
        )
    
    # Remove password from user data
    user.pop("contrasena", None)
    return user



@router.post(
    "/login", 
    response_model=Token,
    summary="Iniciar sesión con JSON",
    description="Endpoint de inicio de sesión que acepta credenciales en formato JSON",
    responses={
        200: {
            "description": "Inicio de sesión exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {
            "description": "Credenciales incorrectas",
            "content": {
                "application/json": {
                    "example": {"detail": "Email o contraseña incorrectos"}
                }
            }
        }
    }
)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ## Inicio de sesión con formato JSON
    
    Endpoint de inicio de sesión que acepta email y contraseña en formato JSON.
    Funciona tanto para estudiantes como administradores.
    
    ### Parámetros del cuerpo de la petición
    - **email**: Dirección de correo electrónico registrada
    - **password**: Contraseña de la cuenta
    
    ### Respuesta exitosa
    Retorna un objeto Token con:
    - **access_token**: Token JWT para autenticación (válido por 1 hora)
    - **refresh_token**: Token para renovar el access_token
    - **token_type**: Tipo de token (siempre "bearer")
    - **expires_in**: Tiempo de expiración en segundos (3600)
    
    ### Uso del token
    Incluir en el header de futuras peticiones:
    ```
    Authorization: Bearer {access_token}
    ```
    """
    auth_result = auth_service.authenticate_user(login_data.email, login_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_result

@router.post(
    "/token", 
    response_model=Token,
    summary="Obtener token de acceso (OAuth2)",
    description="Endpoint compatible con OAuth2 para autenticación mediante formulario - usado por Swagger UI",
    responses={
        200: {
            "description": "Token de acceso obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {
            "description": "Credenciales incorrectas",
            "content": {
                "application/json": {
                    "example": {"detail": "Nombre de usuario o contraseña incorrectos"}
                }
            }
        }
    }
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ## Obtener Token de Acceso (OAuth2)
    
    Endpoint compatible con el estándar OAuth2 para obtener tokens de acceso.
    Este endpoint es utilizado por Swagger UI para la autenticación.
    
    ### Parámetros del formulario
    - **username**: Dirección de correo electrónico del usuario
    - **password**: Contraseña de la cuenta
    - **grant_type**: Tipo de concesión (siempre "password")
    - **scope**: Ámbito de acceso (opcional)
    - **client_id**: ID del cliente (opcional)
    - **client_secret**: Secreto del cliente (opcional)
    
    ### Respuesta exitosa
    Retorna un objeto Token con:
    - **access_token**: Token JWT para autenticación
    - **refresh_token**: Token para renovar el access_token
    - **token_type**: Tipo de token (siempre "bearer")
    - **expires_in**: Tiempo de expiración en segundos
    
    ### Uso en Swagger UI
    1. Haz clic en "Authorize" en la parte superior de Swagger UI
    2. Ingresa tu email en el campo "username"
    3. Ingresa tu contraseña en el campo "password"
    4. Haz clic en "Authorize"
    
    ### Nota
    Este endpoint acepta el email en el campo "username" siguiendo la convención OAuth2.
    """
    # OAuth2 uses 'username' field, but we expect an email
    auth_result = auth_service.authenticate_user(form_data.username, form_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_result

@router.post(
    "/register", 
    response_model=Dict[str, Any], 
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo estudiante",
    description="Crear una nueva cuenta de estudiante con información personal",
    responses={
        201: {
            "description": "Estudiante registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Estudiante registrado exitosamente",
                        "student": {
                            "nombre": "Juan Pérez García",
                            "correo_electronico": "juan.perez@universidad.edu",
                            "fecha_de_nacimiento": "2000-05-15",
                            "institucion_educativa": "Universidad Nacional",
                            "grado_academico": "Licenciatura en Ingeniería",
                            "foto_de_perfil": "https://ejemplo.com/foto.jpg",
                            "role": "student",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Email ya registrado o datos inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "El email ya está registrado"}
                }
            }
        },
        422: {
            "description": "Error de validación de datos",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def register(
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ## Registro de nuevo estudiante
    
    Crea una nueva cuenta de estudiante con información personal básica.
    La contraseña se cifra automáticamente antes del almacenamiento.
    
    ### Parámetros requeridos
    - **nombre**: Nombre completo del estudiante
    - **email**: Dirección de correo electrónico (debe ser única)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **fecha_de_nacimiento**: Fecha de nacimiento en formato YYYY-MM-DD
    - **institucion_educativa**: Nombre de la institución educativa
    - **grado_academico**: Grado o nivel académico actual
    
    ### Parámetros opcionales
    - **foto_de_perfil**: URL de la imagen de perfil
    
    ### Validaciones
    - El email debe tener formato válido
    - El email no debe estar ya registrado
    - La contraseña debe tener al menos 6 caracteres
    - La fecha de nacimiento debe ser válida
    
    ### Respuesta exitosa
    Retorna información del estudiante creado (sin contraseña) y mensaje de confirmación.
    """
    try:
        # Create student model with hashed password
        student = Student(
            nombre=register_data.nombre,
            correo_electronico=register_data.email,
            contrasena=auth_service.get_password_hash(register_data.password),
            fecha_de_nacimiento=register_data.fecha_de_nacimiento,
            institucion_educativa=register_data.institucion_educativa,
            grado_academico=register_data.grado_academico,
            foto_de_perfil=register_data.foto_de_perfil
        )
        
        # Create the student in the database
        created_student = auth_service.student_service.create_student(student)
        
        # Remove password from response
        created_student.pop("contrasena", None)
        
        return {
            "message": "Estudiante registrado exitosamente",
            "student": created_student
        }
    except Exception as e:
        if "already exists" in str(e) or "ya existe" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post(
    "/recovery/request", 
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
    description="Envía un código de recuperación al email del usuario",
    responses={
        200: {
            "description": "Código de recuperación enviado exitosamente",
            "content": {
                "application/json": {
                    "example": {"message": "Código de recuperación enviado a tu email"}
                }
            }
        },
        404: {
            "description": "Usuario no encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Usuario no encontrado"}
                }
            }
        }
    }
)
async def request_password_recovery(
    request: PasswordRecoveryRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ## Solicitar recuperación de contraseña
    
    Inicia el proceso de recuperación de contraseña enviando un código de verificación
    al email del usuario. Funciona tanto para estudiantes como administradores.
    
    ### Proceso
    1. Verifica que el email esté registrado
    2. Genera un código de recuperación único
    3. Envía el código por email
    4. El código tiene validez limitada (normalmente 15 minutos)
    
    ### Parámetros
    - **email**: Dirección de correo electrónico registrada
    
    ### Respuesta exitosa
    Confirma que el código fue enviado (sin revelar información sensible).
    
    ### Siguiente paso
    Usar el endpoint `/recovery/verify` con el código recibido para establecer nueva contraseña.
    """
    try:
        # Check if user exists (either student or admin)
        user = auth_service.user_service.get_user_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Generate and send recovery code
        code = auth_service.generate_recovery_code(request.email)
        auth_service.send_recovery_email(request.email, code)

        return {"message": "Código de recuperación enviado a tu email"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )

@router.post(
    "/recovery/verify", 
    status_code=status.HTTP_200_OK,
    summary="Verificar código y cambiar contraseña",
    description="Verifica el código de recuperación y establece nueva contraseña",
    responses={
        200: {
            "description": "Contraseña actualizada exitosamente",
            "content": {
                "application/json": {
                    "example": {"message": "Contraseña actualizada exitosamente"}
                }
            }
        },
        400: {
            "description": "Código inválido o expirado",
            "content": {
                "application/json": {
                    "example": {"detail": "Código de recuperación inválido o expirado"}
                }
            }
        }
    }
)
async def verify_recovery_code(
    request: PasswordRecoveryVerify,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ## Verificar código de recuperación y cambiar contraseña
    
    Completa el proceso de recuperación de contraseña verificando el código
    y estableciendo la nueva contraseña.
    
    ### Proceso
    1. Verifica que el código sea válido y no haya expirado
    2. Cifra la nueva contraseña
    3. Actualiza la contraseña en la base de datos
    4. Marca el código como usado para evitar reutilización
    
    ### Parámetros
    - **email**: Dirección de correo electrónico del usuario
    - **code**: Código de verificación recibido por email
    - **new_password**: Nueva contraseña (mínimo 6 caracteres)
    
    ### Validaciones
    - El código debe ser válido y no haber expirado
    - El código no debe haber sido usado previamente
    - La nueva contraseña debe cumplir requisitos mínimos
    
    ### Respuesta exitosa
    Confirma que la contraseña fue actualizada correctamente.
    """
    try:
        # Verify the code
        if not auth_service.verify_recovery_code(request.email, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de recuperación inválido o expirado"
            )

        # Update the password
        if not auth_service.update_user_password(request.email, request.new_password):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar la contraseña"
            )

        # Mark the code as used
        auth_service.mark_recovery_code_used(request.email, request.code)

        return {"message": "Contraseña actualizada exitosamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}"
        ) 

@router.post(
    "/verify", 
    response_model=TokenVerifyResponse,
    summary="Verificar validez de token",
    description="Verifica si un token JWT es válido y retorna información del usuario",
    responses={
        200: {
            "description": "Verificación completada (puede ser válido o inválido)",
            "content": {
                "application/json": {
                    "examples": {
                        "token_valido": {
                            "summary": "Token válido",
                            "value": {
                                "is_valid": True,
                                "user": {
                                    "nombre": "Juan Pérez",
                                    "correo_electronico": "juan@ejemplo.com",
                                    "role": "student",
                                    "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                                },
                                "message": "Token es válido"
                            }
                        },
                        "token_invalido": {
                            "summary": "Token inválido",
                            "value": {
                                "is_valid": False,
                                "user": None,
                                "message": "Token inválido: no se pudo decodificar JWT"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def verify_token(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenVerifyResponse:
    """
    ## Verificar validez de token JWT
    
    Verifica si un token JWT es válido y retorna la información del usuario asociado.
    Útil para validaciones en microservicios o aplicaciones cliente.
    
    ### Parámetros
    - **token**: Token JWT en el header Authorization (Bearer {token})
    
    ### Proceso de verificación
    1. Decodifica el token JWT usando la clave secreta
    2. Extrae email y rol del payload
    3. Verifica que el usuario existe en la base de datos
    4. Confirma que el rol coincide con el token
    
    ### Respuesta
    Siempre retorna HTTP 200 con un objeto que indica:
    - **is_valid**: `true` si el token es válido, `false` en caso contrario
    - **user**: Información del usuario (sin contraseña) si el token es válido
    - **message**: Mensaje descriptivo del resultado de la verificación
    
    ### Casos de token inválido
    - Token malformado o corrupto
    - Token expirado
    - Usuario no encontrado en la base de datos
    - Rol del usuario no coincide con el token
    - Firma del token inválida
    """
    try:
        # Decode the JWT token using the public key
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        
        if email is None or role is None:
            return TokenVerifyResponse(
                is_valid=False,
                user=None,
                message="Token inválido: faltan campos requeridos"
            )

        # Get the user from the database based on role
        if role == UserRole.ADMIN.value:
            user = auth_service.admin_service.get_admin_by_email(email)
        else:
            user = auth_service.student_service.get_student_by_email(email)

        if user is None:
            return TokenVerifyResponse(
                is_valid=False,
                user=None,
                message="Usuario no encontrado"
            )

        # Remove sensitive information
        user.pop("contrasena", None)
        
        return TokenVerifyResponse(
            is_valid=True,
            user=user,
            message="Token es válido"
        )

    except JWTError:
        return TokenVerifyResponse(
            is_valid=False,
            user=None,
            message="Token inválido: no se pudo decodificar JWT"
        )

@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    summary="Validar token JWT (Para Microservicios)",
    description="Endpoint avanzado para validación de tokens JWT con caché y métricas detalladas",
    responses={
        200: {
            "description": "Resultado de validación (siempre HTTP 200, verificar 'is_valid' en respuesta)",
            "content": {
                "application/json": {
                    "examples": {
                        "token_valido": {
                            "summary": "Token válido",
                            "value": {
                                "is_valid": True,
                                "user": {
                                    "nombre": "Juan Pérez",
                                    "correo_electronico": "juan@ejemplo.com",
                                    "role": "student",
                                    "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                                },
                                "error": None,
                                "expires_at": "2025-01-15T10:30:00",
                                "cached": False,
                                "validation_time": 45.2
                            }
                        },
                        "token_invalido": {
                            "summary": "Token inválido",
                            "value": {
                                "is_valid": False,
                                "user": None,
                                "error": "JWT validation failed: token expired",
                                "expires_at": None,
                                "cached": False,
                                "validation_time": 12.8
                            }
                        }
                    }
                }
            }
        }
    }
)
async def validate_token_advanced(
    request: TokenValidationRequest,
    validation_service: TokenValidationService = Depends(get_token_validation_service)
) -> TokenValidationResponse:
    """
    ## Validación Avanzada de Tokens JWT para Microservicios
    
    Este endpoint está diseñado específicamente para la validación de tokens en 
    arquitecturas de microservicios, proporcionando:
    
    ### ✨ Características Principales
    - **Caché inteligente**: Resultados cacheados por hasta 5 minutos
    - **Métricas de rendimiento**: Tiempo de validación incluido
    - **Validación completa**: Verificación de usuario en base de datos
    - **Respuesta detallada**: Error específico en caso de fallo
    
    ### 🔧 Parámetros
    - **token**: Token JWT sin el prefijo 'Bearer '
    - **skip_cache**: Omitir caché para validación en tiempo real
    
    ### 📊 Respuesta
    Siempre retorna HTTP 200 con información detallada:
    - **is_valid**: Indica si el token es válido
    - **user**: Datos del usuario (sin contraseña) si el token es válido
    - **error**: Mensaje específico del error si el token es inválido
    - **expires_at**: Timestamp de expiración del token
    - **cached**: Indica si el resultado proviene del caché
    - **validation_time**: Tiempo de validación en milisegundos
    
    ### 🚀 Optimización
    - Primera validación: ~50ms (consulta a BD)
    - Validaciones cacheadas: ~2ms
    - Caché automático basado en expiración del token
    
    ### 💡 Casos de Uso
    - Middleware de autenticación en microservicios
    - Validación de tokens en gateways API
    - Verificación en tiempo real de sesiones
    - Auditoría y logging de accesos
    """
    import time
    start_time = time.time()
    
    # Perform token validation
    result = validation_service.validate_token(
        token=request.token,
        skip_cache=request.skip_cache
    )
    
    # Calculate validation time
    validation_time_ms = (time.time() - start_time) * 1000
    
    return TokenValidationResponse(
        is_valid=result["is_valid"],
        user=result["user"],
        error=result["error"],
        expires_at=result["expires_at"],
        cached=result["cached"],
        validation_time=round(validation_time_ms, 2)
    )

@router.get(
    "/public-key",
    summary="Obtener clave pública para verificación JWT",
    description="Proporciona la clave pública y algoritmo utilizados para verificar tokens JWT",
    responses={
        200: {
            "description": "Clave pública obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "algorithm": "RS256",
                        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq...\n-----END PUBLIC KEY-----"
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudo obtener la clave pública"}
                }
            }
        }
    }
)
async def get_public_key():
    """
    ## Obtener clave pública para verificación JWT
    
    Proporciona la clave pública RSA y el algoritmo utilizado para verificar la validez
    de los tokens JWT. Este endpoint es especialmente útil para microservicios que necesitan
    verificar tokens sin acceso directo a las claves.
    
    ### Uso principal
    - **Microservicios**: Verificación independiente de tokens JWT
    - **Aplicaciones cliente**: Validación local de tokens
    - **Sistemas distribuidos**: Compartir clave pública entre servicios
    
    ### Información retornada
    - **algorithm**: Algoritmo criptográfico utilizado (RS256)
    - **public_key**: Clave pública RSA en formato PEM
    
    ### Seguridad
    - Este endpoint es público por naturaleza
    - La clave pública no compromete la seguridad del sistema
    - Solo permite verificar tokens, no crearlos
    
    ### Formato de clave
    La clave pública se retorna en formato PEM estándar:
    ```
    -----BEGIN PUBLIC KEY-----
    [contenido de la clave en base64]
    -----END PUBLIC KEY-----
    ```
    
    ### 🔒 Nota de seguridad
    La clave pública es segura para compartir y no permite crear tokens,
    solo verificar su autenticidad.
    """
    try:
        return {
            "algorithm": settings.ALGORITHM,
            "public_key": settings.PUBLIC_KEY
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo obtener la clave pública: {str(e)}"
        )

@router.get(
    "/cache-stats",
    summary="Estadísticas del caché de validación",
    description="Obtener estadísticas del sistema de caché para validación de tokens",
    responses={
        200: {
            "description": "Estadísticas del caché obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "cache_enabled": True,
                        "total_entries": 150,
                        "expired_entries": 5,
                        "active_entries": 145,
                        "cache_ttl": 300
                    }
                }
            }
        }
    }
)
async def get_cache_stats(
    validation_service: TokenValidationService = Depends(get_token_validation_service)
):
    """
    ## Estadísticas del Caché de Validación
    
    Proporciona información sobre el estado del sistema de caché utilizado
    para optimizar la validación de tokens JWT.
    
    ### Métricas incluidas
    - **cache_enabled**: Si el caché está habilitado
    - **total_entries**: Total de entradas en el caché
    - **expired_entries**: Entradas expiradas pendientes de limpieza
    - **active_entries**: Entradas válidas disponibles
    - **cache_ttl**: Tiempo de vida por defecto (segundos)
    
    ### Uso recomendado
    - Monitoreo de rendimiento del sistema
    - Optimización de la configuración del caché
    - Debugging de problemas de autenticación
    - Métricas para dashboards de administración
    """
    return validation_service.get_cache_stats()

@router.delete(
    "/cache",
    summary="Limpiar caché de validación",
    description="Eliminar todas las entradas del caché de validación de tokens",
    responses={
        200: {
            "description": "Caché limpiado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Caché limpiado exitosamente",
                        "cleared_entries": 47
                    }
                }
            }
        }
    }
)
async def clear_cache(
    current_user: dict = Depends(get_current_user),
    validation_service: TokenValidationService = Depends(get_token_validation_service)
):
    """
    ## Limpiar Caché de Validación
    
    Elimina todas las entradas del caché de validación de tokens.
    Útil para forzar re-validación de todos los tokens.
    
    ### Casos de uso
    - Cambios de configuración de seguridad
    - Revocación masiva de tokens
    - Mantenimiento del sistema
    - Debugging de problemas de caché
    
    ### Permisos requeridos
    - Usuario autenticado con permisos de administrador
    
    ### Impacto en rendimiento
    - Tokens se validarán directamente contra la BD
    - Aumento temporal en latencia de validación
    - El caché se reconstruirá automáticamente
    """
    # Only allow admins to clear cache
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden limpiar el caché"
        )
    
    # Get stats before clearing
    stats_before = validation_service.get_cache_stats()
    cleared_entries = stats_before.get("active_entries", 0) if stats_before.get("cache_enabled") else 0
    
    # Clear the cache
    validation_service.clear_cache()
    
    return {
        "message": "Caché limpiado exitosamente",
        "cleared_entries": cleared_entries
    } 

@router.post(
    "/refresh", 
    response_model=Token,
    summary="Renovar token de acceso",
    description="Genera un nuevo token de acceso usando un refresh token válido",
    responses={
        200: {
            "description": "Token renovado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {
            "description": "Refresh token inválido o expirado",
            "content": {
                "application/json": {
                    "example": {"detail": "Token de renovación inválido o expirado"}
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al renovar token"}
                }
            }
        }
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """
    ## Renovar token de acceso
    
    Permite obtener un nuevo token de acceso sin necesidad de volver a autenticarse,
    utilizando un refresh token válido. Esto mejora la experiencia del usuario
    evitando reautenticaciones frecuentes.
    
    ### Parámetros del cuerpo
    - **refresh_token**: Token de renovación obtenido durante el login inicial
    
    ### Comportamiento
    - Verifica que el refresh token sea válido y no haya expirado
    - Genera un nuevo access token con tiempo de vida renovado
    - Puede generar también un nuevo refresh token (rotación de tokens)
    - Invalida el refresh token anterior por seguridad
    
    ### Ciclo de vida de tokens
    1. **Login inicial**: Se obtienen access_token y refresh_token
    2. **Uso normal**: Se usa access_token para peticiones API
    3. **Token expira**: Cuando access_token expira, usar este endpoint
    4. **Renovación**: Se obtienen nuevos tokens usando refresh_token
    5. **Repetir**: El ciclo continúa hasta logout o inactividad prolongada
    
    ### Tiempos de expiración
    - **Access token**: 1 hora (para operaciones API)
    - **Refresh token**: 7 días (para renovaciones)
    
    ### Respuesta exitosa
    Retorna nuevos tokens con la misma estructura que el login:
    - **access_token**: Nuevo token JWT para autenticación
    - **refresh_token**: Nuevo token para futuras renovaciones
    - **token_type**: Siempre "bearer"
    - **expires_in**: Tiempo de expiración del access_token en segundos
    
    ### Casos de uso
    - Mantener sesión activa sin interrupciones
    - Implementar auto-renovación en aplicaciones cliente
    - Reducir friction en aplicaciones móviles
    
    ### 🔄 Buenas prácticas
    - Implementar renovación automática antes de que expire el access_token
    - Manejar adecuadamente los errores 401 para redirect a login
    - Almacenar tokens de forma segura en el cliente
    """
    try:
        new_tokens = auth_service.refresh_access_token(request.refresh_token)
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de renovación inválido o expirado"
            )
        return new_tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al renovar token: {str(e)}"
        )

@router.post(
    "/logout",
    summary="Cerrar sesión",
    description="Cierra la sesión del usuario revocando su refresh token específico",
    responses={
        200: {
            "description": "Sesión cerrada exitosamente",
            "content": {
                "application/json": {
                    "example": {"message": "Sesión cerrada exitosamente"}
                }
            }
        },
        400: {
            "description": "Refresh token inválido",
            "content": {
                "application/json": {
                    "example": {"detail": "Token de renovación inválido"}
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al cerrar sesión"}
                }
            }
        }
    }
)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """
    ## Cerrar sesión (dispositivo actual)
    
    Cierra la sesión del usuario en el dispositivo actual revocando únicamente
    el refresh token proporcionado. Esto permite mantener activas las sesiones
    en otros dispositivos.
    
    ### Parámetros del cuerpo
    - **refresh_token**: Token de renovación que se desea revocar
    
    ### Comportamiento
    - Revoca el refresh token específico proporcionado
    - Mantiene activos otros refresh tokens del mismo usuario
    - Permite logout selectivo por dispositivo
    - No afecta sesiones en otros dispositivos/aplicaciones
    
    ### Diferencia con /logout-all
    - **logout**: Cierra sesión solo en el dispositivo actual
    - **logout-all**: Cierra sesión en todos los dispositivos
    
    ### Casos de uso
    - Logout normal desde una aplicación
    - Cerrar sesión en dispositivo público
    - Gestión granular de sesiones por dispositivo
    - Logout al cambiar de cuenta en la misma app
    
    ### Efecto en tokens
    - **Access token**: Sigue siendo válido hasta su expiración natural
    - **Refresh token**: Se revoca inmediatamente y no puede usarse más
    - **Otros refresh tokens**: No se ven afectados
    
    ### Flujo recomendado
    1. Usuario solicita cerrar sesión
    2. Cliente envía refresh token al endpoint
    3. Servidor revoca el token específico
    4. Cliente elimina tokens almacenados localmente
    5. Redirigir a pantalla de login
    
    ### 🔒 Nota de seguridad
    Después del logout, el cliente debe eliminar tanto el access_token
    como el refresh_token de su almacenamiento local para completar
    el proceso de cierre de sesión.
    """
    try:
        success = auth_service.revoke_refresh_token(request.refresh_token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de renovación inválido"
            )
        return {"message": "Sesión cerrada exitosamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        )

@router.post(
    "/logout-all",
    summary="Cerrar sesión en todos los dispositivos",
    description="Cierra la sesión del usuario en todos los dispositivos revocando todos sus refresh tokens",
    responses={
        200: {
            "description": "Sesión cerrada en todos los dispositivos",
            "content": {
                "application/json": {
                    "example": {"message": "Sesión cerrada en todos los dispositivos. Tokens revocados: 3"}
                }
            }
        },
        401: {
            "description": "Token de autenticación inválido",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudieron validar las credenciales"}
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al cerrar sesión"}
                }
            }
        }
    }
)
async def logout_all(
    current_user: dict = Depends(get_current_user)
):
    """
    ## Cerrar sesión en todos los dispositivos
    
    Cierra la sesión del usuario en todos sus dispositivos revocando todos
    los refresh tokens asociados a su cuenta. Requiere autenticación JWT válida.
    
    ### Autenticación requerida
    Este endpoint requiere un access token válido en el header:
    ```
    Authorization: Bearer {access_token}
    ```
    
    ### Comportamiento
    - Identifica al usuario a través del access token
    - Revoca TODOS los refresh tokens del usuario
    - Fuerza logout en todos los dispositivos/aplicaciones
    - Proporciona estadísticas de tokens revocados
    
    ### Diferencia con /logout
    - **logout**: Cierra sesión solo en el dispositivo actual
    - **logout-all**: Cierra sesión en TODOS los dispositivos
    
    ### Casos de uso críticos
    - **Seguridad comprometida**: Cuando se sospecha acceso no autorizado
    - **Pérdida de dispositivo**: Teléfono o laptop perdidos/robados
    - **Cambio de contraseña**: Forzar reautenticación en todos lados
    - **Empleado despedido**: Revocación inmediata de acceso
    - **Configuración de privacidad**: Control total sobre sesiones activas
    
    ### Efecto en todos los dispositivos
    Después de este endpoint, TODOS los dispositivos del usuario:
    - No podrán renovar sus access tokens
    - Serán redirigidos a login cuando el access token expire
    - Necesitarán reautenticarse completamente
    
    ### Respuesta
    La respuesta incluye:
    - **message**: Confirmación de la operación
    - **Número de tokens revocados**: Para auditoria y confirmación
    
    ### Flujo de emergencia recomendado
    1. Usuario detecta actividad sospechosa
    2. Llama a este endpoint desde un dispositivo seguro
    3. Todos los refresh tokens se revocan instantáneamente
    4. Cambia contraseña (recomendado)
    5. Re-login desde dispositivos autorizados
    
    ### ⚠️ Importante
    - **No hay vuelta atrás**: Una vez ejecutado, TODOS los dispositivos perderán acceso
    - **Impacto inmediato**: Los refresh tokens se invalidan al instante
    - **Reautenticación necesaria**: El usuario debe hacer login nuevamente en cada dispositivo
    
    ### 🔒 Seguridad
    Este endpoint es especialmente útil para respuesta a incidentes de seguridad
    y debería estar prominentemente disponible en la configuración de seguridad
    de la cuenta del usuario.
    """
    try:
        auth_service = AuthService()
        success = auth_service.revoke_all_refresh_tokens(current_user["correo_electronico"])
        return {"message": f"Sesión cerrada en todos los dispositivos. Tokens revocados: {success}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        ) 