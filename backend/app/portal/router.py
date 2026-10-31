"""
Customer Portal API Router.
All routes require an authenticated customer account.
Enforces multi-tenant data isolation.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, Response
from fastapi.responses import JSONResponse

from backend.app.portal.dependencies import get_portal_customer
from backend.app.portal.schemas import (
    CustomerProfileDTO,
    CustomerProfileUpdate,
    PortalDashboardSummary,
    PortalOutstandingBalanceResponse,
)
from backend.app.portal import service
from backend.app.portal.requests_router import router as requests_sub_router, admin_router as requests_admin_sub_router

router = APIRouter()

router.include_router(requests_sub_router, prefix="/requests", tags=["Customer Requests"])
router.include_router(requests_admin_sub_router, prefix="/admin/requests", tags=["Customer Requests Admin"])

@router.get("/dashboard", response_model=PortalDashboardSummary, summary="Customer Portal Dashboard Summary")
def get_dashboard(
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.get_portal_dashboard(customer)

@router.get("/subscriptions", response_model=List[Dict[str, Any]], summary="My Subscriptions")
def list_my_subscriptions(
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, PAUSED, CLOSED)"),
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.list_customer_subscriptions(customer, status_filter=status)

@router.get("/subscriptions/{id}", response_model=Dict[str, Any], summary="My Subscription Detail & Timeline")
def get_my_subscription_detail(
    id: str = Path(..., description="Subscription ID"),
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.get_customer_subscription_detail(customer, id)

@router.get("/invoices", response_model=List[Dict[str, Any]], summary="My Invoices")
def list_my_invoices(
    status: Optional[str] = Query(None, description="Filter by invoice status"),
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.list_customer_invoices(customer, status_filter=status)

@router.get("/invoices/{id}", response_model=Dict[str, Any], summary="My Invoice Detail")
def get_my_invoice_detail(
    id: str = Path(..., description="Invoice ID"),
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.get_customer_invoice_detail(customer, id)

@router.get("/invoices/{id}/pdf", summary="Download Invoice PDF")
def download_invoice_pdf(
    id: str = Path(..., description="Invoice ID"),
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    pdf_bytes, filename = service.get_customer_invoice_pdf(customer, id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/payments", response_model=List[Dict[str, Any]], summary="My Payment History")
def list_my_payments(
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.list_customer_payments(customer)

@router.get("/balance", response_model=PortalOutstandingBalanceResponse, summary="My Outstanding Balance")
def get_my_balance(
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.get_customer_balance(customer)

@router.get("/profile", response_model=CustomerProfileDTO, summary="My Customer Profile")
def get_my_profile(
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return customer

@router.patch("/profile", response_model=CustomerProfileDTO, summary="Update Customer Profile")
def update_my_profile(
    payload: CustomerProfileUpdate,
    customer: Dict[str, Any] = Depends(get_portal_customer)
):
    return service.update_customer_profile(customer, payload.model_dump(exclude_unset=True))
