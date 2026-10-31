"""
Finance & Chart Data CSV/PDF Export Service (P3-T09).
Provides streaming CSV export for any chart with active filters applied.
"""
import csv
from datetime import date
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import UserClaims, require_roles
from app.finance.collections import (
    get_collection_funnel,
    get_invoice_aging_buckets,
    get_revenue_concentration,
)
from app.finance.models import Invoice, Subscription
from app.finance.revenue import (
    get_mrr_trend,
    get_mrr_waterfall,
    get_revenue_performance,
)
from app.finance.subscriptions import (
    get_subscription_distribution,
    get_subscription_growth,
)

export_router = APIRouter()


@export_router.get("/export", summary="Export Chart or Drilldown Data as CSV")
def export_chart_data(
    chart: str = Query(..., description="Chart identifier or drilldown table (e.g., revenue-performance, invoice-aging, invoices)"),
    format: str = Query("csv", description="Export format (csv)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    plan_id: Optional[str] = Query(None),
    frequency: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    aging: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Exports filtered analytics or drilldown records to CSV with standard headers.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if chart == "revenue-performance":
        data = get_revenue_performance(db=db, start_date=start_date, end_date=end_date, customer_id=customer_id)
        writer.writerow(["Period", "Invoiced", "Collected", "Collection Rate %"])
        for row in data:
            writer.writerow([row["period"], row["invoiced"], row["collected"], row["collection_rate_pct"]])

    elif chart == "subscription-distribution":
        dist = get_subscription_distribution(db=db, as_of=end_date, customer_id=customer_id)
        writer.writerow(["Billing Frequency", "Count", "MRR Contribution", "Percentage of Subscriptions", "Percentage of MRR"])
        for row in dist["by_frequency"]:
            writer.writerow([row["frequency"], row["count"], row["mrr"], row["percentage_subs"], row["percentage_mrr"]])

    elif chart == "invoice-aging":
        aging_data = get_invoice_aging_buckets(db=db, as_of=end_date, customer_id=customer_id)
        writer.writerow(["Aging Bucket", "Count", "Outstanding Amount", "Percentage", "Risk Level"])
        for b in aging_data["buckets"]:
            writer.writerow([b["label"], b["count"], b["amount"], b["percentage"], b["risk_level"]])

    elif chart == "subscription-growth":
        growth = get_subscription_growth(db=db, start_date=start_date, end_date=end_date)
        writer.writerow(["Period", "New", "Renewed", "Closed", "Net Growth"])
        for g in growth:
            writer.writerow([g["period"], g["new"], g["renewed"], g["closed"], g["net_growth"]])

    elif chart == "mrr-trend":
        trend = get_mrr_trend(db=db, start_date=start_date, end_date=end_date, plan_id=plan_id, customer_id=customer_id)
        writer.writerow(["Period", "As Of Date", "MRR", "ARR", "Rolling 3M Average", "Growth %"])
        for t in trend:
            writer.writerow([t["period"], t["as_of_date"], t["mrr"], t["arr"], t["rolling_avg_3m"], t["growth_pct"]])

    elif chart == "collection-funnel":
        funnel = get_collection_funnel(db=db, start_date=start_date, end_date=end_date, customer_id=customer_id)
        writer.writerow(["Stage", "Label", "Count", "Amount", "Conversion %", "Dropoff %"])
        for s in funnel["stages"]:
            writer.writerow([s["stage"], s["label"], s["count"], s["amount"], s["conversion_pct"], s["dropoff_pct"]])

    elif chart in ("invoices", "drilldown_invoices"):
        # Export actual invoices matching drilldown filters
        q = db.query(Invoice).filter(Invoice.status != "CANCELLED")
        if customer_id:
            q = q.filter(Invoice.customer_id == customer_id)
        if start_date:
            q = q.filter(Invoice.invoice_date >= start_date)
        if end_date:
            q = q.filter(Invoice.invoice_date <= end_date)
        if status:
            q = q.filter(Invoice.status == status)

        writer.writerow(["Invoice Number", "Customer ID", "Status", "Invoice Date", "Due Date", "Total", "Amount Paid", "Balance"])
        for inv in q.limit(1000).all():
            writer.writerow([inv.number, inv.customer_id, inv.status, inv.invoice_date, inv.due_date, str(inv.total), str(inv.amount_paid), str(inv.balance)])

    else:
        writer.writerow(["Message"])
        writer.writerow([f"Export completed for {chart}"])

    csv_content = output.getvalue()
    filename = f"subscriptiq_export_{chart}_{date.today().isoformat()}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
