from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any
from pydantic import BaseModel, EmailStr
from app.services.auth import AuthService
from app.models.auth import Token
from app.models.student import Student
from datetime import date
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    fecha_de_nacimiento: date
    institucion_educativa: str
    grado_academico: str
    foto_de_perfil: str | None = None

class TokenData(BaseModel):
    email: str | None = None

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class PasswordRecoveryVerify(BaseModel):
    email: EmailStr
    code: str
    new_password: str

def get_auth_service():
    """Dependency injector for the AuthService."""
    return AuthService()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Get the current user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = auth_service.student_service.get_student_by_email(email)
    if user is None:
        raise credentials_exception
    
    # Remove password from user data
    user.pop("Contrasena", None)
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    auth_result = auth_service.authenticate_student(form_data.username, form_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_result

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login endpoint that accepts email and password in JSON format.
    """
    auth_result = auth_service.authenticate_student(login_data.email, login_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_result

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new student with basic details.
    The password will be automatically hashed before storage.
    """
    try:
        # Create student model with hashed password
        student = Student(
            Nombre=register_data.nombre,
            Correo_electronico=register_data.email,
            Contrasena=auth_service.get_password_hash(register_data.password),
            Fecha_de_nacimiento=register_data.fecha_de_nacimiento,
            Institucion_educativa=register_data.institucion_educativa,
            Grado_academico=register_data.grado_academico,
            Foto_de_perfil=register_data.foto_de_perfil
        )
        
        # Create the student in the database
        created_student = auth_service.student_service.create_student(student)
        
        # Remove password from response
        created_student.pop("Contrasena", None)
        
        return {
            "message": "Student registered successfully",
            "student": created_student
        }
    except Exception as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/recovery/request", status_code=status.HTTP_200_OK)
async def request_password_recovery(
    request: PasswordRecoveryRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request a password recovery code to be sent to the student's email.
    """
    try:
        # Check if student exists
        student = auth_service.student_service.get_student_by_email(request.email)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

        # Generate and send recovery code
        code = auth_service.generate_recovery_code(request.email)
        auth_service.send_recovery_email(request.email, code)

        return {"message": "Recovery code sent to your email"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/recovery/verify", status_code=status.HTTP_200_OK)
async def verify_recovery_code(
    request: PasswordRecoveryVerify,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify recovery code and update password.
    """
    try:
        # Verify the code
        if not auth_service.verify_recovery_code(request.email, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired recovery code"
            )

        # Update the password
        if not auth_service.update_student_password(request.email, request.new_password):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        # Mark the code as used
        auth_service.mark_recovery_code_used(request.email, request.code)

        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 