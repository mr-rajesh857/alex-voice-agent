import os
from dotenv import load_dotenv

# Load variables from .env file into environment
load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Alex Chat Agent API")
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database & Redis Cache
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://alex_user:alex_password@localhost:5433/alex_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Gemini / LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Security Secrets (Read directly from .env like process.env in Node)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "alex_jwt_secret_token_signing_key_32bytes")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "alex_db_token_encryption_key_32bytes")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
    
    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    
    # FastMCP Server URLs
    CALENDAR_MCP_URL: str = os.getenv("CALENDAR_MCP_URL", "http://localhost:8001")
    CONTACTS_MCP_URL: str = os.getenv("CONTACTS_MCP_URL", "http://localhost:8002")
    REMINDERS_MCP_URL: str = os.getenv("REMINDERS_MCP_URL", "http://localhost:8003")
    SEARCH_RAG_MCP_URL: str = os.getenv("SEARCH_RAG_MCP_URL", "http://localhost:8004")
    EMAIL_MESSAGING_MCP_URL: str = os.getenv("EMAIL_MESSAGING_MCP_URL", "http://localhost:8005")
    USER_PREFS_MCP_URL: str = os.getenv("USER_PREFS_MCP_URL", "http://localhost:8006")

settings = Settings()
