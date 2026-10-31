"""
Finance Visualizations & Chart Analytics API Router (P3-T08).
Exposes the 10 core analytics endpoints under /api/v1/finance/charts/.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import UserClaims, require_roles
from backend.app.finance.cohorts import (
    get_cohort_cell_customers,
    get_cohort_retention_matrix,
)
from backend.app.finance.concentration import get_detailed_revenue_concentration
from backend.app.finance.collections import (
    get_collection_funnel,
    get_forecast_baseline,
    get_invoice_aging_buckets,
    get_revenue_concentration,
)
from backend.app.finance.revenue import (
    get_mrr_trend,
    get_mrr_waterfall,
    get_revenue_performance,
)
from backend.app.finance.subscriptions import (
    get_cohort_retention,
    get_subscription_distribution,
    get_subscription_growth,
)

charts_router = APIRouter()


# 1. Invoiced versus collected revenue
@charts_router.get("/revenue-performance", summary="Chart 1: Invoiced vs Collected Revenue")
def chart_revenue_performance(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_revenue_performance(db=db, start_date=start_date, end_date=end_date, customer_id=customer_id)


# 2. Subscription distribution by frequency & plan
@charts_router.get("/subscription-distribution", summary="Chart 2: Subscription Distribution by Frequency & Plan")
def chart_subscription_distribution(
    as_of: Optional[date] = Query(None, description="As of date (YYYY-MM-DD)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_subscription_distribution(db=db, as_of=as_of, customer_id=customer_id)


# 3. Invoice aging buckets
@charts_router.get("/invoice-aging", summary="Chart 3: Invoice Aging Buckets (Current, 1-30, 31-60, 61-90, 90+)")
def chart_invoice_aging(
    as_of: Optional[date] = Query(None, description="As of date (YYYY-MM-DD)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_invoice_aging_buckets(db=db, as_of=as_of, customer_id=customer_id)


# 4. Subscription growth
@charts_router.get("/subscription-growth", summary="Chart 4: Subscription Growth (New, Renewed, Closed)")
def chart_subscription_growth(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_subscription_growth(db=db, start_date=start_date, end_date=end_date)


# 5. MRR / ARR trend
@charts_router.get("/mrr-trend", summary="Chart 5: MRR / ARR Trend with Rolling Average")
def chart_mrr_trend(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    plan_id: Optional[str] = Query(None, description="Filter by plan ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_mrr_trend(db=db, start_date=start_date, end_date=end_date, plan_id=plan_id, customer_id=customer_id)


# 6. MRR waterfall
@charts_router.get("/mrr-waterfall", summary="Chart 6: MRR Movement Waterfall")
def chart_mrr_waterfall(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_mrr_waterfall(db=db, start_date=start_date, end_date=end_date)


# 7. Cohort retention heatmap
@charts_router.get("/cohorts", summary="Chart 7: Cohort Retention Heatmap")
def chart_cohorts(
    lookback_months: int = Query(6, ge=1, le=24, description="Lookback months"),
    max_offsets: int = Query(6, ge=1, le=12, description="Max offset intervals"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_cohort_retention_matrix(db=db, lookback_months=lookback_months, max_offsets=max_offsets)


@charts_router.get("/cohorts/cell-customers", summary="Drilldown: Customers in Cohort Cell")
def chart_cohort_cell_customers(
    cohort: str = Query(..., description="Cohort month (YYYY-MM)"),
    offset: int = Query(0, ge=0, le=24, description="Month offset"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_cohort_cell_customers(db=db, cohort=cohort, offset=offset)


# 8. Revenue concentration
@charts_router.get("/concentration", summary="Chart 8: Revenue & MRR Pareto Concentration")
def chart_concentration(
    top_n: int = Query(10, ge=1, le=50, description="Top N customers"),
    sort_by: str = Query("mrr", description="Sort by 'mrr' or 'revenue'"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_detailed_revenue_concentration(db=db, top_n=top_n, sort_by=sort_by)


# 9. Payment collection funnel
@charts_router.get("/collection-funnel", summary="Chart 9: Payment Collection Funnel")
def chart_collection_funnel(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_collection_funnel(db=db, start_date=start_date, end_date=end_date, customer_id=customer_id)


# 10. Revenue forecast baseline
@charts_router.get("/forecast", summary="Chart 10: Revenue Forecast Baseline")
def chart_forecast(
    horizon_months: int = Query(12, ge=1, le=36, description="Forecast horizon in months"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    return get_forecast_baseline(db=db, horizon_months=horizon_months)
