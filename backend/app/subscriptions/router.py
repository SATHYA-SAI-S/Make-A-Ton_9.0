import uuid
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.models import User
from app.auth.deps import get_current_user, require_roles, verify_internal_service_key
from app.subscriptions.models import Subscription, SubscriptionEvent
from app.subscriptions.schemas import (
    SubscriptionResponse,
    SubscriptionEventResponse,
    SubscriptionActionRequest,
    DueSubscriptionListResponse,
    AdvanceBillingRequest
)
from app.subscriptions import service

subscriptions_router = APIRouter(tags=["Subscriptions"])
internal_subscriptions_router = APIRouter(prefix="/internal/subscriptions", tags=["Internal Billing Integration"])


# Subscriptions Lifecycle Endpoints

@subscriptions_router.get("/subscriptions", response_model=List[SubscriptionResponse])
def list_subscriptions(
    customer_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List subscriptions (filtered by ownership for customers, all for staff/admin)."""
    return service.list_subscriptions(db, user=current_user, customer_id=customer_id, status=status)


@subscriptions_router.get("/subscriptions/me", response_model=List[SubscriptionResponse])
def get_my_subscriptions(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customer self-service portal: list own subscriptions."""
    return service.list_subscriptions(db, user=current_user, status=status)


@subscriptions_router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full subscription details."""
    return service.get_subscription(db, subscription_id, current_user)


@subscriptions_router.get("/subscriptions/{subscription_id}/events", response_model=List[SubscriptionEventResponse])
def get_subscription_events(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve complete audit event history for a subscription."""
    sub = service.get_subscription(db, subscription_id, current_user)
    return sub.events


@subscriptions_router.post("/subscriptions/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Activate confirmed subscription, setting next billing date."""
    return service.activate_subscription(db, subscription_id, current_user)


@subscriptions_router.post("/subscriptions/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: uuid.UUID,
    request: SubscriptionActionRequest,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Pause an active subscription (if plan allows)."""
    return service.pause_subscription(db, subscription_id, request.reason, current_user)


@subscriptions_router.post("/subscriptions/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: uuid.UUID,
    request: SubscriptionActionRequest,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Resume a paused subscription."""
    return service.resume_subscription(db, subscription_id, request.reason, current_user)


@subscriptions_router.post("/subscriptions/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: uuid.UUID,
    request: SubscriptionActionRequest,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Renew subscription term (if plan allows)."""
    return service.renew_subscription(db, subscription_id, request.reason, current_user)


@subscriptions_router.post("/subscriptions/{subscription_id}/close", response_model=SubscriptionResponse)
def close_subscription(
    subscription_id: uuid.UUID,
    request: SubscriptionActionRequest,
    current_user: User = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    """Close subscription early (if plan allows) or at end of term."""
    return service.close_subscription(db, subscription_id, request.reason, current_user)


# Person 2 Shared Inter-Service Contract Endpoints

@internal_subscriptions_router.get("/due", response_model=DueSubscriptionListResponse)
def get_due_subscriptions_internal(
    as_of: date = Query(..., description="Target billing date to evaluate"),
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    _verified: bool = Depends(verify_internal_service_key),
    db: Session = Depends(get_db)
):
    """
    Person 2 Billing Engine Contract:
    Retrieves active due subscriptions with snapshot lines.
    Protected by X-Internal-Service-Key header.
    """
    return service.get_due_subscriptions(db, as_of=as_of, cursor=cursor, limit=limit)


@internal_subscriptions_router.post("/{subscription_id}/advance-billing", response_model=SubscriptionResponse)
def advance_billing_internal(
    subscription_id: uuid.UUID,
    request: AdvanceBillingRequest,
    _verified: bool = Depends(verify_internal_service_key),
    db: Session = Depends(get_db)
):
    """
    Person 2 Billing Engine Callback:
    Advances next_billing_at after successful invoice creation with month-end day clamping.
    """
    return service.advance_next_billing(
        db=db,
        subscription_id=subscription_id,
        period_start=request.period_start,
        period_end=request.period_end
    )
