"""
Audit API Endpoints.
Accessible by Admin and Staff. Append-Only.
Provides filters, before/after diff rendering, and ready-made audit views.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_roles, UserClaims
from backend.app.core.pagination import PageParams, PageResponse
from backend.app.core.errors import NotFoundError
from backend.app.audit.models import AuditLog
from backend.app.audit.service import query_audit_logs, compute_diff

router = APIRouter()

@router.get("/logs", response_model=PageResponse[Dict[str, Any]], summary="List Audit Logs")
def list_audit_logs(
    actor_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    actor_role: Optional[str] = Query(None, description="Filter by actor role (admin, staff, customer, system)"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (plan, product, subscription, invoice)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    start_date: Optional[datetime] = Query(None, description="Logs occurred on or after this timestamp"),
    end_date: Optional[datetime] = Query(None, description="Logs occurred on or before this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = query_audit_logs(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@router.get("/logs/{id}", summary="Get Audit Log Detail & Diff")
def get_audit_log_detail(
    id: str = Path(..., description="Audit log UUID"),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    log = db.query(AuditLog).filter(AuditLog.id == id).first()
    if not log:
        raise NotFoundError("AuditLog", id)
    
    data = log.to_dict()
    data["diff"] = compute_diff(log.before, log.after)
    return data

@router.get("/views/price-history", summary="Product Price Modification History")
def get_price_modification_history(
    product_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = query_audit_logs(
        db=db,
        entity_type="product",
        entity_id=product_id,
        action="product.price_changed",
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@router.get("/views/plan-history", summary="Plan Modification History")
def get_plan_modification_history(
    plan_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = query_audit_logs(
        db=db,
        entity_type="plan",
        entity_id=plan_id,
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@router.get("/views/invoice-cancellations", summary="Invoice Cancellations History")
def get_invoice_cancellations_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = query_audit_logs(
        db=db,
        entity_type="invoice",
        action="invoice.cancelled",
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@router.get("/views/subscription-lifecycle", summary="Subscription Lifecycle Transitions")
def get_subscription_lifecycle_history(
    subscription_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = query_audit_logs(
        db=db,
        entity_type="subscription",
        entity_id=subscription_id,
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)
