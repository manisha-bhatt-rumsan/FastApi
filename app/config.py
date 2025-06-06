from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "My FastAPI Application"
    app_description: str = "A comprehensive FastAPI application with health checks and documentation"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Allow all origins (development only)
    ]
    debug: bool = True
    database_url: str  # Loaded from .env

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()