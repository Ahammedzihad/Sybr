"""Application configuration loaded from environment variables."""

import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""

    APP_NAME: str = "AI Security Analytics"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Gemini AI configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MOCK_MODE: bool = True
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Database configuration
    DATABASE_PATH: str = "./data/app.db"

    # CORS configuration
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
