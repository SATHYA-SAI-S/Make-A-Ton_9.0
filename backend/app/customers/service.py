import uuid
import math
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.core.errors import NotFoundException, ConflictException, ForbiddenException
from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerUpdate, CustomerListResponse, CustomerResponse
from app.auth.models import User


def create_customer(db: Session, request: CustomerCreate, creator: User) -> Customer:
    """Create a new customer profile. Admin & Staff permitted."""
    if creator.role not in ("admin", "staff"):
        raise ForbiddenException("Only staff and administrators can directly create customer profiles.", code="PERMISSION_DENIED")

    normalized_email = request.email.lower().strip()
    existing = db.scalar(select(Customer).where(func.lower(Customer.email) == normalized_email))
    if existing:
        raise ConflictException("A customer with this email address already exists.", code="CUSTOMER_EXISTS")

    customer = Customer(
        user_id=request.user_id,
        name=request.name.strip(),
        email=normalized_email,
        phone=request.phone,
        billing_contact=request.billing_contact or request.name.strip(),
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country,
        timezone=request.timezone,
        tax_id=request.tax_id,
        status=request.status
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: uuid.UUID, requesting_user: User) -> Customer:
    """Retrieve customer by ID. Staff/Admin can view all; Customer can only view own."""
    customer = db.get(Customer, customer_id)
    if not customer:
        raise NotFoundException("Customer not found.", code="CUSTOMER_NOT_FOUND")

    if requesting_user.role == "customer" and customer.user_id != requesting_user.id:
        raise ForbiddenException("You are not authorized to view another customer's profile.", code="IDOR_VIOLATION")

    return customer


def get_customer_for_user(db: Session, user: User) -> Customer:
    """Get the customer profile tied to an authenticated customer user."""
    customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
    if not customer:
        raise NotFoundException("Customer profile not found for this account.", code="CUSTOMER_NOT_FOUND")
    return customer


def update_customer(db: Session, customer_id: uuid.UUID, request: CustomerUpdate, requesting_user: User) -> Customer:
    """Update customer profile."""
    customer = get_customer(db, customer_id, requesting_user)

    if requesting_user.role == "customer" and customer.user_id != requesting_user.id:
        raise ForbiddenException("You cannot modify another customer's profile.", code="PERMISSION_DENIED")

    update_data = request.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"].lower().strip()
        if new_email != customer.email:
            existing = db.scalar(select(Customer).where(func.lower(Customer.email) == new_email))
            if existing:
                raise ConflictException("Another customer already has this email.", code="EMAIL_ALREADY_EXISTS")
            customer.email = new_email

    for field, value in update_data.items():
        if field != "email":
            setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


def list_customers(
    db: Session,
    requesting_user: User,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> CustomerListResponse:
    """Paginated and searchable customer listing (Admin & Staff only)."""
    if requesting_user.role not in ("admin", "staff"):
        raise ForbiddenException("Customers cannot access the full customer registry.", code="PERMISSION_DENIED")

    query = select(Customer)
    if status:
        query = query.where(Customer.status == status)
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Customer.name).like(search_filter),
                func.lower(Customer.email).like(search_filter),
                Customer.phone.like(search_filter)
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    items = db.scalars(
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return CustomerListResponse(
        items=[CustomerResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
