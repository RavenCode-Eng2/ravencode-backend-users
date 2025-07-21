from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Union
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.student import StudentService
from app.api.auth import get_auth_service, get_current_user
from app.models.user import User, Student, Admin, UserUpdate, StudentUpdate, AdminUpdate, UserRole
import datetime

router = APIRouter()

def get_user_service():
    """
    Inyector de dependencias para UserService.
    Retorna una instancia del servicio para interactuar con la base de datos.
    """
    return UserService()

def get_student_service():
    """
    Inyector de dependencias para StudentService.
    Retorna una instancia del servicio para interactuar con la base de datos.
    """
    return StudentService()

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency para verificar que el usuario actual sea administrador.
    Retorna la información del usuario si es admin, sino lanza HTTPException.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador para realizar esta operación."
        )
    return current_user

@router.get(
    "/me", 
    response_model=Dict[str, Any],
    summary="Obtener perfil del usuario actual",
    description="Obtiene la información completa del perfil del usuario autenticado",
    responses={
        200: {
            "description": "Información del usuario obtenida exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "estudiante": {
                            "summary": "Respuesta para estudiante",
                            "value": {
                                "nombre": "Ana María García",
                                "correo_electronico": "ana.garcia@universidad.edu",
                                "fecha_de_nacimiento": "1998-09-12",
                                "foto_de_perfil": "https://ejemplo.com/ana-perfil.jpg",
                                "institucion_educativa": "Universidad de Ciencias Aplicadas",
                                "grado_academico": "Licenciatura en Ingeniería de Software",
                                "role": "student",
                                "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                            }
                        },
                        "administrador": {
                            "summary": "Respuesta para administrador",
                            "value": {
                                "nombre": "Dr. Roberto Martínez",
                                "correo_electronico": "roberto.martinez@admin.ravencode.com",
                                "foto_de_perfil": "https://ejemplo.com/roberto-perfil.jpg",
                                "departamento": "Tecnología y Desarrollo",
                                "nivel_acceso": "super_admin",
                                "role": "admin",
                                "_id": "60c72b2f9b1e8b3f8c8e4c2c"
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Token de autenticación inválido o expirado",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudieron validar las credenciales"}
                }
            }
        }
    }
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    ## Obtener información del perfil del usuario actual
    
    Retorna la información completa del perfil del usuario que está actualmente autenticado,
    basándose en el token JWT proporcionado en el header de autorización.
    
    ### Autenticación requerida
    Este endpoint requiere autenticación JWT. Incluir en el header:
    ```
    Authorization: Bearer {access_token}
    ```
    
    ### 🔒 Nota de seguridad
    Este endpoint solo retorna información del usuario propietario del token.
    No es posible acceder a información de otros usuarios a través de este endpoint.
    """
    return current_user

@router.put(
    "/me",
    response_model=Dict[str, Any],
    summary="Actualizar perfil del usuario actual",
    description="Permite al usuario autenticado actualizar su propia información de perfil",
    responses={
        200: {
            "description": "Perfil actualizado exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "estudiante_actualizado": {
                            "summary": "Perfil de estudiante actualizado",
                            "value": {
                                "message": "Perfil actualizado exitosamente",
                                "user": {
                                    "nombre": "María González López",
                                    "correo_electronico": "maria.gonzalez@universidad.edu",
                                    "fecha_de_nacimiento": "1999-03-22",
                                    "foto_de_perfil": "https://ejemplo.com/nuevo-perfil.jpg",
                                    "institucion_educativa": "Universidad Tecnológica Nacional",
                                    "grado_academico": "Ingeniería en Sistemas",
                                    "role": "student",
                                    "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                                }
                            }
                        },
                        "admin_actualizado": {
                            "summary": "Perfil de admin actualizado",
                            "value": {
                                "message": "Perfil actualizado exitosamente",
                                "user": {
                                    "nombre": "Dr. Roberto Martínez",
                                    "correo_electronico": "roberto.martinez@admin.ravencode.com",
                                    "foto_de_perfil": "https://ejemplo.com/nuevo-perfil.jpg",
                                    "departamento": "Tecnología y Desarrollo",
                                    "nivel_acceso": "super_admin",
                                    "role": "admin",
                                    "_id": "60c72b2f9b1e8b3f8c8e4c2c"
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Error de validación o datos inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al actualizar perfil"}
                }
            }
        },
        401: {
            "description": "Token inválido o no proporcionado",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudieron validar las credenciales"}
                }
            }
        }
    }
)
async def update_me(
    update_data: Union[StudentUpdate, AdminUpdate, UserUpdate],
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    ## Actualizar perfil del usuario actual
    
    Permite al usuario autenticado actualizar su propia información de perfil.
    Solo se pueden actualizar los campos proporcionados (actualización parcial).
    
    ### Autenticación requerida
    Este endpoint requiere autenticación JWT. Incluir en el header:
    ```
    Authorization: Bearer {access_token}
    ```
    
    ### Campos actualizables para estudiantes:
    - **nombre**: Nombre completo del usuario
    - **correo_electronico**: Dirección de email (debe ser única)
    - **contrasena**: Nueva contraseña (se cifra automáticamente)
    - **foto_de_perfil**: URL de la imagen de perfil (usar `null` para eliminar)
    - **fecha_de_nacimiento**: Fecha de nacimiento
    - **institucion_educativa**: Institución educativa
    - **grado_academico**: Grado académico
    
    ### Campos actualizables para administradores:
    - **nombre**: Nombre completo del usuario
    - **correo_electronico**: Dirección de email (debe ser única)
    - **contrasena**: Nueva contraseña (se cifra automáticamente)
    - **foto_de_perfil**: URL de la imagen de perfil (usar `null` para eliminar)
    - **departamento**: Departamento que administra
    - **nivel_acceso**: Nivel de acceso del administrador
    
    ### Comportamiento
    - Solo se actualizan los campos proporcionados
    - Los campos no incluidos mantienen su valor actual
    - La contraseña se cifra automáticamente si se proporciona
    - El email debe ser único si se cambia
    - No se puede cambiar el rol del usuario
    
    ### 🔒 Seguridad
    - Cada usuario solo puede actualizar su propio perfil
    - Las contraseñas se cifran antes de almacenarse
    - Se valida la autenticidad del token JWT
    """
    try:
        user_email = current_user.get("correo_electronico")
        if not user_email:
            raise HTTPException(
                status_code=400,
                detail="No se pudo obtener el email del usuario actual"
            )
        
        # Convert update data to dict, including explicitly set None values
        # Use exclude_unset to only include fields that were actually provided
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Get all fields that were explicitly set (including None values)
        fields_set = update_data.model_fields_set if hasattr(update_data, 'model_fields_set') else set()
        
        # For fields that were explicitly set to None, add them to update_dict
        for field_name in fields_set:
            field_value = getattr(update_data, field_name, None)
            if field_value is None:
                update_dict[field_name] = None
        
        # Handle date conversion for students
        if "fecha_de_nacimiento" in update_dict:
            if isinstance(update_dict["fecha_de_nacimiento"], datetime.date):
                update_dict["fecha_de_nacimiento"] = update_dict["fecha_de_nacimiento"].isoformat()
        
        # Hash password if provided
        if "contrasena" in update_dict:
            from app.services.auth import AuthService
            auth_service = AuthService()
            update_dict["contrasena"] = auth_service.get_password_hash(update_dict["contrasena"])
        
        # Perform the update
        if update_dict:  # Only update if there's actual data
            result = user_service.update_user(user_email, update_dict)
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Usuario no encontrado"
                )
        
        # Return updated user information
        updated_user = user_service.get_user_by_email(user_email)
        
        # Remove password from response
        if updated_user and "contrasena" in updated_user:
            del updated_user["contrasena"]
        
        return {
            "message": "Perfil actualizado exitosamente",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al actualizar perfil: {str(e)}"
        )

