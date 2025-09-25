from pydantic import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    notion_api_key: str = os.getenv("NOTION_API_KEY", "")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./workflow_agent.db")
    
    # Vector Database
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./chroma_db")
    
    # Application
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    secret_key: str = os.getenv("SECRET_KEY", "default-secret-key")
    
    # Email Settings
    gmail_credentials_path: str = os.getenv("GMAIL_CREDENTIALS_PATH", "config/gmail_credentials.json")
    gmail_token_path: str = os.getenv("GMAIL_TOKEN_PATH", "config/gmail_token.pickle")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
