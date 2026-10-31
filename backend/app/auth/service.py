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
    hash_token,
    generate_secure_otp,
    hash_otp,
    verify_otp_hash
)
from app.core.email import (
    send_registration_otp_email,
    send_password_reset_otp_email
)
from app.core.errors import (
    ValidationException,
    ConflictException,
    UnauthorizedException,
    NotFoundException,
    ForbiddenException
)
from app.auth.models import User, PendingRegistration, PasswordResetOTP
from app.customers.models import Customer
from app.auth.schemas import (
    UserRegisterRequest,
    RegisterInitiateRequest,
    RegisterInitiateResponse,
    VerifyRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    ForgotPasswordResponse,
    VerifyResetOTPResponse,
    StaffCreateRequest,
    StaffUpdateRequest,
    mask_email
)


def initiate_registration(db: Session, request: RegisterInitiateRequest) -> RegisterInitiateResponse:
    """
    Step 1: Validate registration info, generate cryptographically secure 6-digit OTP,
    store hashed OTP in PendingRegistration, and dispatch email via SMTP.
    """
    # 1. Validate password policy
    is_valid, error_msg = validate_password_complexity(request.password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    # 2. Check unique email (case-insensitive) against registered users
    normalized_email = request.email.lower().strip()
    existing_user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing_user:
        raise ConflictException(message="An account with this email address already exists.", code="EMAIL_ALREADY_EXISTS")

    now = datetime.now(timezone.utc)

    # 3. Check existing pending registration for resend cooldown (60 seconds)
    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == normalized_email))
    if pending:
        # Check cooldown if previously sent
        elapsed = (now - pending.last_sent_at.replace(tzinfo=timezone.utc if pending.last_sent_at.tzinfo is None else pending.last_sent_at.tzinfo)).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise ValidationException(
                message=f"Please wait {remaining} seconds before requesting a new verification code.",
                code="RESEND_COOLDOWN_ACTIVE"
            )

    # 4. Generate cryptographically secure random 6-digit OTP (preserves leading zeroes)
    otp = generate_secure_otp()
    hashed_otp = hash_otp(otp)
    hashed_password = hash_password(request.password)
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # 5. Dispatch email via configured email service
    send_registration_otp_email(normalized_email, request.name.strip(), otp)

    # 6. Upsert pending registration record (only hashed OTP is stored!)
    if pending:
        pending.name = request.name.strip()
        pending.phone = request.phone
        pending.company_name = request.company_name
        pending.country = request.country
        pending.timezone = request.timezone
        pending.password_hash = hashed_password
        pending.otp_hash = hashed_otp
        pending.expires_at = expires_at
        pending.attempts = 0
        pending.last_sent_at = now
    else:
        pending = PendingRegistration(
            email=normalized_email,
            name=request.name.strip(),
            phone=request.phone,
            company_name=request.company_name,
            country=request.country,
            timezone=request.timezone,
            password_hash=hashed_password,
            otp_hash=hashed_otp,
            expires_at=expires_at,
            attempts=0,
            last_sent_at=now
        )
        db.add(pending)

    db.commit()

    return RegisterInitiateResponse(
        message=f"A 6-digit verification code has been dispatched to {mask_email(normalized_email)}.",
        email=normalized_email,
        masked_email=mask_email(normalized_email)
    )


def resend_registration_otp(db: Session, email: str) -> RegisterInitiateResponse:
    """Resend verification code for pending registration with cooldown enforcement."""
    normalized_email = email.lower().strip()
    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == normalized_email))
    if not pending:
        raise ValidationException(
            message="No pending registration found for this email address. Please start registration again.",
            code="REGISTRATION_NOT_FOUND"
        )

    now = datetime.now(timezone.utc)
    last_sent = pending.last_sent_at.replace(tzinfo=timezone.utc if pending.last_sent_at.tzinfo is None else pending.last_sent_at.tzinfo)
    elapsed = (now - last_sent).total_seconds()
    if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
        remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
        raise ValidationException(
            message=f"Please wait {remaining} seconds before requesting a new code.",
            code="RESEND_COOLDOWN_ACTIVE"
        )

    # Generate new secure OTP and invalidate older OTP
    otp = generate_secure_otp()
    pending.otp_hash = hash_otp(otp)
    pending.expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    pending.attempts = 0
    pending.last_sent_at = now

    send_registration_otp_email(normalized_email, pending.name, otp)
    db.commit()

    return RegisterInitiateResponse(
        message=f"A fresh verification code has been dispatched to {mask_email(normalized_email)}.",
        email=normalized_email,
        masked_email=mask_email(normalized_email)
    )


