"""
Finance Intelligence & KPI Router.
Exposes /api/v1/finance/overview and metric query endpoints for admin and staff.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import UserClaims, require_roles
from backend.app.finance.overview import get_finance_overview_data
from backend.app.finance.charts_router import charts_router
from backend.app.finance.export import export_router
from backend.app.finance.forecast_router import forecast_router

router = APIRouter()
router.include_router(charts_router, prefix="/charts", tags=["Finance Charts"])
router.include_router(export_router, tags=["Finance Export"])
router.include_router(forecast_router)


@router.get("/overview", summary="Get Finance Intelligence Overview KPIs")
def get_finance_overview(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    plan_id: Optional[str] = Query(None, description="Filter by plan ID"),
    frequency: Optional[str] = Query(None, description="Filter by billing frequency (DAILY, WEEKLY, MONTHLY, YEARLY)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by subscription status (ACTIVE, PAUSED, CLOSED)"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated financial KPIs with prior period comparison
    and percentage delta changes, adhering to docs/p3/metrics.md.
    """
    return get_finance_overview_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        plan_id=plan_id,
        frequency=frequency,
        customer_id=customer_id,
        status=status,
    )


@router.get("/kpis", summary="Get Structured Finance KPIs")
def get_finance_kpis(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    plan_id: Optional[str] = Query(None, description="Filter by plan ID"),
    frequency: Optional[str] = Query(None, description="Filter by billing frequency"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by subscription status"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """Alias endpoint for KPI dashboard widgets."""
    return get_finance_overview_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        plan_id=plan_id,
        frequency=frequency,
        customer_id=customer_id,
        status=status,
    )


@router.get("/metrics/definitions", summary="Financial Metric Definitions and Normalization Rules")
def get_metric_definitions(
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
):
    """
    Returns formal mathematical definitions and conventions
    from docs/p3/metrics.md for UI tooltips and documentation.
    """
    return {
        "mrr": {
            "name": "Monthly Recurring Revenue (MRR)",
            "description": "Normalized sum of recurring revenue from active subscriptions.",
            "normalization": {
                "DAILY": "Price * 365 / 12",
                "WEEKLY": "Price * 52 / 12",
                "MONTHLY": "Price",
                "YEARLY": "Price / 12",
            },
            "excluded_statuses": ["PAUSED", "CLOSED", "DRAFT"],
        },
        "arr": {
            "name": "Annual Recurring Revenue (ARR)",
            "formula": "MRR * 12",
        },
        "arpc": {
            "name": "Average Revenue Per Customer (ARPC)",
            "formula": "MRR / Active Customers",
        },
        "collection_rate": {
            "name": "Collection Rate (%)",
            "formula": "(Amount Collected / Amount Due) * 100",
        },
        "churn_rate": {
            "name": "Customer Churn Rate (%)",
            "formula": "(Lost Customers in Period / Active Customers at Start) * 100",
        },
    }
