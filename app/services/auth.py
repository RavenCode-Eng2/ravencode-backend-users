from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random
import string
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.services.student import StudentService
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.DB.database import get_database
from app.models.auth import Token, User, TokenData
from app.models.role import Role
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

class AuthService:
    """
    Service class for handling authentication and password recovery operations.
    """
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.student_service = StudentService()
        self.db = get_database()
        if self.db is None:
            raise Exception("Could not connect to the database")
        self.recovery_codes = self.db["recovery_codes"]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Generate a password hash.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            str: The hashed password
        """
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token with role information.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional expiration time delta
            
        Returns:
            str: The encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
        """
        Get the current user from the JWT token.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_data = TokenData(email=email, role=Role(payload.get("role", Role.STUDENT)))
        except JWTError:
            raise credentials_exception
        
        student = self.student_service.get_student_by_email(token_data.email)
        if student is None:
            raise credentials_exception
        
        return User(
            email=student["Correo_electronico"],
            is_active=True,
            role=token_data.role
        )

    def authenticate_student(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a student and return a JWT token.
        
        Args:
            email: The student's email
            password: The student's password
            
        Returns:
            Optional[Dict[str, Any]]: Token object containing access token and type if successful,
                           None if authentication fails
        """
        student = self.student_service.get_student_by_email(email)
        if not student:
            return None
        if not self.verify_password(password, student["Contrasena"]):
            return None
        
        # Determine role (you might want to implement your own logic here)
        role = Role.ADMIN if email.endswith("@admin.com") else Role.STUDENT
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": email, "role": role},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    def generate_recovery_code(self, email: str) -> str:
        """
        Generate a recovery code for password reset.
        
        Args:
            email: The student's email
            
        Returns:
            str: The generated recovery code
        """
        # Generate a 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Store the code in MongoDB with expiration time (15 minutes)
        self.recovery_codes.update_one(
            {"email": email},
            {
                "$set": {
                    "code": code,
                    "expires": datetime.utcnow() + timedelta(minutes=15),
                    "used": False
                }
            },
            upsert=True
        )
        
        return code

    def verify_recovery_code(self, email: str, code: str) -> bool:
        """
        Verify a recovery code.
        
        Args:
            email: The student's email
            code: The recovery code to verify
            
        Returns:
            bool: True if the code is valid and not expired, False otherwise
        """
        recovery_data = self.recovery_codes.find_one({
            "email": email,
            "code": code,
            "used": False,
            "expires": {"$gt": datetime.utcnow()}
        })
        
        return recovery_data is not None

    def mark_recovery_code_used(self, email: str, code: str) -> None:
        """
        Mark a recovery code as used.
        
        Args:
            email: The student's email
            code: The recovery code to mark as used
        """
        self.recovery_codes.update_one(
            {"email": email, "code": code},
            {"$set": {"used": True}}
        )

    def send_recovery_email(self, email: str, code: str) -> None:
        """
        Send a recovery code to the student's email.
        
        Args:
            email: The student's email
            code: The recovery code to send
        """
        if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, 
                   settings.SMTP_PASSWORD, settings.EMAILS_FROM_EMAIL]):
            raise ValueError("SMTP settings are not properly configured")

        # Crear el mensaje
        message = MIMEMultipart()
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = email
        message["Subject"] = "Código de Recuperación de Contraseña"

        # Crear el cuerpo del mensaje
        body = f"""
        Hola,

        Has solicitado recuperar tu contraseña. Tu código de recuperación es:

        {code}

        Este código expirará en 15 minutos.

        Si no solicitaste este código, por favor ignora este mensaje.

        Saludos,
        El equipo de Student Management
        """
        
        message.attach(MIMEText(body, "plain"))

        try:
            # Conectar al servidor SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                # Iniciar sesión
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                # Enviar email
                server.send_message(message)
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise Exception("Failed to send recovery email")

    def update_student_password(self, email: str, new_password: str) -> bool:
        """
        Update a student's password.
        
        Args:
            email: The student's email
            new_password: The new password to set
            
        Returns:
            bool: True if the password was updated successfully
        """
        try:
            # Hash the new password
            hashed_password = self.get_password_hash(new_password)
            
            # Update the password in the database
            result = self.student_service.collection.update_one(
                {"Correo_electronico": email},
                {"$set": {"Contrasena": hashed_password}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating password: {str(e)}")
            return False 