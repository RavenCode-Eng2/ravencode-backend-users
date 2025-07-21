from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random
import string
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.services.student import StudentService
from app.services.admin import AdminService
from app.services.user import UserService
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.DB.database import get_database
from app.models.auth import Token, RefreshTokenData
from app.models.user import Student, Admin, User, UserRole

class AuthService:
    """
    Service class for handling authentication and password recovery operations.
    """
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.student_service = StudentService()
        self.admin_service = AdminService()
        self.user_service = UserService()
        self.db = get_database()
        if self.db is None:
            raise Exception("Could not connect to the database")
        self.recovery_codes = self.db["recovery_codes"]
        self.refresh_tokens = self.db["refresh_tokens"]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Generate a password hash.
        """
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token using RS256 algorithm with private key.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.PRIVATE_KEY, 
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            print(f"Error creating JWT token: {str(e)}")
            raise

    def create_refresh_token(self) -> str:
        """
        Create a secure refresh token.
        """
        return secrets.token_urlsafe(32)

    def store_refresh_token(self, user_email: str, refresh_token: str) -> None:
        """
        Store refresh token in database.
        """
        refresh_data = RefreshTokenData(
            user_email=user_email,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),  # 7 days
            created_at=datetime.utcnow()
        )
        
        # Remove old refresh tokens for this user
        self.refresh_tokens.delete_many({"user_email": user_email})
        
        # Store new refresh token
        self.refresh_tokens.insert_one(refresh_data.model_dump())

    def verify_refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        Verify refresh token and return user email if valid.
        """
        token_data = self.refresh_tokens.find_one({
            "refresh_token": refresh_token,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not token_data:
            return None
        
        # Update last used timestamp
        self.refresh_tokens.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"last_used": datetime.utcnow()}}
        )
        
        return token_data["user_email"]

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        """
        result = self.refresh_tokens.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    def revoke_all_refresh_tokens(self, user_email: str) -> bool:
        """
        Revoke all refresh tokens for a user.
        """
        result = self.refresh_tokens.update_many(
            {"user_email": user_email},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    def authenticate_user(self, email: str, password: str) -> Optional[Token]:
        """
        Authenticate any user (student or admin) and return tokens if successful.
        """
        user = self.user_service.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user["contrasena"]):
            return None
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": email, "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = self.create_refresh_token()
        self.store_refresh_token(email, refresh_token)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )

    def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        """
        Create new access token using refresh token.
        """
        user_email = self.verify_refresh_token(refresh_token)
        if not user_email:
            return None
        
        # Get user data
        user = self.user_service.get_user_by_email(user_email)
        if not user:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user_email, "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token (rotate refresh tokens for security)
        new_refresh_token = self.create_refresh_token()
        
        # Revoke old refresh token
        self.revoke_refresh_token(refresh_token)
        
        # Store new refresh token
        self.store_refresh_token(user_email, new_refresh_token)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    # Keep the old method for backward compatibility
    def authenticate_student(self, email: str, password: str) -> Optional[Token]:
        """
        Authenticate a student and return an access token if successful.
        """
        user = self.student_service.get_student_by_email(email)
        if not user:
            return None
        return self.authenticate_user(email, password)

    def authenticate_admin(self, email: str, password: str) -> Optional[Token]:
        """
        Authenticate an admin and return an access token if successful.
        """
        user = self.admin_service.get_admin_by_email(email)
        if not user:
            return None
        return self.authenticate_user(email, password)

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
        Send a recovery code to the user's email.
        
        Args:
            email: The user's email
            code: The recovery code to send
        """
        if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, 
                   settings.SMTP_PASSWORD, settings.EMAILS_FROM_EMAIL]):
            raise ValueError("SMTP settings are not properly configured")

        # Create the message
        message = MIMEMultipart('alternative')
        message["From"] = f"RavenCode Support <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = email
        message["Subject"] = "Código de Recuperación de Contraseña - RavenCode"

        # Plain text version
        text = f"""
Hola,

Has solicitado recuperar tu contraseña en RavenCode. 

Tu código de recuperación es: {code}

Este código expirará en 15 minutos.

Si no solicitaste este código, por favor ignora este mensaje.

Saludos,
RavenCode Support
"""

        # HTML version
        html = f"""
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .code {{
            background-color: #f5f5f5;
            padding: 15px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 5px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eeeeee;
            font-size: 14px;
            color: #666666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Recuperación de Contraseña</h2>
        </div>
        
        <p>Hola,</p>
        
        <p>Has solicitado recuperar tu contraseña en <strong>RavenCode</strong>.</p>
        
        <p>Tu código de recuperación es:</p>
        
        <div class="code">
            {code}
        </div>
        
        <p><strong>Este código expirará en 15 minutos.</strong></p>
        
        <p>Si no solicitaste este código, por favor ignora este mensaje.</p>
        
        <div class="footer">
            <p>Saludos,<br>
            RavenCode Support</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Attach both versions
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        try:
            # Connect to SMTP server
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                # Login
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                # Send email
                server.send_message(message)
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise Exception("Failed to send recovery email")

    def update_user_password(self, email: str, new_password: str) -> bool:
        """
        Update any user's password (student or admin).
        
        Args:
            email: The user's email
            new_password: The new password to set
            
        Returns:
            bool: True if the password was updated successfully
        """
        try:
            # First check if user exists
            user = self.user_service.get_user_by_email(email)
            print(f"DEBUG: Looking up user with email: {email}")
            print(f"DEBUG: User lookup result: {user}")
            
            if not user:
                print(f"DEBUG: No user found with email: {email}")
                return False
            
            # Hash the new password
            hashed_password = self.get_password_hash(new_password)
            print("DEBUG: Password hashed successfully")
            
            # Update the password in the database
            result = self.user_service.collection.update_one(
                {"correo_electronico": email},
                {"$set": {"contrasena": hashed_password}}
            )
            
            print(f"DEBUG: Password update result - matched_count: {result.matched_count}, modified_count: {result.modified_count}")
            
            return result.modified_count > 0
        except Exception as e:
            print(f"DEBUG: Error updating password: {str(e)}")
            return False

    # Keep the old method for backward compatibility but make it use the new one
    def update_student_password(self, email: str, new_password: str) -> bool:
        """
        Update a student's password.
        This method is kept for backward compatibility and now uses update_user_password.
        
        Args:
            email: The student's email
            new_password: The new password to set
            
        Returns:
            bool: True if the password was updated successfully
        """
        return self.update_user_password(email, new_password) 