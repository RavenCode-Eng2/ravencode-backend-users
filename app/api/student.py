from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.user import Student
from app.services.student import StudentService

router = APIRouter()

def get_student_service():
    """
    Inyector de dependencias para StudentService.
    Retorna una instancia del servicio para interactuar con la base de datos.
    """
    return StudentService()

@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo estudiante",
    description="Crea un nuevo estudiante en la base de datos con toda la información personal",
    responses={
        201: {
            "description": "Estudiante creado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Estudiante creado exitosamente",
                        "student": {
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
        400: {
            "description": "El estudiante ya existe o datos inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Un estudiante con este email ya existe"}
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
                                "loc": ["body", "correo_electronico"],
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
async def create_student(student: Student, student_service: StudentService = Depends(get_student_service)):
    """
    ## Crear nuevo estudiante
    
    Crea un nuevo registro de estudiante en la base de datos con toda la información personal.
    
    ### Parámetros requeridos
    - **nombre**: Nombre completo del estudiante
    - **correo_electronico**: Email único del estudiante
    - **contrasena**: Contraseña para la cuenta (se cifra automáticamente)
    - **fecha_de_nacimiento**: Fecha de nacimiento en formato YYYY-MM-DD
    - **institucion_educativa**: Nombre de la institución educativa
    - **grado_academico**: Grado o carrera académica
    
    ### Parámetros opcionales
    - **foto_de_perfil**: URL de la imagen de perfil
    
    ### Validaciones automáticas
    - El email debe ser único en el sistema
    - El formato del email debe ser válido
    - La fecha de nacimiento debe ser válida
    - El rol se asigna automáticamente como "student"
    
    ### Respuesta exitosa
    Retorna la información del estudiante creado (sin la contraseña) junto con un mensaje de confirmación.
    """
    try:
        created_student = student_service.create_student(student)
        return {
            "message": "Estudiante creado exitosamente",
            "student": created_student
        }
    except Exception as e:
        if "already exists" in str(e) or "ya existe" in str(e):
            raise HTTPException(
                status_code=400, 
                detail="Un estudiante con este email ya existe"
            )
        raise HTTPException(
            status_code=400, 
            detail=f"Error al crear estudiante: {str(e)}"
        )

@router.get(
    "/{student_email}",
    response_model=Dict[str, Any],
    summary="Obtener estudiante por email",
    description="Busca y retorna la información de un estudiante específico usando su dirección de email",
    responses={
        200: {
            "description": "Estudiante encontrado exitosamente",
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
            "description": "Estudiante no encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Estudiante no encontrado"}
                }
            }
        },
        400: {
            "description": "Error en la consulta",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al buscar estudiante"}
                }
            }
        }
    }
)
async def get_student(student_email: str, student_service: StudentService = Depends(get_student_service)):
    """
    ## Obtener estudiante por email
    
    Busca y retorna toda la información de un estudiante específico usando su dirección de email como identificador único.
    
    ### Parámetros de ruta
    - **student_email**: Dirección de correo electrónico del estudiante (debe ser exacta)
    
    ### Comportamiento
    - Busca el estudiante en la base de datos usando el email
    - Retorna toda la información del perfil (sin contraseña)
    - Si no encuentra el estudiante, retorna error 404
    
    ### Casos de uso
    - Consultar perfil de estudiante específico
    - Verificar información antes de actualizar
    - Mostrar detalles del estudiante en interfaces de administración
    
    ### Información retornada
    Incluye todos los campos del perfil del estudiante:
    - Información personal (nombre, fecha de nacimiento)
    - Información académica (institución, grado)
    - Información de contacto (email)
    - Metadatos (ID, rol, foto de perfil)
    """
    try:
        student = student_service.get_student_by_email(student_email)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return student
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al buscar estudiante: {str(e)}")

