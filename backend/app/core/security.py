from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

class UserContext(BaseModel):
    user_id: str = "dev-user-admin"
    email: str = "admin@brightloop.com"
    role: str = "admin"  # admin, staff, customer
    customer_id: Optional[str] = "cust-dev-001"

def current_user(
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header("admin"),
    x_user_id: Optional[str] = Header("dev-user-admin"),
    x_customer_id: Optional[str] = Header(None)
) -> UserContext:
    """Dev user context resolver allowing easy testing across roles."""
    return UserContext(
        user_id=x_user_id or "dev-user-admin",
        email=f"{x_user_role}@brightloop.com",
        role=x_user_role or "admin",
        customer_id=x_customer_id or ("cust-dev-001" if x_user_role == "customer" else None)
    )

def require_roles(*allowed_roles: str):
    def role_checker(user: UserContext = Depends(current_user)):
        if user.role not in allowed_roles and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized to access this resource"
            )
        return user
    return role_checker

def require_customer_owner(customer_id: str, user: UserContext = Depends(current_user)):
    if user.role == "customer" and user.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another customer's resources"
        )
    return user
