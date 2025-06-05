from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application metadata
    app_name: str = "My FastAPI Application"
    app_description: str = "A comprehensive FastAPI application with health checks and documentation"
    app_version: str = "1.0.0"
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    
    # CORS settings
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:8080",  # Vue.js default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Allow all origins (only for development!)
    ]
    
    # Development settings
    debug: bool = True  # Set to False in production
    
    # Database settings (for future use)
   # database_url: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"

# Create a global settings instance
settings = Settings()