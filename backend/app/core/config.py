import os
import secrets
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "AFFECTORYX"
    API_V1_STR: str = "/api/v1"
    
    # Security: In development, fallback to a randomly generated key per process or custom key
    SECRET_KEY: str = "dev-insecure-only-local-eval-key-replace-in-production-affactoryx-32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "sqlite:///./affactoryx.db"

    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Initial Superuser setup
    FIRST_SUPERUSER_EMAIL: str = "admin@affactoryx.internal"
    FIRST_SUPERUSER_PASSWORD: str = "AdminAffactoryx2026!"
    
    # External Integrations (Optional)
    GITHUB_TOKEN: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = self.ENVIRONMENT.lower()
        if env in ("production", "prod"):
            # Enforce strong secret key in production
            insecure_indicators = ["insecure", "replace", "secret", "test", "dev", "123"]
            is_insecure = any(term in self.SECRET_KEY.lower() for term in insecure_indicators)
            if len(self.SECRET_KEY) < 32 or is_insecure:
                raise ValueError(
                    "SECURITY ERROR: In production environment, SECRET_KEY must be at least 32 "
                    "characters long and must not contain insecure placeholder terms. "
                    "Generate a cryptographically secure key with: openssl rand -hex 32"
                )
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError(
                    "SECURITY WARNING: Production environment cannot use SQLite. "
                    "Provide a production PostgreSQL connection string."
                )
        return self

    def __repr__(self) -> str:
        """Prevent secrets from leaking when settings object is inspected or logged."""
        return f"<Settings: env={self.ENVIRONMENT}, project={self.PROJECT_NAME}, db={self.DATABASE_URL.split('@')[-1]}>"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
