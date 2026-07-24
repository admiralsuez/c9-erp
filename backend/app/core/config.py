import json
import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Cloud9 ERP"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # production, staging, development

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # CORS - Allow frontend domain(s)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://erp.cloud9beverages.com",
    ]
    ALLOWED_HOSTS: Union[List[str], str] = [
        "localhost",
        "127.0.0.1",
        "erp.cloud9beverages.com",
    ]

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_list(cls, v: Union[List[str], str, None]) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [item.strip().strip("'\"") for item in v.split(",") if item.strip()]
        return v

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    REFRESH_TOKEN_EXPIRATION_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "30"))

    # DigitalOcean Spaces (S3-compatible)
    DO_SPACES_KEY: str = os.getenv("DO_SPACES_KEY", "")
    DO_SPACES_SECRET: str = os.getenv("DO_SPACES_SECRET", "")
    DO_SPACES_BUCKET: str = os.getenv("DO_SPACES_BUCKET", "cloud9-erp")
    DO_SPACES_REGION: str = os.getenv("DO_SPACES_REGION", "sfo3")
    DO_SPACES_ENDPOINT: str = os.getenv("DO_SPACES_ENDPOINT", "https://sfo3.digitaloceanspaces.com")
    DO_SPACES_CDN_URL: str = os.getenv("DO_SPACES_CDN_URL", "")  # Optional CDN URL

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Validate required secrets at startup
if not settings.JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required. Set it in .env or environment.")
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Set it in .env or environment.")
