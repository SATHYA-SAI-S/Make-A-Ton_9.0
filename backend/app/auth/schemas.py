import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


def mask_email(email: str) -> str:
    """Mask email for privacy in user interfaces (e.g., j***e@domain.com)."""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=9, description="Minimum 9 chars with upper, lower, and special char")
    name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    company_name: Optional[str] = None
    country: str = "India"
    timezone: str = "Asia/Kolkata"


class RegisterInitiateRequest(UserRegisterRequest):
    pass


class RegisterInitiateResponse(BaseModel):
    message: str = "A 6-digit verification code has been dispatched to your email address."
    email: EmailStr
    masked_email: str


class VerifyRegistrationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification OTP")

    @model_validator(mode="before")
    @classmethod
    def alias_code_to_otp(cls, values: dict):
        if isinstance(values, dict) and "code" in values and "otp" not in values:
            values["otp"] = values["code"]
        return values


class ResendOTPRequest(BaseModel):
    email: EmailStr


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "If your email is registered in our system, a 6-digit verification code has been dispatched."
    email: EmailStr
    masked_email: str


class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification OTP")

    @model_validator(mode="before")
    @classmethod
    def alias_code_to_otp(cls, values: dict):
        if isinstance(values, dict) and "code" in values and "otp" not in values:
            values["otp"] = values["code"]
        return values


class VerifyResetOTPResponse(BaseModel):
    message: str = "Verification code confirmed. You may now set your new password."
    email: EmailStr
    reset_token: str


class ResetPasswordConfirmRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str = Field(..., min_length=9, description="Minimum 9 chars with upper, lower, and special char")


# Backward compatible request
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=9)


class StaffCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=9)
    name: str = Field(..., min_length=2)
    role: str = Field("staff", pattern="^staff$")


class StaffUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern="^(staff|admin)$")
