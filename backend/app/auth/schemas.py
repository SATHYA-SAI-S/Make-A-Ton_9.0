import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
    message: str = "If your email is registered in our system, you will receive password reset instructions."
    reset_token: Optional[str] = None  # Returned in development mode for easy local verification


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
