import os
from typing import Optional
from pydantic import BaseModel

try:
    from pydantic_settings import BaseSettings
except ImportError:
    class BaseSettings(BaseModel):
        pass

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "SubscriptIQ")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-must-be-32-chars!")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./subscriptiq.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    # Company / Billing Settings Defaults
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Brightloop Software")
    COMPANY_STATE_CODE: str = os.getenv("COMPANY_STATE_CODE", "KA")  # Karnataka default
    COMPANY_GSTIN: str = os.getenv("COMPANY_GSTIN", "29AABCU9603R1Z7")
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")

    # SMTP / Mailpit
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "billing@brightloop.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "Brightloop Software")

    # Razorpay / Stripe
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_samplekey123")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "sample_secret_key_456")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "sample_webhook_secret_789")

settings = Settings()
