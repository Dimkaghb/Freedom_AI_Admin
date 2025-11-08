import os
from typing import List
from datetime import timedelta
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_TITLE: str = "FreedomAIAdmin API"
    API_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")  # Default to all interfaces for Docker, can be overridden via env
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:9002",  # Added missing port
        "http://127.0.0.1:3000",
        "http://frontend:9002",  # Docker container name
        "http://choco-frontend:9002",  # Docker container name from compose
        "http://freedom-analysis.chocodev.kz:9002",  # Production frontend
        "https://freedom-analysis.chocodev.kz:9002",  # Fixed missing comma
        "*"  # Allow all origins as fallback
    ]
    
    # File Processing Configuration
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        ".csv", ".xlsx", ".xls", ".json", ".txt", ".log"
    ]
    
    
    # AI API Configuration
    # AI_API_URL: str = "https://ai-platform-connect.kassen.space/connect/v1/d82fc727-bb94-4f82-848c-a9be5c779e4a/agent/run"
    
    # Server Timeout Configuration
    UVICORN_TIMEOUT_KEEP_ALIVE: int = 600  # 10 minutes
    UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN: int = 60  # 60 seconds
    REQUEST_TIMEOUT: int = 600  # 10 minutes for long-running operations
    
    # Database Connection Timeout
    MONGODB_CONNECT_TIMEOUT: int = 30000  # 30 seconds
    MONGODB_SERVER_SELECTION_TIMEOUT: int = 30000  # 30 seconds
    
    # Data Processing Configuration
    MAX_SAMPLE_ROWS: int = 1000
    MAX_TEXT_PREVIEW: int = 100000
    
    # Authentication Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "AjR4TrX1Xj0Y-vcXtyyZ_d-wxUUSs5zJtHvkDriR_5g")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh token

    # Registration Link Configuration
    USER_LINK_EXPIRATION_HOURS: int = 24  # Registration link expires in 24 hours
    USER_LINK_EXPIRATION_DELTA: timedelta = timedelta(hours=24)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "\hoco")
    USERS_COLLECTION: str = os.getenv("USERS_COLLECTION", "Choco_users")
    HOLDINGS_COLLECTION: str = os.getenv("HOLDINGS_COLLECTION", "holdings")
    COMPANIES_COLLECTION: str = os.getenv("COMPANIES_COLLECTION", "companies")
    DEPARTMENTS_COLLECTION: str = os.getenv("DEPARTMENTS_COLLECTION", "departments")
    FOLDERS_COLLECTION: str = os.getenv("FOLDERS_COLLECTION", "folders")
    USER_LINKS_COLLECTION: str = os.getenv("USER_LINKS_COLLECTION", "user_registration_links")
    PENDING_USERS_COLLECTION: str = os.getenv("PENDING_USERS_COLLECTION", "pending_users")

    #S3 config
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT")
    S3_BUCKET: str = os.getenv("S3_BUCKET")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY")
    S3_REGION: str = os.getenv("S3_REGION")

    # SMTP Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")
    SMTP_SENDER_NAME: str = os.getenv("SMTP_SENDER_NAME", "FreedomAIAdmin")

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()