"""
Customer Portal Security Dependencies.
Enforces that only authenticated customers can access portal endpoints.
Strictly resolves customer_id from user JWT claims via CustomerPort.
"""
from typing import Any, Dict
from fastapi import Depends
from backend.app.core.security import get_current_user, UserClaims
from backend.app.core.errors import PermissionDeniedError
from backend.app.shared.registry import get_port

async def get_portal_customer(
    user: UserClaims = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Enforces customer role and resolves the customer entity from CustomerPort.
    Staff and Admin roles are explicitly rejected on portal routes.
    """
    if user.role != "customer":
        raise PermissionDeniedError("Portal endpoints are restricted to customer accounts only.")
    
    cust_port = get_port("customer")
    customer = None
    
    # First try resolving by user_id
    customer = cust_port.get_by_user(user.id)
    
    # Fallback to customer_id if set on token
    if not customer and user.customer_id:
        customer = cust_port.get(user.customer_id)

    if not customer:
        raise PermissionDeniedError("No customer record is associated with this login account.")

    return customer
