from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "SubscriptIQ"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./subscriptiq.db"

    # JWT Security
    JWT_SECRET_KEY: str = "dev-secret-key-subscriptiq-change-in-production-2026-secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Inter-service contract key
    INTERNAL_SERVICE_KEY: str = "subscriptiq-internal-dev-key-2026"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Email Service Configuration
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_FROM_EMAIL: str = "noreply@subscriptiq.com"
    SMTP_FROM_NAME: str = "SubscriptIQ"
    FRONTEND_URL: str = "http://127.0.0.1:5173"

    # Security & OTP Policies
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # Seed Admin Defaults
    SEED_ADMIN_EMAIL: str = "admin@subscriptiq.local"
    SEED_ADMIN_PASSWORD: str = "Admin@SecurePassword2026!"


settings = Settings()
