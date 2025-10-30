"""Application configuration settings."""

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Research Compass UI API"
    api_version: str = "1.0.0"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Research Configuration
    export_directory: str = "./research_reports"

    # Environment
    openai_api_key: str = ""
    semantic_scholar_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "research-compass"
    langsmith_tracing: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure export directory exists
Path(settings.export_directory).mkdir(parents=True, exist_ok=True)