@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo usuario (Solo Administradores)",
    description="Crea un nuevo usuario en la base de datos (estudiante o administrador). Requiere permisos de administrador.",
    responses={
        201: {
            "description": "Usuario creado exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "estudiante_creado": {
                            "summary": "Estudiante creado por admin",
                            "value": {
                                "message": "Usuario creado exitosamente",
                                "user": {
                                    "nombre": "María González López",
                                    "correo_electronico": "maria.gonzalez@universidad.edu",
                                    "fecha_de_nacimiento": "1999-03-22",
                                    "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                                    "institucion_educativa": "Universidad Tecnológica Nacional",
                                    "grado_academico": "Ingeniería en Sistemas",
                                    "role": "student",
                                    "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                                }
                            }
                        },
                        "administrador_creado": {
                            "summary": "Administrador creado por admin",
                            "value": {
                                "message": "Usuario creado exitosamente",
                                "user": {
                                    "nombre": "Dr. Roberto Martínez",
                                    "correo_electronico": "roberto.martinez@admin.ravencode.com",
                                    "foto_de_perfil": "https://ejemplo.com/roberto-perfil.jpg",
                                    "departamento": "Tecnología y Desarrollo",
                                    "nivel_acceso": "super_admin",
                                    "role": "admin",
                                    "_id": "60c72b2f9b1e8b3f8c8e4c2c"
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "El usuario ya existe o datos inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Un usuario con este email ya existe"}
                }
            }
        },
        401: {
            "description": "Token de autenticación inválido o expirado",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudieron validar las credenciales"}
                }
            }
        },
        403: {
            "description": "Permisos insuficientes - Se requiere rol de administrador",
            "content": {
                "application/json": {
                    "example": {"detail": "Acceso denegado. Se requieren permisos de administrador para realizar esta operación."}
                }
            }
        }
    }
)
async def create_user(
    user: Union[Student, Admin], 
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    """
    ## Crear nuevo usuario (Solo Administradores)
    
    Crea un nuevo registro de usuario en la base de datos. Puede ser estudiante o administrador
    según los campos proporcionados en el cuerpo de la petición.
    
    ### 🔐 Autenticación requerida
    Este endpoint requiere autenticación JWT con rol de **administrador**. Incluir en el header:
    ```
    Authorization: Bearer {admin_access_token}
    ```
    
    ### Tipos de usuario que se pueden crear
    - **Estudiante**: Incluye fecha_de_nacimiento, institucion_educativa, grado_academico
    - **Administrador**: Incluye departamento, nivel_acceso
    
    ### Casos de uso
    - **Administradores creando estudiantes**: Registro masivo de estudiantes
    - **Administradores creando otros admins**: Gestión de equipo administrativo
    - **Onboarding de usuarios**: Creación de cuentas por parte del equipo admin
    
    ### Validaciones automáticas
    - El email debe ser único en el sistema
    - El formato del email debe ser válido
    - La contraseña se cifra automáticamente
    - Solo usuarios con rol 'admin' pueden acceder a este endpoint
    
    ### 🔒 Permisos
    - **Requerido**: Rol de administrador en el token JWT
    - **Permitido**: Crear tanto estudiantes como administradores
    - **Restricción**: Usuarios estudiantes no pueden acceder a este endpoint
    """
    try:
        # Use StudentService for students (it has proper date handling)
        if hasattr(user, 'fecha_de_nacimiento') and user.role == UserRole.STUDENT:
            student_service = get_student_service()
            created_user = student_service.create_student(user)
        else:
            # For admins, use the regular UserService
            created_user = user_service.create_user(user)
        
        return {
            "message": "Usuario creado exitosamente",
            "user": created_user
        }
    except Exception as e:
        if "already exists" in str(e) or "ya existe" in str(e):
            raise HTTPException(
                status_code=400, 
                detail="Un usuario con este email ya existe"
            )
        raise HTTPException(
            status_code=400, 
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.get(
    "/{user_email}",
    response_model=Dict[str, Any],
    summary="Obtener usuario por email",
    description="Busca y retorna la información de un usuario específico usando su dirección de email",
    responses={
        200: {
            "description": "Usuario encontrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "nombre": "María González López",
                        "correo_electronico": "maria.gonzalez@universidad.edu",
                        "fecha_de_nacimiento": "1999-03-22",
                        "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                        "institucion_educativa": "Universidad Tecnológica Nacional",
                        "grado_academico": "Ingeniería en Sistemas",
                        "role": "student",
                        "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                    }
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
async def get_user(
    user_email: str, 
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    """
    ## Obtener usuario por email
    
    Busca y retorna toda la información de un usuario específico usando su dirección de email 
    como identificador único.
    
    ### Parámetros de ruta
    - **user_email**: Dirección de correo electrónico del usuario (debe ser exacta)
    
    ### Información retornada
    Incluye todos los campos del perfil del usuario (sin contraseña):
    - Información personal (nombre, email, foto de perfil)
    - Información específica según el rol (estudiante o administrador)
    - Rol del usuario y ID único en la base de datos
    """
    try:
        user = user_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail="Usuario no encontrado"
            )
        
        # Remove password from response
        if user and "contrasena" in user:
            del user["contrasena"]
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error al buscar usuario: {str(e)}"
        )

@router.put(
    "/{user_email}",
    response_model=Dict[str, Any],
    summary="Actualizar información del usuario",
    description="Actualiza parcial o completamente la información de un usuario específico",
    responses={
        200: {
            "description": "Usuario actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Usuario actualizado exitosamente",
                        "user": {
                            "nombre": "María González López",
                            "correo_electronico": "maria.gonzalez@universidad.edu",
                            "fecha_de_nacimiento": "1999-03-22",
                            "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                            "institucion_educativa": "Universidad Tecnológica Nacional",
                            "grado_academico": "Ingeniería en Sistemas",
                            "role": "student",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        }
                    }
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
        },
        400: {
            "description": "Error de validación o datos inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al actualizar usuario"}
                }
            }
        }
    }
)
async def update_user(
    user_email: str, 
    update_data: Union[StudentUpdate, AdminUpdate, UserUpdate],
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    """
    ## Actualizar información del usuario
    
    Actualiza parcial o completamente la información de un usuario específico usando su email.
    
    ### Parámetros de ruta
    - **user_email**: Dirección de correo electrónico del usuario a actualizar
    
    ### Cuerpo de la petición
    Acepta cualquier combinación de campos válidos para el tipo de usuario:
    
    **Para estudiantes:**
    - nombre, correo_electronico, contrasena, foto_de_perfil
    - fecha_de_nacimiento, institucion_educativa, grado_academico
    
    **Para administradores:**
    - nombre, correo_electronico, contrasena, foto_de_perfil
    - departamento, nivel_acceso
    
    ### Comportamiento
    - Solo se actualizan los campos proporcionados (actualización parcial)
    - Los campos no incluidos mantienen su valor actual
    - Valida que el usuario exista antes de actualizar
    - Retorna la información actualizada del usuario (sin contraseña)
    
    ### Casos de uso
    - Actualizar perfil de usuario desde el frontend
    - Modificar información específica sin afectar otros campos
    - Cambiar contraseña de usuario
    - Actualizar foto de perfil
    """
    try:
        # First verify the user exists
        existing_user = user_service.get_user_by_email(user_email)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Convert update data to dict, including explicitly set None values
        # Use exclude_unset to only include fields that were actually provided
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Get all fields that were explicitly set (including None values)
        fields_set = update_data.model_fields_set if hasattr(update_data, 'model_fields_set') else set()
        
        # For fields that were explicitly set to None, add them to update_dict
        for field_name in fields_set:
            field_value = getattr(update_data, field_name, None)
            if field_value is None:
                update_dict[field_name] = None
        
        # Handle date conversion for students
        if "fecha_de_nacimiento" in update_dict:
            if isinstance(update_dict["fecha_de_nacimiento"], datetime.date):
                update_dict["fecha_de_nacimiento"] = update_dict["fecha_de_nacimiento"].isoformat()
        
        # Perform the update
        if update_dict:  # Only update if there's actual data
            result = user_service.update_user(user_email, update_dict)
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Usuario no encontrado"
                )
        
        # Return updated user information
        updated_user = user_service.get_user_by_email(user_email)
        
        # Remove password from response
        if updated_user and "contrasena" in updated_user:
            del updated_user["contrasena"]
        
        return {
            "message": "Usuario actualizado exitosamente",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al actualizar usuario: {str(e)}"
        )