@router.put(
    "/{student_email}", 
    response_model=Dict[str, Any],
    summary="Actualizar información de estudiante",
    description="Actualiza la información de un estudiante existente usando su email como identificador",
    responses={
        200: {
            "description": "Estudiante actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "nombre": "María González López",
                        "correo_electronico": "maria.gonzalez@universidad.edu",
                        "fecha_de_nacimiento": "1999-03-22",
                        "foto_de_perfil": "https://ejemplo.com/nuevo-perfil.jpg",
                        "institucion_educativa": "Universidad Tecnológica Nacional",
                        "grado_academico": "Maestría en Ciencias de la Computación",
                        "role": "student",
                        "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                    }
                }
            }
        },
        404: {
            "description": "Estudiante no encontrado o sin cambios",
            "content": {
                "application/json": {
                    "example": {"detail": "Estudiante no encontrado o no se realizaron cambios"}
                }
            }
        },
        400: {
            "description": "Error en la actualización",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al actualizar estudiante"}
                }
            }
        }
    }
)
async def update_student(
    student_email: str,
    student_data: Student,
    student_service: StudentService = Depends(get_student_service)
):
    """
    ## Actualizar información de estudiante
    
    Actualiza la información de un estudiante existente. Solo se actualizarán los campos proporcionados en el cuerpo de la petición.
    
    ### Parámetros de ruta
    - **student_email**: Email del estudiante a actualizar (identificador único)
    
    ### Parámetros del cuerpo
    Objeto Student con los campos a actualizar:
    - **nombre**: Nuevo nombre completo (opcional)
    - **correo_electronico**: Nuevo email (opcional, debe ser único)
    - **contrasena**: Nueva contraseña (opcional, se cifra automáticamente)
    - **fecha_de_nacimiento**: Nueva fecha de nacimiento (opcional)
    - **institucion_educativa**: Nueva institución (opcional)
    - **grado_academico**: Nuevo grado académico (opcional)
    - **foto_de_perfil**: Nueva URL de foto de perfil (opcional)
    
    ### Comportamiento
    - Solo actualiza los campos que han cambiado
    - Mantiene los valores existentes para campos no especificados
    - Valida que el email siga siendo único si se cambia
    - Cifra automáticamente la contraseña si se proporciona una nueva
    
    ### Validaciones
    - El estudiante debe existir en la base de datos
    - El nuevo email (si se proporciona) debe ser único
    - Los formatos de datos deben ser válidos
    
    ### Respuesta exitosa
    Retorna la información completa del estudiante actualizado.
    """
    try:
        # Convert Student model to dict excluding unset fields
        update_data = student_data.model_dump(exclude_unset=True)
        result = student_service.update_student(student_email, update_data)
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, 
                detail="Estudiante no encontrado o no se realizaron cambios"
            )
        return student_service.get_student_by_email(student_email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar estudiante: {str(e)}")

@router.delete(
    "/{student_email}",
    response_model=Dict[str, str],
    summary="Eliminar estudiante",
    description="Elimina permanentemente un estudiante de la base de datos usando su email",
    responses={
        200: {
            "description": "Estudiante eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {"message": "Estudiante eliminado exitosamente"}
                }
            }
        },
        404: {
            "description": "Estudiante no encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Estudiante no encontrado"}
                }
            }
        },
        400: {
            "description": "Error al eliminar",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al eliminar estudiante"}
                }
            }
        }
    }
)
async def delete_student(student_email: str, student_service: StudentService = Depends(get_student_service)):
    """
    ## Eliminar estudiante
    
    Elimina permanentemente un estudiante de la base de datos. Esta operación no se puede deshacer.
    
    ### Parámetros de ruta
    - **student_email**: Email del estudiante a eliminar (identificador único)
    
    ### Comportamiento
    - Busca el estudiante por email
    - Elimina permanentemente todos sus datos
    - No hay forma de recuperar la información después de la eliminación
    
    ### Consideraciones de seguridad
    - Esta operación es irreversible
    - Se recomienda confirmar la operación antes de ejecutarla
    - Considerar archivar en lugar de eliminar para casos sensibles
    
    ### Casos de uso
    - Cumplimiento con solicitudes de eliminación de datos (GDPR)
    - Limpieza de cuentas inactivas
    - Eliminación por violación de términos de servicio
    
    ### Respuesta exitosa
    Retorna mensaje de confirmación de eliminación exitosa.
    
    ### ⚠️ Advertencia
    Esta operación elimina permanentemente todos los datos del estudiante.
    Asegúrese de que realmente desea proceder antes de llamar este endpoint.
    """
    try:
        student_service.delete_student_by_email(student_email)
        return {"message": "Estudiante eliminado exitosamente"}
    except Exception as e:
        if "not found" in str(e).lower() or "no encontrado" in str(e).lower():
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al eliminar estudiante: {str(e)}")

@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Listar todos los estudiantes",
    description="Obtiene una lista completa de todos los estudiantes registrados en el sistema",
    responses={
        200: {
            "description": "Lista de estudiantes obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "nombre": "María González López",
                            "correo_electronico": "maria.gonzalez@universidad.edu",
                            "fecha_de_nacimiento": "1999-03-22",
                            "foto_de_perfil": "https://ejemplo.com/perfil1.jpg",
                            "institucion_educativa": "Universidad Tecnológica Nacional",
                            "grado_academico": "Ingeniería en Sistemas",
                            "role": "student",
                            "_id": "60c72b2f9b1e8b3f8c8e4b1a"
                        },
                        {
                            "nombre": "Carlos Rodríguez Pérez",
                            "correo_electronico": "carlos.rodriguez@instituto.edu",
                            "fecha_de_nacimiento": "2000-07-15",
                            "foto_de_perfil": "https://ejemplo.com/perfil2.jpg",
                            "institucion_educativa": "Instituto Politécnico Nacional",
                            "grado_academico": "Licenciatura en Matemáticas",
                            "role": "student",
                            "_id": "60c72b2f9b1e8b3f8c8e4b2b"
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Error al obtener la lista",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al obtener lista de estudiantes"}
                }
            }
        }
    }
)
async def list_students(student_service: StudentService = Depends(get_student_service)):
    """
    ## Listar todos los estudiantes
    
    Obtiene una lista completa de todos los estudiantes registrados en el sistema, 
    incluyendo toda su información personal y académica.
    
    ### Comportamiento
    - Retorna todos los estudiantes sin filtros
    - Incluye información completa de cada estudiante (sin contraseñas)
    - Los resultados no están paginados (todos los registros)
    - Ordenamiento por fecha de creación (más recientes primero)
    
    ### Información incluida por estudiante
    - **Datos personales**: nombre, fecha de nacimiento, foto de perfil
    - **Datos académicos**: institución educativa, grado académico
    - **Datos de contacto**: correo electrónico
    - **Metadatos**: ID del sistema, rol de usuario
    
    ### Casos de uso
    - Panel de administración general
    - Reportes y estadísticas
    - Exportación de datos
    - Búsquedas y filtrados en frontend
    
    ### Consideraciones de rendimiento
    - Para sistemas con muchos estudiantes, considerar implementar paginación
    - La respuesta puede ser grande si hay muchos registros
    - Usar cache cuando sea apropiado
    
    ### Respuesta
    Array de objetos Student con toda la información disponible.
    
    ### 📝 Nota
    Este endpoint retorna todos los estudiantes sin paginación. 
    Para sistemas grandes, considere implementar parámetros de paginación y filtrado.
    """
    try:
        return student_service.list_students()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al obtener lista de estudiantes: {str(e)}")