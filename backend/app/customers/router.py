import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.models import User
from app.auth.deps import get_current_user, require_roles
from app.customers.models import Customer
from app.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse
)
from app.customers import service

customers_router = APIRouter(prefix="/customers", tags=["Customers"])


@customers_router.get("", response_model=CustomerListResponse)
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[str] = Query(None, description="Filter by active/suspended"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """List and search customers with pagination (Admin & Staff)."""
    return service.list_customers(
        db=db,
        requesting_user=current_user,
        search=search,
        status=status,
        page=page,
        page_size=page_size
    )


@customers_router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    request: CustomerCreate,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Create a new customer profile (Admin & Staff)."""
    return service.create_customer(db=db, request=request, creator=current_user)


@customers_router.get("/me", response_model=CustomerResponse)
def get_my_customer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the customer profile of the authenticated user."""
    return service.get_customer_for_user(db=db, user=current_user)


@customers_router.patch("/me", response_model=CustomerResponse)
def update_my_customer_profile(
    request: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update own customer profile (Customer self-service)."""
    customer = service.get_customer_for_user(db=db, user=current_user)
    return service.update_customer(db=db, customer_id=customer.id, request=request, requesting_user=current_user)


@customers_router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve customer details (Staff/Admin or customer accessing own profile)."""
    return service.get_customer(db=db, customer_id=customer_id, requesting_user=current_user)


@customers_router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: uuid.UUID,
    request: CustomerUpdate,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Update customer profile (Admin & Staff)."""
    return service.update_customer(db=db, customer_id=customer_id, request=request, requesting_user=current_user)
