import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.models import User
from app.auth.schemas import (
    UserRegisterRequest,
    RegisterInitiateRequest,
    RegisterInitiateResponse,
    VerifyRegistrationRequest,
    ResendOTPRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
    ResetPasswordConfirmRequest,
    ResetPasswordRequest,
    UserResponse,
    StaffCreateRequest,
    StaffUpdateRequest
)
from app.auth.deps import get_current_user, require_roles
from app.auth import service

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
staff_router = APIRouter(prefix="/staff", tags=["Staff Management"])


# -------------------------------------------------------------
# Registration Endpoints (Real Email OTP)
# -------------------------------------------------------------

@auth_router.post("/register/initiate", response_model=RegisterInitiateResponse, status_code=status.HTTP_200_OK)
def register_initiate(request: RegisterInitiateRequest, db: Session = Depends(get_db)):
    """Step 1: Validate registration info, generate secure 6-digit OTP, and dispatch verification email."""
    return service.initiate_registration(db, request)


@auth_router.post("/register/resend", response_model=RegisterInitiateResponse, status_code=status.HTTP_200_OK)
def register_resend(request: ResendOTPRequest, db: Session = Depends(get_db)):
    """Resend registration verification code with 60s cooldown enforcement."""
    return service.resend_registration_otp(db, request.email)


@auth_router.post("/register/verify", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_verify(request: VerifyRegistrationRequest, db: Session = Depends(get_db)):
    """Step 2: Verify 6-digit OTP, activate customer account, assign CUSTOMER role, and return tokens."""
    return service.verify_registration(db, request)


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Direct registration (fallback for backwards compatibility)."""
    user, customer = service.register_customer(db, request)
    return service.authenticate_user(db, UserLoginRequest(email=request.email, password=request.password))


# -------------------------------------------------------------
# Login & Token Endpoints
# -------------------------------------------------------------

@auth_router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    return service.authenticate_user(db, request)


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotate and refresh access token using valid refresh token."""
    return service.refresh_access_token(db, request.refresh_token)


@auth_router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Client logout confirmation."""
    return {"message": "Logged out successfully."}


# -------------------------------------------------------------
# Forgot & Reset Password Endpoints (Real Email OTP)
# -------------------------------------------------------------

@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset OTP via email. Returns generic response to prevent account enumeration."""
    return service.initiate_password_reset(db, request.email)


@auth_router.post("/forgot-password/resend", response_model=ForgotPasswordResponse)
def forgot_password_resend(request: ResendOTPRequest, db: Session = Depends(get_db)):
    """Resend password reset OTP with 60-second cooldown."""
    return service.resend_password_reset_otp(db, request.email)


@auth_router.post("/forgot-password/verify-otp", response_model=VerifyResetOTPResponse)
def forgot_password_verify_otp(request: VerifyResetOTPRequest, db: Session = Depends(get_db)):
    """Verify 6-digit password reset OTP and obtain short-lived authorization reset token."""
    return service.verify_password_reset_otp(db, request.email, request.otp)


@auth_router.post("/forgot-password/confirm")
def forgot_password_confirm(request: ResetPasswordConfirmRequest, db: Session = Depends(get_db)):
    """Set new password using verified reset authorization token."""
    service.complete_password_reset_with_token(db, request.email, request.reset_token, request.new_password)
    return {"message": "Password has been successfully updated. You may now sign in."}


@auth_router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Legacy backward-compatible password reset with token."""
    service.complete_password_reset(db, request.token, request.new_password)
    return {"message": "Password has been successfully updated. You may now login."}


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return current_user


# -------------------------------------------------------------
# Staff Management Endpoints (Admin Only)
# -------------------------------------------------------------

@staff_router.get("", response_model=List[UserResponse])
def get_staff_members(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """List all internal staff accounts (Admin only)."""
    return service.list_staff_users(db, current_user)


@staff_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_member(
    request: StaffCreateRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Create a new internal staff member (Admin only)."""
    return service.create_staff_user(db, request, current_user)


@staff_router.patch("/{staff_id}", response_model=UserResponse)
def update_staff_member(
    staff_id: uuid.UUID,
    request: StaffUpdateRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Activate, deactivate, or modify staff role (Admin only)."""
    return service.update_staff_user(db, staff_id, request, current_user)
