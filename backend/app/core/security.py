import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

try:
    from app.core.config import settings
except ImportError:
    from app.core.config import settings

_ph = PasswordHasher()
security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using Argon2."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2 hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_password_complexity(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validates password against mandatory policy:
    - More than 8 characters (minimum 9 characters)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one special character
    """
    if len(password) <= 8:
        return False, "Password must be more than 8 characters long (minimum 9 characters)."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\/`~]", password):
        return False, "Password must contain at least one special character."
    return True, None


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_secure_token() -> str:
    """Generate a high-entropy random URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA256 for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_otp() -> str:
    """
    Generate a cryptographically secure 6-digit numeric OTP (000000 - 999999).
    Preserves leading zeros.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    """Hash an OTP using SHA-256 for secure in-memory or database storage."""
    return hashlib.sha256(otp.strip().encode("utf-8")).hexdigest()


def verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
    """Constant-time verification of plain OTP against its stored SHA-256 hash."""
    computed = hash_otp(plain_otp)
    return secrets.compare_digest(computed, hashed_otp)


class UserClaims(BaseModel):
    id: str = "dev-user-admin"
    user_id: str = "dev-user-admin"
    email: str = "admin@brightloop.com"
    role: str = "admin"  # admin, staff, customer
    customer_id: Optional[str] = "cust-dev-001"
    is_active: bool = True

    def __init__(self, **data):
        if "id" in data and "user_id" not in data:
            data["user_id"] = data["id"]
        elif "user_id" in data and "id" not in data:
            data["id"] = data["user_id"]
        super().__init__(**data)


UserContext = UserClaims

DEV_USERS = {
    "dev-admin-token": UserClaims(
        id="usr-admin-001",
        email="admin@brightloop.com",
        role="admin"
    ),
    "dev-staff-token": UserClaims(
        id="usr-staff-001",
        email="finance@brightloop.com",
        role="staff"
    ),
    "dev-customer-token": UserClaims(
        id="usr-cust-001",
        email="billing@acme.com",
        role="customer",
        customer_id="cust-101"
    ),
    "dev-customer-2-token": UserClaims(
        id="usr-cust-002",
        email="ops@techcorp.com",
        role="customer",
        customer_id="cust-102"
    )
}


def current_user(
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_customer_id: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> UserClaims:
    """User context resolver supporting dev headers, test tokens, or fallback."""
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if raw_token and raw_token in DEV_USERS:
        return DEV_USERS[raw_token]

    if raw_token and raw_token.startswith("test-"):
        parts = raw_token.split(":")
        role = parts[1] if len(parts) > 1 else "customer"
        cid = parts[2] if len(parts) > 2 else "cust-101"
        return UserClaims(
            id=f"usr-{role}-01",
            user_id=f"usr-{role}-01",
            email=f"{role}@example.com",
            role=role,
            customer_id=cid if role == "customer" else None
        )

    # Check headers
    if x_user_role or x_user_id or x_customer_id:
        role = x_user_role or "admin"
        return UserClaims(
            id=x_user_id or "dev-user-admin",
            user_id=x_user_id or "dev-user-admin",
            email=f"{role}@brightloop.com",
            role=role,
            customer_id=x_customer_id or ("cust-dev-001" if role == "customer" else None)
        )

    return DEV_USERS["dev-admin-token"]


get_current_user = current_user


def require_roles(*allowed_roles: str):
    def role_checker(user: UserClaims = Depends(current_user)):
        if user.role not in allowed_roles and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized to access this resource"
            )
        return user
    return role_checker


def require_customer_owner(customer_id: str = "customer_id", user: UserClaims = Depends(current_user)):
    if user.role == "customer" and user.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another customer's resources"
        )
    return user

