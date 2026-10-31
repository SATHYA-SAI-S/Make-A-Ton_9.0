import os
from typing import List, Optional
from pydantic import BaseModel

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    class _BaseSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )
except ImportError:
    class _BaseSettings(BaseModel):  # type: ignore
        pass


class Settings(_BaseSettings):
    PROJECT_NAME: str = "SubscriptIQ"
    APP_NAME: str = "SubscriptIQ"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./subscriptiq.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-subscriptiq-change-in-production-2026-secure")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-subscriptiq-change-in-production-2026-secure")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Inter-service contract key
    INTERNAL_SERVICE_KEY: str = os.getenv("INTERNAL_SERVICE_KEY", "subscriptiq-internal-dev-key-2026")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Email Service Configuration / SMTP / Mailpit
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "smtp")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "False").lower() in ("true", "1")
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "False").lower() in ("true", "1")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@subscriptiq.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "SubscriptIQ")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "billing@brightloop.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "Brightloop Software")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")

    # Security & OTP Policies
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # Seed Admin Defaults
    SEED_ADMIN_EMAIL: str = os.getenv("SEED_ADMIN_EMAIL", "admin@subscriptiq.local")
    SEED_ADMIN_PASSWORD: str = os.getenv("SEED_ADMIN_PASSWORD", "Admin@SecurePassword2026!")

    # Company / Billing Settings Defaults
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Brightloop Software")
    COMPANY_STATE_CODE: str = os.getenv("COMPANY_STATE_CODE", "KA")
    COMPANY_GSTIN: str = os.getenv("COMPANY_GSTIN", "29AABCU9603R1Z7")
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")

    # Razorpay / Stripe
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_samplekey123")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "sample_secret_key_456")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "sample_webhook_secret_789")


settings = Settings()
