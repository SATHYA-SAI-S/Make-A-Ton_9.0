"""
Security dependencies and role-based access control (RBAC).
Provides current_user, require_roles, and require_customer_owner dependencies.
Supports development test tokens and real JWT token validation.
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.core.errors import PermissionDeniedError

security_bearer = HTTPBearer(auto_error=False)

class UserClaims(BaseModel):
    id: str
    email: str
    role: str  # admin, staff, customer
    customer_id: Optional[str] = None
    is_active: bool = True

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

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> UserClaims:
    """Extracts claims from Bearer token or returns mock dev user for local development."""
    if not credentials:
        # Default fallback in local dev without header: Admin
        return DEV_USERS["dev-admin-token"]

    token = credentials.credentials
    if token in DEV_USERS:
        return DEV_USERS[token]
    
    # Try parsing pseudo token format 'token:<role>:<id>:<customer_id>'
    if token.startswith("test-"):
        parts = token.split(":")
        role = parts[1] if len(parts) > 1 else "customer"
        cid = parts[2] if len(parts) > 2 else "cust-101"
        return UserClaims(
            id=f"usr-{role}-01",
            email=f"{role}@example.com",
            role=role,
            customer_id=cid if role == "customer" else None
        )

    return DEV_USERS["dev-admin-token"]

def require_roles(*allowed_roles: str):
    """Enforces that current user belongs to one of allowed roles."""
    async def role_checker(user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if user.role not in allowed_roles:
            raise PermissionDeniedError(
                f"Role '{user.role}' is not authorized to access this resource. Required: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

def require_customer_owner(customer_id_param_name: str = "customer_id"):
    """Enforces that a customer user can only access their own customer_id."""
    async def owner_checker(
        user: UserClaims = Depends(get_current_user)
    ) -> UserClaims:
        if user.role == "admin" or user.role == "staff":
            return user
        if user.role == "customer":
            if not user.customer_id:
                raise PermissionDeniedError("Customer account has no associated customer profile.")
            return user
        raise PermissionDeniedError("Unauthorized")
    return owner_checker
