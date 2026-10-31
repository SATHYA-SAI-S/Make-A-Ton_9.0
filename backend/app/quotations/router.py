import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.models import User
from app.auth.deps import get_current_user, require_roles
from app.quotations.schemas import (
    QuotationTemplateCreate,
    QuotationTemplateResponse,
    QuotationCreate,
    QuotationResponse,
    QuotationExtendValidityRequest
)
from app.subscriptions.schemas import SubscriptionResponse
from app.quotations import service
from app.subscriptions import service as sub_service

quotations_router = APIRouter(tags=["Quotations & Templates"])


# Quotation Templates

@quotations_router.get("/quotation-templates", response_model=List[QuotationTemplateResponse])
def list_quotation_templates(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List reusable quotation templates."""
    return service.list_templates(db, is_active=is_active)


@quotations_router.post("/quotation-templates", response_model=QuotationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_template(
    request: QuotationTemplateCreate,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Create reusable quotation template (Admin & Staff)."""
    return service.create_template(db, request, current_user)


@quotations_router.get("/quotation-templates/{template_id}", response_model=QuotationTemplateResponse)
def get_quotation_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve quotation template by ID."""
    return service.get_template(db, template_id)


# Quotations

@quotations_router.get("/quotations", response_model=List[QuotationResponse])
def list_quotations(
    customer_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List quotations (filtered for customers to their own; all for staff)."""
    return service.list_quotations(db, requesting_user=current_user, customer_id=customer_id, status=status)


@quotations_router.post("/quotations", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    request: QuotationCreate,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Create quotation with snapshot unit prices (Admin & Staff)."""
    return service.create_quotation(db, request, current_user)


@quotations_router.get("/quotations/{quotation_id}", response_model=QuotationResponse)
def get_quotation(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve quotation details."""
    return service.get_quotation(db, quotation_id, current_user)


@quotations_router.post("/quotations/{quotation_id}/send", response_model=QuotationResponse)
def send_quotation(
    quotation_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Mark draft quotation as sent to customer."""
    return service.send_quotation(db, quotation_id, current_user)


@quotations_router.post("/quotations/{quotation_id}/confirm", response_model=SubscriptionResponse)
def confirm_quotation(
    quotation_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Confirm quotation, creating exactly one confirmed subscription idempotently."""
    return sub_service.confirm_quotation_to_subscription(db, quotation_id, current_user)


@quotations_router.post("/quotations/{quotation_id}/extend-validity", response_model=QuotationResponse)
def extend_quotation_validity(
    quotation_id: uuid.UUID,
    request: QuotationExtendValidityRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Admin-only extension of an expired or pending quotation's validity."""
    return service.extend_quotation_validity(db, quotation_id, request, current_user)


@quotations_router.post("/quotations/{quotation_id}/cancel", response_model=QuotationResponse)
def cancel_quotation(
    quotation_id: uuid.UUID,
    reason: str = Query("Cancelled by user"),
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Cancel quotation."""
    return service.cancel_quotation(db, quotation_id, reason, current_user)
