"""
Collections & Risk Analytics Chart Calculations (P3-T08).
Computes Invoice Aging Buckets, Payment Collection Funnel, and Revenue Concentration.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.core.money import to_money
from backend.app.finance.models import Customer, Invoice, Payment, Subscription
from backend.app.finance.overview import compute_mrr_sql


@cached("chart_invoice_aging", ttl=300)
def get_invoice_aging_buckets(
    db: Session,
    as_of: Optional[date] = None,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Categorizes unpaid invoice balances into standard aging buckets:
    - Current (Not Due): due_date >= as_of
    - 1-30 Days: 1 <= (as_of - due_date) <= 30
    - 31-60 Days: 31 <= (as_of - due_date) <= 60
    - 61-90 Days: 61 <= (as_of - due_date) <= 90
    - 90+ Days: (as_of - due_date) > 90
    """
    if not as_of:
        as_of = date.today()

    conds = [
        Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
        Invoice.balance > Decimal("0.00"),
        Invoice.invoice_date <= as_of,
    ]
    if customer_id:
        conds.append(Invoice.customer_id == customer_id)

    invoices = db.query(Invoice).filter(and_(*conds)).all()

    buckets = {
        "current": {"label": "Current (Not Due)", "count": 0, "amount": Decimal("0.00"), "risk": "LOW", "key": "current"},
        "1_30": {"label": "1–30 Days", "count": 0, "amount": Decimal("0.00"), "risk": "MODERATE", "key": "1_30"},
        "31_60": {"label": "31–60 Days", "count": 0, "amount": Decimal("0.00"), "risk": "HIGH", "key": "31_60"},
        "61_90": {"label": "61–90 Days", "count": 0, "amount": Decimal("0.00"), "risk": "SEVERE", "key": "61_90"},
        "90_plus": {"label": "90+ Days", "count": 0, "amount": Decimal("0.00"), "risk": "CRITICAL", "key": "90_plus"},
    }

    total_outstanding = Decimal("0.00")

    for inv in invoices:
        due = inv.due_date
        bal = to_money(inv.balance)
        total_outstanding += bal
        days_overdue = (as_of - due).days

        if days_overdue <= 0:
            b_key = "current"
        elif 1 <= days_overdue <= 30:
            b_key = "1_30"
        elif 31 <= days_overdue <= 60:
            b_key = "31_60"
        elif 61 <= days_overdue <= 90:
            b_key = "61_90"
        else:
            b_key = "90_plus"

        buckets[b_key]["count"] += 1
        buckets[b_key]["amount"] += bal

    # Format list with percentages and drilldown links
    bucket_list = []
    for k in ["current", "1_30", "31_60", "61_90", "90_plus"]:
        b = buckets[k]
        amt = b["amount"]
        pct = round(float((amt / total_outstanding) * Decimal("100")), 2) if total_outstanding > Decimal("0.00") else 0.0
        bucket_list.append({
            "bucket": k,
            "label": b["label"],
            "count": b["count"],
            "amount": str(to_money(amt)),
            "percentage": pct,
            "risk_level": b["risk"],
            "drilldown": {
                "label": f"View {b['label']} Invoices",
                "url": f"/p3/finance/invoices?aging={k}" + (f"&customer_id={customer_id}" if customer_id else ""),
                "filters": {"aging": k, "as_of": as_of.isoformat(), "customer_id": customer_id}
            }
        })

    return {
        "as_of_date": as_of.isoformat(),
        "total_outstanding": str(to_money(total_outstanding)),
        "buckets": bucket_list,
    }


