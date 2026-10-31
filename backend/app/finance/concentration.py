"""
Revenue Concentration & Pareto Analysis Service (P3-T11).
Computes top customer dependency, cumulative shares, and plan-wise contributions.
Deterministic tie-breaking and 100% share conservation.
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, select, or_
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.core.money import to_money
from backend.app.finance.models import Customer, Invoice, Plan, Subscription, SubscriptionLine
from backend.app.finance.overview import compute_mrr_sql, normalize_mrr


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

    # 3. Query all active subscriptions in a single aggregated batch (O(1) database hit)
    active_subs_stmt = (
        select(
            Subscription.customer_id,
            Subscription.plan_id,
            Plan.name.label("plan_name"),
            Plan.billing_frequency,
            Plan.price.label("plan_price"),
            func.coalesce(func.sum(SubscriptionLine.quantity * SubscriptionLine.unit_price), 0).label("lines_sum")
        )
        .select_from(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .outerjoin(SubscriptionLine, Subscription.id == SubscriptionLine.subscription_id)
        .where(
            and_(
                Subscription.status == "ACTIVE",
                Subscription.start_date <= today,
                or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= today)
            )
        )
        .group_by(Subscription.id, Subscription.customer_id, Subscription.plan_id, Plan.name, Plan.billing_frequency, Plan.price)
    )
    all_subs_rows = db.execute(active_subs_stmt).fetchall()

    customer_mrr_map: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    customer_plans_map: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    for cid, pid, pname, freq, pprice, lsum in all_subs_rows:
        base_price = to_money(lsum) if lsum and lsum > 0 else to_money(pprice)
        sub_mrr = normalize_mrr(base_price, freq)
        customer_mrr_map[cid] += sub_mrr
        customer_plans_map[cid].append({
            "plan_id": pid,
            "plan_name": pname or pid,
            "frequency": freq,
            "mrr": str(sub_mrr),
        })

    # 4. Query all customers with their annual invoiced totals
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
        c_mrr = customer_mrr_map.get(cid, Decimal("0.00"))

        # Skip accounts with 0 MRR and 0 revenue
        if inv_amt == Decimal("0.00") and c_mrr == Decimal("0.00"):
            continue

        customer_metrics.append({
            "customer_id": cid,
            "name": cname,
            "email": cemail,
            "annual_invoiced": inv_amt,
            "current_mrr": c_mrr,
            "plan_breakdown": customer_plans_map.get(cid, []),
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
