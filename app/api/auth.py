from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any
from pydantic import BaseModel, EmailStr
from app.services.auth import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

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
    return {
        "access_token": auth_result["access_token"],
        "token_type": auth_result["token_type"]
    }

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