def verify_registration(db: Session, request: VerifyRegistrationRequest) -> TokenResponse:
    """
    Step 2: Verify the 6-digit email OTP.
    Enforces expiry (10 mins), max attempts (5), and constant-time hash comparison.
    Activates account, assigns CUSTOMER role, and issues tokens.
    """
    normalized_email = request.email.lower().strip()
    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == normalized_email))

    if not pending:
        raise ValidationException(
            message="No pending registration found for this email address. Please start registration again.",
            code="REGISTRATION_NOT_FOUND"
        )

    now = datetime.now(timezone.utc)
    expires = pending.expires_at.replace(tzinfo=timezone.utc if pending.expires_at.tzinfo is None else pending.expires_at.tzinfo)

    # Check max failed attempts (max 5)
    if pending.attempts >= settings.OTP_MAX_ATTEMPTS:
        db.delete(pending)
        db.commit()
        raise ValidationException(
            message="Too many failed attempts. This verification code has been invalidated. Please register again.",
            code="TOO_MANY_ATTEMPTS"
        )

    # Check 10-minute expiry
    if now > expires:
        db.delete(pending)
        db.commit()
        raise ValidationException(
            message="Verification code has expired (valid for 10 minutes). Please request a new code.",
            code="OTP_EXPIRED"
        )

    # Verify constant-time hash
    if not verify_otp_hash(request.otp, pending.otp_hash):
        pending.attempts += 1
        if pending.attempts >= settings.OTP_MAX_ATTEMPTS:
            db.delete(pending)
            db.commit()
            raise ValidationException(
                message="Too many failed attempts. This verification code has been invalidated. Please register again.",
                code="TOO_MANY_ATTEMPTS"
            )
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - pending.attempts
        raise ValidationException(
            message=f"Invalid verification code. {remaining} attempt(s) remaining.",
            code="INVALID_VERIFICATION_CODE"
        )

    # Validated! Create permanent customer User
    user = User(
        email=pending.email,
        password_hash=pending.password_hash,
        role="customer",
        is_active=True
    )
    db.add(user)
    db.flush()

    # Create associated Customer Profile
    customer = Customer(
        user_id=user.id,
        name=pending.name,
        email=pending.email,
        phone=pending.phone,
        billing_contact=pending.name,
        country=pending.country,
        timezone=pending.timezone,
        status="active"
    )
    db.add(customer)

    # Remove pending registration
    db.delete(pending)
    db.commit()
    db.refresh(user)

    # Issue JWT tokens
    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


def register_customer(db: Session, request: UserRegisterRequest) -> Tuple[User, Customer]:
    """Direct registration (fallback for backwards compatibility)."""
    is_valid, error_msg = validate_password_complexity(request.password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    normalized_email = request.email.lower().strip()
    existing_user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing_user:
        raise ConflictException(message="An account with this email address already exists.", code="EMAIL_ALREADY_EXISTS")

    hashed_pw = hash_password(request.password)

    user = User(
        email=normalized_email,
        password_hash=hashed_pw,
        role="customer",
        is_active=True
    )
    db.add(user)
    db.flush()

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


# -------------------------------------------------------------
# Password Reset Flow (Real Email OTP)
# -------------------------------------------------------------

def initiate_password_reset(db: Session, email: str) -> ForgotPasswordResponse:
    """
    Generate password reset OTP and dispatch via email.
    Always returns generic response to prevent account enumeration.
    """
    normalized_email = email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))

    now = datetime.now(timezone.utc)

    if user and user.is_active:
        # Check cooldown on existing reset request
        existing_reset = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.email == normalized_email))
        if existing_reset:
            last_sent = existing_reset.last_sent_at.replace(tzinfo=timezone.utc if existing_reset.last_sent_at.tzinfo is None else existing_reset.last_sent_at.tzinfo)
            elapsed = (now - last_sent).total_seconds()
            if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise ValidationException(
                    message=f"Please wait {remaining} seconds before requesting a new password reset code.",
                    code="RESEND_COOLDOWN_ACTIVE"
                )

        # Generate cryptographically secure 6-digit OTP
        otp = generate_secure_otp()
        hashed_otp = hash_otp(otp)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        # Dispatch email
        recipient_name = user.customer.name if user.customer else "Valued Customer"
        send_password_reset_otp_email(user.email, recipient_name, otp)

        # Upsert PasswordResetOTP record
        if existing_reset:
            existing_reset.otp_hash = hashed_otp
            existing_reset.expires_at = expires_at
            existing_reset.attempts = 0
            existing_reset.last_sent_at = now
            existing_reset.reset_token_hash = None
            existing_reset.reset_token_expires_at = None
        else:
            new_reset = PasswordResetOTP(
                email=user.email,
                user_id=user.id,
                otp_hash=hashed_otp,
                expires_at=expires_at,
                attempts=0,
                last_sent_at=now
            )
            db.add(new_reset)

        # Also populate user.reset_token_hash for legacy fallback
        legacy_token = generate_secure_token()
        user.reset_token_hash = hash_token(legacy_token)
        user.reset_token_expires_at = expires_at

        db.commit()

    return ForgotPasswordResponse(
        message="If your email is registered in our system, a 6-digit verification code has been dispatched.",
        email=normalized_email,
        masked_email=mask_email(normalized_email)
    )


