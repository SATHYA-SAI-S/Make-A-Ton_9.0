import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_complexity,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    hash_token
)
from app.core.errors import (
    ValidationException,
    ConflictException,
    UnauthorizedException,
    NotFoundException,
    ForbiddenException
)
from app.auth.models import User
from app.customers.models import Customer
from app.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    StaffCreateRequest,
    StaffUpdateRequest
)


def register_customer(db: Session, request: UserRegisterRequest) -> Tuple[User, Customer]:
    """Register a new customer account with profile."""
    # 1. Validate password policy
    is_valid, error_msg = validate_password_complexity(request.password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    # 2. Check unique email (case-insensitive)
    normalized_email = request.email.lower().strip()
    existing_user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing_user:
        raise ConflictException(message="An account with this email address already exists.", code="EMAIL_ALREADY_EXISTS")

    # 3. Hash password with Argon2
    hashed_pw = hash_password(request.password)

    # 4. Create User
    user = User(
        email=normalized_email,
        password_hash=hashed_pw,
        role="customer",
        is_active=True
    )
    db.add(user)
    db.flush()

    # 5. Create associated Customer Profile
    customer = Customer(
        user_id=user.id,
        name=request.name.strip(),
        email=normalized_email,
        phone=request.phone,
        billing_contact=request.name.strip(),
        country=request.country,
        timezone=request.timezone,
        status="active"
    )
    db.add(customer)
    db.commit()
    db.refresh(user)
    db.refresh(customer)

    return user, customer


def authenticate_user(db: Session, request: UserLoginRequest) -> TokenResponse:
    """Authenticate user and generate access and refresh tokens."""
    normalized_email = request.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if not user or not verify_password(request.password, user.password_hash):
        raise UnauthorizedException(message="Invalid email or password.", code="INVALID_CREDENTIALS")

    if not user.is_active:
        raise ForbiddenException(message="This account has been deactivated. Please contact support.", code="ACCOUNT_DEACTIVATED")

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
    """Generate new access and refresh tokens using valid refresh token."""
    try:
        payload = decode_token(refresh_token_str)
    except Exception:
        raise UnauthorizedException(message="Invalid or expired refresh token.", code="INVALID_REFRESH_TOKEN")

    if payload.get("type") != "refresh":
        raise UnauthorizedException(message="Token is not a valid refresh token.", code="INVALID_TOKEN_TYPE")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Invalid token subject.", code="INVALID_TOKEN_SUBJECT")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Malformed user ID in token.", code="MALFORMED_TOKEN")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(message="User not found or deactivated.", code="USER_NOT_ACTIVE")

    new_access_token = create_access_token(subject=str(user.id), role=user.role)
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user)
    )


def initiate_password_reset(db: Session, email: str) -> Optional[str]:
    """
    Generate password reset token.
    Returns token in dev mode, but always safe response.
    Never enumerates whether email exists.
    """
    normalized_email = email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if not user or not user.is_active:
        return None

    raw_token = generate_secure_token()
    user.reset_token_hash = hash_token(raw_token)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    return raw_token


def complete_password_reset(db: Session, token: str, new_password: str) -> bool:
    """Verify reset token and update password."""
    # 1. Validate password policy
    is_valid, error_msg = validate_password_complexity(new_password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    # 2. Find user by hashed token
    token_hashed = hash_token(token)
    now = datetime.now(timezone.utc)
    user = db.scalar(
        select(User).where(
            User.reset_token_hash == token_hashed,
            User.reset_token_expires_at > now
        )
    )
    if not user:
        raise ValidationException(message="Invalid or expired password reset token.", code="INVALID_RESET_TOKEN")

    # 3. Update password and invalidate token
    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.commit()

    return True


def create_staff_user(db: Session, request: StaffCreateRequest, creator: User) -> User:
    """Admin-only staff creation."""
    if creator.role != "admin":
        raise ForbiddenException(message="Only administrators can create staff accounts.", code="ADMIN_REQUIRED")

    is_valid, error_msg = validate_password_complexity(request.password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    normalized_email = request.email.lower().strip()
    existing_user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing_user:
        raise ConflictException(message="An account with this email address already exists.", code="EMAIL_ALREADY_EXISTS")

    staff = User(
        email=normalized_email,
        password_hash=hash_password(request.password),
        role="staff",
        is_active=True
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


def list_staff_users(db: Session, creator: User) -> List[User]:
    """Admin-only staff listing."""
    if creator.role != "admin":
        raise ForbiddenException(message="Only administrators can view staff members.", code="ADMIN_REQUIRED")

    return list(db.scalars(select(User).where(User.role == "staff").order_by(User.created_at.desc())).all())


def update_staff_user(db: Session, staff_id: uuid.UUID, request: StaffUpdateRequest, creator: User) -> User:
    """Admin-only staff update."""
    if creator.role != "admin":
        raise ForbiddenException(message="Only administrators can manage staff accounts.", code="ADMIN_REQUIRED")

    staff = db.get(User, staff_id)
    if not staff or staff.role not in ("staff", "admin"):
        raise NotFoundException(message="Staff member not found.", code="STAFF_NOT_FOUND")

    if request.is_active is not None:
        staff.is_active = request.is_active
    if request.role is not None:
        staff.role = request.role

    db.commit()
    db.refresh(staff)
    return staff
