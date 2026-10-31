"""
Financial Reports REST Router.
Provides on-demand and streaming report downloads (JSON, CSV, PDF) for staff & admin:
1. Monthly Financial Pack
2. Revenue Ledger
3. Outstanding Invoices & Aging
4. Cash Payments & Settlements
5. Subscriptions Portfolio
6. Discount Performance
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import UserClaims, require_roles
from backend.app.reports.service import (
    generate_csv_stream,
    get_monthly_financial_report,
    get_revenue_report,
    get_outstanding_invoices_report,
    get_payments_report,
    get_subscriptions_report,
    get_discount_performance_report,
)
from backend.app.reports.pdf_generator import generate_report_pdf

router = APIRouter(tags=["Financial Reports"])


def _respond_report(report_data: dict, filename_slug: str, export_format: str) -> Response:
    """Helper to dispatch report as JSON, streaming CSV, or ReportLab PDF."""
    fmt = (export_format or "json").lower()
    headers = report_data["headers"]
    rows = report_data["rows"]

    if fmt == "csv":
        return StreamingResponse(
            generate_csv_stream(headers, rows),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_slug}.csv"'}
        )
    elif fmt == "pdf":
        pdf_bytes = generate_report_pdf(
            title=report_data["title"],
            subtitle=report_data["subtitle"],
            headers=headers,
            rows=rows,
            summary_kpis=report_data.get("summary")
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_slug}.pdf"'}
        )
    else:
        return Response(
            content=None,
            media_type="application/json"
        ) if False else report_data


@router.get("/catalog", summary="List Available Financial Reports")
def get_report_catalog(
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
):
    return {
        "reports": [
            {
                "id": "monthly-financial",
                "name": "Monthly Financial Pack",
                "description": "Comprehensive monthly revenue, collections, outstanding AR, and MRR metrics.",
                "supported_formats": ["json", "csv", "pdf"]
            },
            {
                "id": "revenue",
                "name": "Revenue & Invoicing Ledger",
                "description": "Itemized list of confirmed invoices, billing totals, and tax breakdowns.",
                "supported_formats": ["json", "csv", "pdf"]
            },
            {
                "id": "outstanding-invoices",
                "name": "Outstanding Receivables & Aging",
                "description": "Unpaid invoice balances categorized by overdue aging buckets.",
                "supported_formats": ["json", "csv", "pdf"]
            },
            {
                "id": "payments",
                "name": "Payments & Cash Collections Ledger",
                "description": "Recorded cash collections, payment methods, and invoice allocations.",
                "supported_formats": ["json", "csv", "pdf"]
            },
            {
                "id": "subscriptions",
                "name": "Subscriptions Portfolio",
                "description": "Active contracts, billing frequencies, and recurring MRR value.",
                "supported_formats": ["json", "csv", "pdf"]
            },
            {
                "id": "discount-performance",
                "name": "Discount Performance & Concessions",
                "description": "Redeemed promotional discounts, coupons, and concession impact.",
                "supported_formats": ["json", "csv", "pdf"]
            }
        ]
    }


@router.get("/monthly-financial", summary="Monthly Financial Pack Report")
def report_monthly_financial(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_monthly_financial_report(db=db, start_date=start_date, end_date=end_date)
    return _respond_report(data, "monthly_financial_pack", format)


@router.get("/revenue", summary="Revenue & Invoicing Ledger Report")
def report_revenue(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_revenue_report(db=db, start_date=start_date, end_date=end_date)
    return _respond_report(data, "revenue_ledger", format)


@router.get("/outstanding-invoices", summary="Outstanding Receivables & Aging Report")
def report_outstanding(
    as_of_date: Optional[date] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_outstanding_invoices_report(db=db, as_of_date=as_of_date)
    return _respond_report(data, "outstanding_invoices", format)


@router.get("/payments", summary="Payments & Collections Ledger Report")
def report_payments(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_payments_report(db=db, start_date=start_date, end_date=end_date)
    return _respond_report(data, "payments_ledger", format)


@router.get("/subscriptions", summary="Subscriptions Portfolio Report")
def report_subscriptions(
    status: Optional[str] = Query(None),
    plan_id: Optional[str] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_subscriptions_report(db=db, status=status, plan_id=plan_id)
    return _respond_report(data, "subscriptions_portfolio", format)


@router.get("/discount-performance", summary="Discount Performance Report")
def report_discounts(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    data = get_discount_performance_report(db=db, start_date=start_date, end_date=end_date)
    return _respond_report(data, "discount_performance", format)