@router.delete(
    "/{user_email}",
    response_model=Dict[str, Any],
    summary="Eliminar usuario",
    description="Elimina permanentemente un usuario del sistema usando su email",
    responses={
        200: {
            "description": "Usuario eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Usuario eliminado exitosamente",
                        "email": "usuario@ejemplo.com"
                    }
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
async def delete_user(
    user_email: str, 
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    """
    ## Eliminar usuario
    
    Elimina permanentemente un usuario del sistema usando su dirección de email.
    
    ### ⚠️ Advertencia de seguridad
    Esta operación es **IRREVERSIBLE**. Una vez eliminado, el usuario y toda su información
    se perderán permanentemente.
    
    ### Parámetros de ruta
    - **user_email**: Dirección de correo electrónico del usuario a eliminar
    
    ### Comportamiento
    - Busca el usuario por email
    - Elimina completamente el registro de la base de datos
    - Retorna confirmación de eliminación
    
    ### Casos de uso
    - Eliminar cuentas de usuarios inactivos
    - Cumplir con solicitudes de eliminación de datos (GDPR)
    - Limpiar cuentas de prueba o duplicadas
    """
    try:
        success = user_service.delete_user_by_email(user_email)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        return {
            "message": "Usuario eliminado exitosamente",
            "email": user_email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al eliminar usuario: {str(e)}"
        )

@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Listar todos los usuarios",
    description="Obtiene una lista de todos los usuarios registrados en el sistema",
    responses={
        200: {
            "description": "Lista de usuarios obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "nombre": "María González López",
                            "correo_electronico": "maria.gonzalez@universidad.edu",
                            "fecha_de_nacimiento": "1999-03-22",
                            "foto_de_perfil": "https://ejemplo.com/perfil.jpg",
                            "institucion_educativa": "Universidad Tecnológica Nacional",
                            "grado_academico": "Ingeniería en Sistemas",
                            "role": "student",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        },
                        {
                            "nombre": "Dr. Roberto Martínez",
                            "correo_electronico": "roberto.martinez@admin.ravencode.com",
                            "foto_de_perfil": "https://ejemplo.com/roberto-perfil.jpg",
                            "departamento": "Tecnología y Desarrollo",
                            "nivel_acceso": "super_admin",
                            "role": "admin",
                            "_id": "60c72b2f9b1e8b3f8c8e4c2c"
                        }
                    ]
                }
            }
        }
    }
)
async def list_users(
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    """
    ## Listar todos los usuarios
    
    Obtiene una lista completa de todos los usuarios registrados en el sistema,
    incluyendo tanto estudiantes como administradores.
    
    ### Información retornada
    Lista de usuarios con toda su información (sin contraseñas):
    - Información personal completa
    - Rol del usuario (student/admin)
    - Campos específicos según el tipo de usuario
    - ID único de cada usuario
    
    ### Rendimiento
    Este endpoint puede retornar grandes cantidades de datos si hay muchos usuarios.
    En el futuro se implementará paginación para mejorar el rendimiento.
    
    ### Casos de uso
    - Administración de usuarios desde panel de control
    - Generación de reportes de usuarios
    - Búsqueda y filtrado de usuarios
    """
    try:
        users = user_service.list_users()
        
        # Remove passwords from all users
        for user in users:
            if "contrasena" in user:
                del user["contrasena"]
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al listar usuarios: {str(e)}"
        ) 