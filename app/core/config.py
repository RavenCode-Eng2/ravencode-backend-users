from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings.
    """
    # Database settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ravencode_users")

    # JWT settings
    ALGORITHM: str = os.getenv("ALGORITHM", "RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # RSA Keys - Support both direct env vars and file paths
    PRIVATE_KEY_PATH: Optional[str] = os.getenv("PRIVATE_KEY_PATH")
    PUBLIC_KEY_PATH: Optional[str] = os.getenv("PUBLIC_KEY_PATH")
    PRIVATE_KEY_CONTENT: Optional[str] = os.getenv("PRIVATE_KEY_CONTENT")
    PUBLIC_KEY_CONTENT: Optional[str] = os.getenv("PUBLIC_KEY_CONTENT")
    
    @property
    def PRIVATE_KEY(self) -> str:
        # First try direct environment variable
        if self.PRIVATE_KEY_CONTENT:
            return self.PRIVATE_KEY_CONTENT
        
        # Fallback to file path
        if self.PRIVATE_KEY_PATH:
            try:
                with open(self.PRIVATE_KEY_PATH, "r") as f:
                    return f.read()
            except FileNotFoundError:
                raise ValueError(f"Private key file not found at {self.PRIVATE_KEY_PATH}")
        
        # Default fallback for development
        default_path = "app/keys/private_key.pem"
        if os.path.exists(default_path):
            with open(default_path, "r") as f:
                return f.read()
        
        raise ValueError("No private key found. Set PRIVATE_KEY_CONTENT or PRIVATE_KEY_PATH environment variable.")
    
    @property
    def PUBLIC_KEY(self) -> str:
        # First try direct environment variable
        if self.PUBLIC_KEY_CONTENT:
            return self.PUBLIC_KEY_CONTENT
        
        # Fallback to file path
        if self.PUBLIC_KEY_PATH:
            try:
                with open(self.PUBLIC_KEY_PATH, "r") as f:
                    return f.read()
            except FileNotFoundError:
                raise ValueError(f"Public key file not found at {self.PUBLIC_KEY_PATH}")
        
        # Default fallback for development
        default_path = "app/keys/public_key.pem"
        if os.path.exists(default_path):
            with open(default_path, "r") as f:
                return f.read()
        
        raise ValueError("No public key found. Set PUBLIC_KEY_CONTENT or PUBLIC_KEY_PATH environment variable.")

    # Email settings
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "RavenCode Support")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 