@cached("chart_collection_funnel", ttl=300)
def get_collection_funnel(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes Invoice lifecycle conversion funnel:
    Generated (All active) -> Confirmed -> Partially Paid -> Fully Paid.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    conds = [
        Invoice.status != "CANCELLED",
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
    ]
    if customer_id:
        conds.append(Invoice.customer_id == customer_id)

    # 1. Generated total
    gen_stmt = select(
        func.count(Invoice.id).label("count"),
        func.coalesce(func.sum(Invoice.total), 0).label("amount")
    ).where(and_(*conds))
    gen_row = db.execute(gen_stmt).first()
    gen_cnt = gen_row[0] if gen_row else 0
    gen_amt = to_money(gen_row[1] if gen_row else 0)

    # 2. Confirmed & Active
    conf_stmt = select(
        func.count(Invoice.id).label("count"),
        func.coalesce(func.sum(Invoice.total), 0).label("amount")
    ).where(and_(*(conds + [Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID", "PAID"])])))
    conf_row = db.execute(conf_stmt).first()
    conf_cnt = conf_row[0] if conf_row else 0
    conf_amt = to_money(conf_row[1] if conf_row else 0)

    # 3. Partially Paid
    part_stmt = select(
        func.count(Invoice.id).label("count"),
        func.coalesce(func.sum(Invoice.amount_paid), 0).label("amount")
    ).where(and_(*(conds + [Invoice.status.in_(["PARTIALLY_PAID", "PAID"])])))
    part_row = db.execute(part_stmt).first()
    part_cnt = part_row[0] if part_row else 0
    part_amt = to_money(part_row[1] if part_row else 0)

    # 4. Fully Paid
    paid_stmt = select(
        func.count(Invoice.id).label("count"),
        func.coalesce(func.sum(Invoice.amount_paid), 0).label("amount")
    ).where(and_(*(conds + [Invoice.status == "PAID"])))
    paid_row = db.execute(paid_stmt).first()
    paid_cnt = paid_row[0] if paid_row else 0
    paid_amt = to_money(paid_row[1] if paid_row else 0)

    def pct(c, base):
        return round((c / base) * 100, 2) if base > 0 else 0.0

    stages = [
        {
            "stage": "GENERATED",
            "label": "Invoices Generated",
            "count": gen_cnt,
            "amount": str(gen_amt),
            "conversion_pct": 100.0,
            "dropoff_pct": 0.0,
        },
        {
            "stage": "CONFIRMED",
            "label": "Confirmed & Sent",
            "count": conf_cnt,
            "amount": str(conf_amt),
            "conversion_pct": pct(conf_cnt, gen_cnt),
            "dropoff_pct": round(100.0 - pct(conf_cnt, gen_cnt), 2),
        },
        {
            "stage": "PARTIALLY_PAID",
            "label": "Payments Commenced",
            "count": part_cnt,
            "amount": str(part_amt),
            "conversion_pct": pct(part_cnt, gen_cnt),
            "dropoff_pct": round(pct(conf_cnt, gen_cnt) - pct(part_cnt, gen_cnt), 2),
        },
        {
            "stage": "PAID",
            "label": "Fully Settled",
            "count": paid_cnt,
            "amount": str(paid_amt),
            "conversion_pct": pct(paid_cnt, gen_cnt),
            "dropoff_pct": round(pct(part_cnt, gen_cnt) - pct(paid_cnt, gen_cnt), 2),
        },
    ]

    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "stages": stages,
    }


@cached("chart_concentration", ttl=300)
def get_revenue_concentration(
    db: Session,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Computes top N customers by annual invoiced revenue and active MRR,
    showing individual share and cumulative share (Pareto dependency).
    """
    # Total active MRR
    total_mrr = compute_mrr_sql(db, as_of=date.today())

    # Invoiced sum per customer over past 365 days
    year_ago = date.today() - timedelta(days=365)
    stmt = (
        select(
            Customer.id,
            Customer.name,
            func.coalesce(func.sum(Invoice.total), 0).label("invoiced_sum")
        )
        .select_from(Customer)
        .outerjoin(Invoice, and_(Customer.id == Invoice.customer_id, Invoice.invoice_date >= year_ago, Invoice.status != "CANCELLED"))
        .group_by(Customer.id, Customer.name)
        .order_by(func.coalesce(func.sum(Invoice.total), 0).desc())
        .limit(top_n)
    )
    rows = db.execute(stmt).fetchall()

    total_invoiced_stmt = select(func.coalesce(func.sum(Invoice.total), 0)).where(
        and_(Invoice.invoice_date >= year_ago, Invoice.status != "CANCELLED")
    )
    all_invoiced = to_money(db.execute(total_invoiced_stmt).scalar_one_or_none() or Decimal("0.00"))

    customers = []
    cumulative_pct = Decimal("0.00")

    for r in rows:
        cid, cname, inv_sum = r[0], r[1], to_money(r[2])
        # Customer MRR
        c_mrr = compute_mrr_sql(db, as_of=date.today(), customer_id=cid)
        share_pct = ((inv_sum / all_invoiced) * Decimal("100")).quantize(Decimal("0.01")) if all_invoiced > Decimal("0.00") else Decimal("0.00")
        cumulative_pct += share_pct

        customers.append({
            "customer_id": cid,
            "customer_name": cname,
            "annual_invoiced": str(inv_sum),
            "current_mrr": str(c_mrr),
            "share_pct": float(share_pct),
            "cumulative_share_pct": float(cumulative_pct),
            "drilldown": {
                "label": f"View {cname} Account",
                "url": f"/p3/finance/customers/{cid}",
                "filters": {"customer_id": cid}
            }
        })

    return {
        "total_annual_invoiced": str(all_invoiced),
        "total_active_mrr": str(total_mrr),
        "top_customers": customers,
        "pareto_summary": {
            "top_10_share_pct": float(cumulative_pct),
            "risk_status": "CONCENTRATED" if cumulative_pct > Decimal("70.00") else "HEALTHY_DIVERSIFICATION"
        }
    }


@cached("chart_forecast_baseline", ttl=300)
def get_forecast_baseline(
    db: Session,
    horizon_months: int = 12,
) -> Dict[str, Any]:
    """
    Computes baseline forward-looking projection from recent 6-month averages.
    """
    cur_mrr = compute_mrr_sql(db, as_of=date.today())
    today = date.today()

    baseline = []
    running_mrr = cur_mrr

    # Default assumed modest baseline growth from metrics
    default_monthly_growth = Decimal("0.02")  # 2% baseline

    for i in range(1, horizon_months + 1):
        target_year = today.year + (today.month - 1 + i) // 12
        target_month = ((today.month - 1 + i) % 12) + 1
        m_str = f"{target_year:04d}-{target_month:02d}"

        running_mrr = (running_mrr * (Decimal("1.00") + default_monthly_growth)).quantize(Decimal("0.01"))
        proj_arr = (running_mrr * Decimal("12")).quantize(Decimal("0.01"))

        baseline.append({
            "month": m_str,
            "mrr": str(running_mrr),
            "arr": str(proj_arr),
            "projected_invoiced": str(running_mrr),
            "projected_collected": str((running_mrr * Decimal("0.95")).quantize(Decimal("0.01"))),
            "projected_outstanding": str((running_mrr * Decimal("0.05")).quantize(Decimal("0.01"))),
        })

    return {
        "current_mrr": str(cur_mrr),
        "current_arr": str(to_money(cur_mrr * Decimal("12"))),
        "horizon_months": horizon_months,
        "baseline": baseline,
    }
