"""
Customer Requests API Router.
Provides self-service request submission for Customers, and management review for Staff/Admin.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles, UserClaims
from app.core.pagination import PageParams, PageResponse
from app.portal.dependencies import get_portal_customer
from app.portal.requests_schemas import (
    CustomerRequestCreate,
    CustomerRequestReview,
    CustomerRequestDTO,
)
from app.portal import requests_service

router = APIRouter()

# --- Customer Endpoints ---

@router.post("", response_model=CustomerRequestDTO, summary="Submit Customer Request")
def submit_request(
    payload: CustomerRequestCreate,
    customer: Dict[str, Any] = Depends(get_portal_customer),
    db: Session = Depends(get_db)
):
    return requests_service.create_customer_request(
        db=db,
        customer=customer,
        subscription_id=payload.subscription_id,
        req_type=payload.type,
        target_plan_id=payload.target_plan_id,
        note=payload.note
    )

@router.get("", response_model=PageResponse[Dict[str, Any]], summary="List My Requests")
def list_my_requests(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED, APPLIED)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer: Dict[str, Any] = Depends(get_portal_customer),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = requests_service.list_customer_requests(
        db=db,
        customer_id=customer["id"],
        status=status,
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@router.get("/{id}", response_model=CustomerRequestDTO, summary="Get Request Detail")
def get_my_request_detail(
    id: str = Path(..., description="Request UUID"),
    customer: Dict[str, Any] = Depends(get_portal_customer),
    db: Session = Depends(get_db)
):
    req = requests_service.get_customer_request_by_id(db, id)
    if req.customer_id != customer["id"]:
        from app.core.errors import NotFoundError
        raise NotFoundError("CustomerRequest", id)
    return req.to_dict()

# --- Staff / Admin Review Endpoints ---

admin_router = APIRouter()

@admin_router.get("", response_model=PageResponse[Dict[str, Any]], summary="Staff: List All Requests")
def list_all_requests_staff(
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    params = PageParams(page=page, page_size=page_size)
    items, total = requests_service.list_customer_requests(
        db=db,
        customer_id=customer_id,
        status=status,
        offset=params.offset,
        limit=params.limit
    )
    return PageResponse.create(items=items, total=total, params=params)

@admin_router.post("/{id}/review", response_model=CustomerRequestDTO, summary="Staff: Review Customer Request")
def review_request_staff(
    id: str = Path(..., description="Request UUID"),
    payload: CustomerRequestReview = ...,
    user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    return requests_service.review_customer_request(
        db=db,
        request_id=id,
        action=payload.action,
        decision_note=payload.decision_note,
        staff_user_id=user.id
    )
