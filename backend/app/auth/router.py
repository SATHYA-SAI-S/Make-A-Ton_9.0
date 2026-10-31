import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.models import User
from app.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    UserResponse,
    StaffCreateRequest,
    StaffUpdateRequest
)
from app.auth.deps import get_current_user, require_roles
from app.auth import service

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
staff_router = APIRouter(prefix="/staff", tags=["Staff Management"])


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new customer account with profile."""
    user, customer = service.register_customer(db, request)
    return service.authenticate_user(db, UserLoginRequest(email=request.email, password=request.password))


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


@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset link. Returns generic response for security."""
    raw_token = service.initiate_password_reset(db, request.email)
    return ForgotPasswordResponse(
        message="If your email is registered in our system, you will receive password reset instructions.",
        reset_token=raw_token  # For development testing/inspection
    )


@auth_router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password with valid token."""
    service.complete_password_reset(db, request.token, request.new_password)
    return {"message": "Password has been successfully updated. You may now login."}


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return current_user


# Staff Management Endpoints (Admin Only)

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
