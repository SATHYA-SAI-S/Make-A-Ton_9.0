import uuid
from typing import Callable, List, Optional
from fastapi import Depends, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.core.errors import UnauthorizedException, ForbiddenException
from app.auth.models import User
from app.customers.models import Customer

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that extracts and verifies current authenticated user."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(message="Authentication required. Missing Bearer token.", code="UNAUTHORIZED")

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise UnauthorizedException(message="Invalid or expired access token.", code="INVALID_TOKEN")

    if payload.get("type") != "access":
        raise UnauthorizedException(message="Token is not an access token.", code="INVALID_TOKEN_TYPE")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Malformed access token payload.", code="MALFORMED_TOKEN")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Invalid user ID in token.", code="MALFORMED_USER_ID")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedException(message="User account not found.", code="USER_NOT_FOUND")

    if not user.is_active:
        raise ForbiddenException(message="User account is deactivated.", code="ACCOUNT_DEACTIVATED")

    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency factory checking that the current user has one of the required roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                message=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}.",
                code="INSUFFICIENT_PERMISSIONS"
            )
        return current_user

    return role_checker


def get_current_customer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Customer:
    """Dependency for customer portal endpoints ensuring customer profile exists."""
    if current_user.role != "customer":
        raise ForbiddenException(message="This endpoint is restricted to customer accounts.", code="CUSTOMER_ONLY")

    customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
    if not customer:
        raise ForbiddenException(message="Customer profile not found for this account.", code="CUSTOMER_PROFILE_MISSING")

    return customer


def verify_internal_service_key(
    x_internal_service_key: Optional[str] = Header(None, alias="X-Internal-Service-Key")
) -> bool:
    """Dependency for inter-service communication (Person 2 billing engine & Person 3 analytics)."""
    if not x_internal_service_key or x_internal_service_key != settings.INTERNAL_SERVICE_KEY:
        raise ForbiddenException(
            message="Invalid or missing internal service security key.",
            code="INVALID_INTERNAL_KEY"
        )
    return True