def resend_password_reset_otp(db: Session, email: str) -> ForgotPasswordResponse:
    """Resend password reset OTP with cooldown check."""
    return initiate_password_reset(db, email)


def verify_password_reset_otp(db: Session, email: str, otp: str) -> VerifyResetOTPResponse:
    """
    Verify the 6-digit password reset OTP.
    Enforces 10-minute expiry, max 5 attempts, single-use invalidation,
    and returns a short-lived reset authorization token.
    """
    normalized_email = email.lower().strip()
    reset_rec = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.email == normalized_email))

    if not reset_rec:
        raise ValidationException(
            message="No active password reset request found. Please request a new code.",
            code="RESET_NOT_FOUND"
        )

    now = datetime.now(timezone.utc)
    expires = reset_rec.expires_at.replace(tzinfo=timezone.utc if reset_rec.expires_at.tzinfo is None else reset_rec.expires_at.tzinfo)

    # Check max failed attempts
    if reset_rec.attempts >= settings.OTP_MAX_ATTEMPTS:
        db.delete(reset_rec)
        db.commit()
        raise ValidationException(
            message="Too many failed attempts. This reset code has been invalidated. Please request a new one.",
            code="TOO_MANY_ATTEMPTS"
        )

    # Check 10-minute expiry
    if now > expires:
        db.delete(reset_rec)
        db.commit()
        raise ValidationException(
            message="Password reset code has expired. Please request a new one.",
            code="OTP_EXPIRED"
        )

    # Single-use check
    if reset_rec.otp_hash == "USED":
        raise ValidationException(
            message="This verification code has already been used. Please request a new one.",
            code="OTP_ALREADY_USED"
        )

    # Verify constant-time hash
    if not verify_otp_hash(otp, reset_rec.otp_hash):
        reset_rec.attempts += 1
        if reset_rec.attempts >= settings.OTP_MAX_ATTEMPTS:
            db.delete(reset_rec)
            db.commit()
            raise ValidationException(
                message="Too many failed attempts. This reset code has been invalidated. Please request a new one.",
                code="TOO_MANY_ATTEMPTS"
            )
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - reset_rec.attempts
        raise ValidationException(
            message=f"Invalid verification code. {remaining} attempt(s) remaining.",
            code="INVALID_OTP"
        )

    # Mark OTP as USED (single-use enforcement)
    reset_rec.otp_hash = "USED"

    # Issue short-lived reset authorization token (valid for 5 minutes)
    raw_reset_token = generate_secure_token()
    reset_rec.reset_token_hash = hash_token(raw_reset_token)
    reset_rec.reset_token_expires_at = now + timedelta(minutes=5)

    db.commit()

    return VerifyResetOTPResponse(
        message="Verification code confirmed. You may now set your new password.",
        email=normalized_email,
        reset_token=raw_reset_token
    )


def complete_password_reset_with_token(
    db: Session,
    email: str,
    reset_token: str,
    new_password: str
) -> bool:
    """Update password after verifying the authorization token."""
    # 1. Validate password policy
    is_valid, error_msg = validate_password_complexity(new_password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

    normalized_email = email.lower().strip()
    token_hashed = hash_token(reset_token)
    now = datetime.now(timezone.utc)

    # Find reset record
    reset_rec = db.scalar(
        select(PasswordResetOTP).where(
            PasswordResetOTP.email == normalized_email,
            PasswordResetOTP.reset_token_hash == token_hashed
        )
    )

    if not reset_rec:
        raise ValidationException(
            message="Invalid or expired password reset session. Please request a new verification code.",
            code="INVALID_RESET_TOKEN"
        )

    expires = reset_rec.reset_token_expires_at.replace(
        tzinfo=timezone.utc if reset_rec.reset_token_expires_at.tzinfo is None else reset_rec.reset_token_expires_at.tzinfo
    )

    if now > expires:
        db.delete(reset_rec)
        db.commit()
        raise ValidationException(
            message="Password reset session has expired. Please request a new code.",
            code="RESET_TOKEN_EXPIRED"
        )

    # Update user password
    user = db.get(User, reset_rec.user_id)
    if not user:
        raise NotFoundException(message="User account not found.", code="USER_NOT_FOUND")

    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None

    # Invalidate reset record
    db.delete(reset_rec)
    db.commit()

    return True


def complete_password_reset(db: Session, token: str, new_password: str) -> bool:
    """Legacy backward-compatible password reset using raw token."""
    is_valid, error_msg = validate_password_complexity(new_password)
    if not is_valid:
        raise ValidationException(message=error_msg, code="WEAK_PASSWORD")

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

    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None

    # Clean up any PasswordResetOTP for this user
    reset_rec = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id))
    if reset_rec:
        db.delete(reset_rec)

    db.commit()
    return True


# -------------------------------------------------------------
# Staff Management (Admin Only)
# -------------------------------------------------------------

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
