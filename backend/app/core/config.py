from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Alex Voice Agent API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://alex_user:alex_password@localhost:5432/alex_db",
        env="DATABASE_URL"
    )
    
    # Gemini / LLM
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    
    # Auth & Security
    SECRET_KEY: str = Field(default="alex_secret_key_change_in_production_32bytes", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # FastMCP Server URLs
    CALENDAR_MCP_URL: str = Field(default="http://localhost:8001", env="CALENDAR_MCP_URL")
    CONTACTS_MCP_URL: str = Field(default="http://localhost:8002", env="CONTACTS_MCP_URL")
    REMINDERS_MCP_URL: str = Field(default="http://localhost:8003", env="REMINDERS_MCP_URL")
    SEARCH_RAG_MCP_URL: str = Field(default="http://localhost:8004", env="SEARCH_RAG_MCP_URL")
    EMAIL_MESSAGING_MCP_URL: str = Field(default="http://localhost:8005", env="EMAIL_MESSAGING_MCP_URL")
    USER_PREFS_MCP_URL: str = Field(default="http://localhost:8006", env="USER_PREFS_MCP_URL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
