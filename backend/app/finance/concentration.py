"""
Revenue Concentration & Pareto Analysis Service (P3-T11).
Computes top customer dependency, cumulative shares, and plan-wise contributions.
Deterministic tie-breaking and 100% share conservation.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.core.money import to_money
from backend.app.finance.models import Customer, Invoice, Plan, Subscription, SubscriptionLine
from backend.app.finance.overview import compute_mrr_sql


@cached("revenue_concentration_analysis", ttl=300)
def get_detailed_revenue_concentration(
    db: Session,
    top_n: int = 10,
    sort_by: str = "mrr",  # "mrr" or "revenue"
) -> Dict[str, Any]:
    """
    Computes Pareto Revenue Concentration with deterministic tie-breaking.
    1. Evaluates all customers with active MRR or annual invoiced revenue.
    2. Calculates individual percentage share and cumulative dependency.
    3. Breaks down plan-wise contributions for each top customer.
    4. Guarantees that shares sum to 100.0%.
    """
    today = date.today()
    one_year_ago = today - timedelta(days=365)

    # 1. Total Active MRR across all customers
    total_mrr = compute_mrr_sql(db, as_of=today)

    # 2. Total Annual Invoiced across all non-cancelled invoices
    total_invoiced_stmt = select(func.coalesce(func.sum(Invoice.total), 0)).where(
        and_(Invoice.invoice_date >= one_year_ago, Invoice.status != "CANCELLED")
    )
    total_annual_invoiced = to_money(db.execute(total_invoiced_stmt).scalar_one_or_none() or Decimal("0.00"))

    # 3. Query all customers with their annual invoiced totals
    annual_inv_stmt = (
        select(
            Customer.id,
            Customer.name,
            Customer.email,
            func.coalesce(func.sum(Invoice.total), 0).label("annual_invoiced")
        )
        .select_from(Customer)
        .outerjoin(
            Invoice,
            and_(
                Customer.id == Invoice.customer_id,
                Invoice.invoice_date >= one_year_ago,
                Invoice.status != "CANCELLED"
            )
        )
        .group_by(Customer.id, Customer.name, Customer.email)
    )
    all_customer_rows = db.execute(annual_inv_stmt).fetchall()

    customer_metrics = []
    for cid, cname, cemail, inv_sum in all_customer_rows:
        inv_amt = to_money(inv_sum)
        c_mrr = compute_mrr_sql(db, as_of=today, customer_id=cid)

        # Skip accounts with 0 MRR and 0 revenue
        if inv_amt == Decimal("0.00") and c_mrr == Decimal("0.00"):
            continue

        # Get plan-wise breakdown for this customer
        active_subs = (
            db.query(Subscription)
            .filter(Subscription.customer_id == cid, Subscription.status == "ACTIVE")
            .all()
        )
        plan_breakdown = []
        for s in active_subs:
            sub_mrr = compute_mrr_sql(db, as_of=today, customer_id=cid, plan_id=s.plan_id)
            plan_breakdown.append({
                "plan_id": s.plan_id,
                "plan_name": s.plan.name if s.plan else s.plan_id,
                "frequency": s.plan.billing_frequency if s.plan else "MONTHLY",
                "mrr": str(sub_mrr),
            })

        customer_metrics.append({
            "customer_id": cid,
            "name": cname,
            "email": cemail,
            "annual_invoiced": inv_amt,
            "current_mrr": c_mrr,
            "plan_breakdown": plan_breakdown,
        })

    # Deterministic sorting with tie-breaking on customer_id
    if sort_by == "revenue":
        customer_metrics.sort(key=lambda c: (-c["annual_invoiced"], -c["current_mrr"], c["customer_id"]))
    else:
        customer_metrics.sort(key=lambda c: (-c["current_mrr"], -c["annual_invoiced"], c["customer_id"]))

    # Slice top N and "Others"
    top_slice = customer_metrics[:top_n]
    others_slice = customer_metrics[top_n:]

    top_customers_formatted = []
    running_mrr_share = Decimal("0.00")

    for c in top_slice:
        mrr_val = c["current_mrr"]
        inv_val = c["annual_invoiced"]

        mrr_share = ((mrr_val / total_mrr) * Decimal("100")).quantize(Decimal("0.01")) if total_mrr > Decimal("0.00") else Decimal("0.00")
        running_mrr_share += mrr_share

        top_customers_formatted.append({
            "customer_id": c["customer_id"],
            "customer_name": c["name"],
            "email": c["email"],
            "annual_invoiced": str(inv_val),
            "current_mrr": str(mrr_val),
            "mrr_share_pct": float(mrr_share),
            "cumulative_mrr_share_pct": float(running_mrr_share),
            "plan_breakdown": c["plan_breakdown"],
            "drilldown": {
                "label": f"View {c['name']} Profile",
                "url": f"/p3/finance/customers/{c['customer_id']}",
                "filters": {"customer_id": c["customer_id"]}
            }
        })

    # Others group aggregation
    others_mrr = sum((c["current_mrr"] for c in others_slice), Decimal("0.00"))
    others_inv = sum((c["annual_invoiced"] for c in others_slice), Decimal("0.00"))
    others_share = Decimal("100.00") - running_mrr_share if total_mrr > Decimal("0.00") else Decimal("0.00")

    # Dependency risk rating
    top_10_mrr_share = float(running_mrr_share)
    if top_10_mrr_share >= 80.0:
        risk_level = "CRITICAL_CONCENTRATION"
        risk_desc = "Top 10 customers represent over 80% of total recurring revenue (High single point of failure risk)."
    elif top_10_mrr_share >= 60.0:
        risk_level = "MODERATE_DEPENDENCY"
        risk_desc = "Top 10 customers represent 60%–80% of recurring revenue."
    else:
        risk_level = "HEALTHY_DIVERSIFICATION"
        risk_desc = "Recurring revenue is well-distributed across customer base."

    return {
        "as_of_date": today.isoformat(),
        "total_active_mrr": str(total_mrr),
        "total_annual_invoiced": str(total_annual_invoiced),
        "total_active_customers": len(customer_metrics),
        "top_customers": top_customers_formatted,
        "others_summary": {
            "customer_count": len(others_slice),
            "combined_mrr": str(to_money(others_mrr)),
            "combined_annual_invoiced": str(to_money(others_inv)),
            "mrr_share_pct": float(others_share),
        },
        "pareto_summary": {
            "top_10_mrr_share_pct": top_10_mrr_share,
            "risk_status": risk_level,
            "risk_description": risk_desc,
        }
    }
