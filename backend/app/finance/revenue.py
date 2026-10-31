"""
Revenue Analytics & Chart Calculations (P3-T08).
Computes Invoiced vs Collected performance, MRR trend, and MRR movement waterfall.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.analytics.metrics import calculate_pct_change, normalize_mrr
from backend.app.core.money import to_money
from backend.app.finance.models import Invoice, Payment, Plan, Refund, Subscription, SubscriptionLine
from backend.app.finance.overview import compute_mrr_sql


@cached("chart_revenue_performance", ttl=300)
def get_revenue_performance(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns monthly invoiced vs collected revenue with net collection percentage
    and structured drilldown links.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=180)  # past 6 months

    # Monthly Invoiced
    inv_conds = [
        Invoice.status != "CANCELLED",
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
    ]
    if customer_id:
        inv_conds.append(Invoice.customer_id == customer_id)

    # Invoices by month
    inv_stmt = (
        select(
            func.substr(Invoice.invoice_date, 1, 7).label("month"),
            func.coalesce(func.sum(Invoice.total), 0).label("invoiced")
        )
        .where(and_(*inv_conds))
        .group_by(func.substr(Invoice.invoice_date, 1, 7))
        .order_by("month")
    )
    invoiced_by_month = {r[0]: to_money(r[1]) for r in db.execute(inv_stmt).fetchall()}

    # Monthly Collected (Payments - Refunds)
    pay_conds = [
        Payment.status == "RECORDED",
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
    ]
    if customer_id:
        pay_conds.append(Payment.customer_id == customer_id)

    pay_stmt = (
        select(
            func.substr(Payment.payment_date, 1, 7).label("month"),
            func.coalesce(func.sum(Payment.amount), 0).label("payments")
        )
        .where(and_(*pay_conds))
        .group_by(func.substr(Payment.payment_date, 1, 7))
        .order_by("month")
    )
    payments_by_month = {r[0]: to_money(r[1]) for r in db.execute(pay_stmt).fetchall()}

    ref_conds = [
        Refund.status == "PROCESSED",
        Refund.refund_date >= start_date,
        Refund.refund_date <= end_date,
    ]
    if customer_id:
        ref_conds.append(Refund.customer_id == customer_id)

    ref_stmt = (
        select(
            func.substr(Refund.refund_date, 1, 7).label("month"),
            func.coalesce(func.sum(Refund.amount), 0).label("refunds")
        )
        .where(and_(*ref_conds))
        .group_by(func.substr(Refund.refund_date, 1, 7))
        .order_by("month")
    )
    refunds_by_month = {r[0]: to_money(r[1]) for r in db.execute(ref_stmt).fetchall()}

    # Merge all unique months in sorted order
    all_months = sorted(set(list(invoiced_by_month.keys()) + list(payments_by_month.keys())))
    if not all_months:
        return []

    data = []
    for m in all_months:
        inv = invoiced_by_month.get(m, Decimal("0.00"))
        pay = payments_by_month.get(m, Decimal("0.00"))
        ref = refunds_by_month.get(m, Decimal("0.00"))
        coll = to_money(pay - ref)

        rate = Decimal("0.00")
        if inv > Decimal("0.00"):
            rate = ((coll / inv) * Decimal("100")).quantize(Decimal("0.01"))
        elif coll > Decimal("0.00"):
            rate = Decimal("100.00")

        data.append({
            "period": m,
            "invoiced": str(inv),
            "collected": str(coll),
            "collection_rate_pct": float(rate),
            "drilldown": {
                "label": f"View Invoices for {m}",
                "url": f"/p3/finance/invoices?period={m}" + (f"&customer_id={customer_id}" if customer_id else ""),
                "filters": {"period": m, "customer_id": customer_id}
            }
        })
    return data


@cached("chart_mrr_trend", ttl=300)
def get_mrr_trend(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    plan_id: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns monthly MRR and ARR trajectory with rolling averages and percentage growth.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=180)

    # Generate list of month end dates between start_date and end_date
    cur = date(start_date.year, start_date.month, 1)
    month_ends = []
    while cur <= end_date:
        if cur.month == 12:
            next_m = date(cur.year + 1, 1, 1)
        else:
            next_m = date(cur.year, cur.month + 1, 1)
        m_end = next_m - timedelta(days=1)
        if m_end <= end_date or cur <= end_date:
            month_ends.append(min(m_end, end_date))
        cur = next_m

    results = []
    prev_mrr = Decimal("0.00")
    mrr_history: List[Decimal] = []

    for m_end in month_ends:
        period_key = f"{m_end.year:04d}-{m_end.month:02d}"
        mrr = compute_mrr_sql(db, as_of=m_end, plan_id=plan_id, customer_id=customer_id)
        arr = to_money(mrr * Decimal("12"))

        # Rolling 3-month average
        mrr_history.append(mrr)
        recent_3 = mrr_history[-3:]
        rolling_avg = (sum(recent_3) / Decimal(len(recent_3))).quantize(Decimal("0.01"))

        growth_pct = calculate_pct_change(mrr, prev_mrr) if prev_mrr > Decimal("0.00") else Decimal("0.00")
        prev_mrr = mrr

        results.append({
            "period": period_key,
            "as_of_date": m_end.isoformat(),
            "mrr": str(mrr),
            "arr": str(arr),
            "rolling_avg_3m": str(rolling_avg),
            "growth_pct": float(growth_pct),
            "drilldown": {
                "label": f"Active Subscriptions as of {period_key}",
                "url": f"/p3/finance/subscriptions?as_of={m_end.isoformat()}" + (f"&plan_id={plan_id}" if plan_id else ""),
                "filters": {"as_of": m_end.isoformat(), "plan_id": plan_id, "customer_id": customer_id}
            }
        })
    return results


@cached("chart_mrr_waterfall", ttl=300)
def get_mrr_waterfall(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    MRR movement waterfall:
    Ending MRR = Starting MRR + New + Expansion - Contraction - Churned.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    starting_mrr = compute_mrr_sql(db, as_of=start_date)
    ending_mrr = compute_mrr_sql(db, as_of=end_date)

    # Compute new subscriptions MRR started in period
    new_subs = (
        db.query(Subscription)
        .filter(Subscription.start_date >= start_date, Subscription.start_date <= end_date, Subscription.status == "ACTIVE")
        .all()
    )
    new_mrr = Decimal("0.00")
    for s in new_subs:
        new_mrr += normalize_mrr(s.plan.price if s.plan else Decimal("0.00"), s.plan.billing_frequency if s.plan else "MONTHLY")

    # Closed subscriptions in period
    closed_subs = (
        db.query(Subscription)
        .filter(
            Subscription.status == "CLOSED",
            Subscription.expiry_date >= start_date,
            Subscription.expiry_date <= end_date,
        )
        .all()
    )
    churn_mrr = Decimal("0.00")
    for s in closed_subs:
        churn_mrr += normalize_mrr(s.plan.price if s.plan else Decimal("0.00"), s.plan.billing_frequency if s.plan else "MONTHLY")

    # Expansion / Contraction balance
    diff = ending_mrr - (starting_mrr + new_mrr - churn_mrr)
    expansion_mrr = diff if diff > Decimal("0.00") else Decimal("0.00")
    contraction_mrr = abs(diff) if diff < Decimal("0.00") else Decimal("0.00")

    return {
        "starting_mrr": str(starting_mrr),
        "new_mrr": str(to_money(new_mrr)),
        "expansion_mrr": str(to_money(expansion_mrr)),
        "contraction_mrr": str(to_money(contraction_mrr)),
        "churn_mrr": str(to_money(churn_mrr)),
        "ending_mrr": str(ending_mrr),
        "steps": [
            {"category": "Starting MRR", "value": str(starting_mrr), "type": "baseline"},
            {"category": "New Subscriptions", "value": str(to_money(new_mrr)), "type": "positive"},
            {"category": "Expansion", "value": str(to_money(expansion_mrr)), "type": "positive"},
            {"category": "Contraction", "value": str(to_money(-contraction_mrr)), "type": "negative"},
            {"category": "Churn", "value": str(to_money(-churn_mrr)), "type": "negative"},
            {"category": "Ending MRR", "value": str(ending_mrr), "type": "total"},
        ],
        "drilldown": {
            "label": "View Subscription Movements",
            "url": f"/p3/finance/subscriptions?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            "filters": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
        }
    }
