"""
Subscription Analytics & Chart Calculations (P3-T08).
Computes Subscription Distribution by frequency/tier, Subscription Growth, and Cohorts.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.analytics.metrics import normalize_mrr
from backend.app.core.money import to_money
from backend.app.finance.models import Customer, Plan, Subscription


@cached("chart_subscription_distribution", ttl=300)
def get_subscription_distribution(
    db: Session,
    as_of: Optional[date] = None,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns active subscription distribution broken down by:
    1. Billing Frequency (DAILY, WEEKLY, MONTHLY, YEARLY)
    2. Plan Tier / Plan ID
    Each slice includes count, MRR contribution, percentage, and drilldown link.
    """
    if not as_of:
        as_of = date.today()

    conds = [
        Subscription.status == "ACTIVE",
        Subscription.start_date <= as_of,
    ]
    if customer_id:
        conds.append(Subscription.customer_id == customer_id)

    # 1. Distribution by Billing Frequency
    freq_stmt = (
        select(
            func.upper(Plan.billing_frequency).label("frequency"),
            func.count(Subscription.id).label("count"),
            func.coalesce(func.sum(Plan.price), 0).label("raw_price_sum")
        )
        .select_from(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(and_(*conds))
        .group_by(func.upper(Plan.billing_frequency))
    )
    freq_rows = db.execute(freq_stmt).fetchall()

    total_subs = sum(r[1] for r in freq_rows)
    by_frequency = []
    total_mrr = Decimal("0.00")

    # Compute normalized MRR per frequency
    for r in freq_rows:
        freq = r[0] or "MONTHLY"
        cnt = int(r[1])
        raw_price = to_money(r[2])
        # Each subscription's average normalized price
        norm_mrr = normalize_mrr(raw_price, freq)
        total_mrr += norm_mrr

        by_frequency.append({
            "frequency": freq,
            "count": cnt,
            "mrr": str(norm_mrr),
            "percentage_subs": round((cnt / total_subs) * 100, 2) if total_subs > 0 else 0.0,
            "drilldown": {
                "label": f"Filter {freq} Subscriptions",
                "url": f"/p3/finance/subscriptions?frequency={freq}",
                "filters": {"frequency": freq}
            }
        })

    # Add MRR percentage to frequencies
    for item in by_frequency:
        mrr_val = Decimal(item["mrr"])
        item["percentage_mrr"] = round(float((mrr_val / total_mrr) * Decimal("100")), 2) if total_mrr > 0 else 0.0

    # 2. Distribution by Plan
    plan_stmt = (
        select(
            Plan.id.label("plan_id"),
            Plan.name.label("plan_name"),
            func.upper(Plan.billing_frequency).label("frequency"),
            func.count(Subscription.id).label("count"),
            func.coalesce(func.sum(Plan.price), 0).label("raw_price_sum")
        )
        .select_from(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(and_(*conds))
        .group_by(Plan.id, Plan.name, func.upper(Plan.billing_frequency))
    )
    plan_rows = db.execute(plan_stmt).fetchall()

    by_plan = []
    for r in plan_rows:
        pid, pname, freq, cnt, raw_price = r[0], r[1], r[2] or "MONTHLY", int(r[3]), to_money(r[4])
        norm_mrr = normalize_mrr(raw_price, freq)
        pct = round(float((norm_mrr / total_mrr) * Decimal("100")), 2) if total_mrr > 0 else 0.0
        by_plan.append({
            "plan_id": pid,
            "plan_name": pname,
            "frequency": freq,
            "count": cnt,
            "mrr": str(norm_mrr),
            "percentage_mrr": pct,
            "drilldown": {
                "label": f"Filter by {pname}",
                "url": f"/p3/finance/subscriptions?plan_id={pid}",
                "filters": {"plan_id": pid}
            }
        })

    return {
        "as_of_date": as_of.isoformat(),
        "total_active_subscriptions": total_subs,
        "total_mrr": str(total_mrr),
        "by_frequency": by_frequency,
        "by_plan": by_plan,
    }


@cached("chart_subscription_growth", ttl=300)
def get_subscription_growth(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Returns monthly subscription movements: new, renewed, closed, and net growth.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=180)

    # 1. New subscriptions by month
    new_stmt = (
        select(
            func.substr(Subscription.start_date, 1, 7).label("month"),
            func.count(Subscription.id).label("count")
        )
        .where(
            and_(
                Subscription.start_date >= start_date,
                Subscription.start_date <= end_date,
            )
        )
        .group_by(func.substr(Subscription.start_date, 1, 7))
    )
    new_by_month = {r[0]: int(r[1]) for r in db.execute(new_stmt).fetchall()}

    # 2. Renewed subscriptions by month
    ren_stmt = (
        select(
            func.substr(Subscription.start_date, 1, 7).label("month"),
            func.count(Subscription.id).label("count")
        )
        .where(
            and_(
                Subscription.start_date >= start_date,
                Subscription.start_date <= end_date,
                Subscription.number.like("%-REN%"),
            )
        )
        .group_by(func.substr(Subscription.start_date, 1, 7))
    )
    ren_by_month = {r[0]: int(r[1]) for r in db.execute(ren_stmt).fetchall()}

    # 3. Closed subscriptions by month
    closed_stmt = (
        select(
            func.substr(Subscription.expiry_date, 1, 7).label("month"),
            func.count(Subscription.id).label("count")
        )
        .where(
            and_(
                Subscription.status == "CLOSED",
                Subscription.expiry_date >= start_date,
                Subscription.expiry_date <= end_date,
            )
        )
        .group_by(func.substr(Subscription.expiry_date, 1, 7))
    )
    closed_by_month = {r[0]: int(r[1]) for r in db.execute(closed_stmt).fetchall()}

    all_months = sorted(set(list(new_by_month.keys()) + list(closed_by_month.keys())))
    if not all_months:
        return []

    data = []
    for m in all_months:
        new_cnt = new_by_month.get(m, 0)
        ren_cnt = ren_by_month.get(m, 0)
        cls_cnt = closed_by_month.get(m, 0)
        net = new_cnt - cls_cnt

        data.append({
            "period": m,
            "new": new_cnt,
            "renewed": ren_cnt,
            "closed": cls_cnt,
            "net_growth": net,
            "drilldown": {
                "label": f"View Movements for {m}",
                "url": f"/p3/finance/subscriptions?period={m}",
                "filters": {"period": m}
            }
        })
    return data


@cached("chart_cohorts", ttl=300)
def get_cohort_retention(
    db: Session,
    lookback_months: int = 6,
) -> Dict[str, Any]:
    """
    Computes triangular cohort retention heatmap.
    Groups customers by month of first subscription start and tracks active percentage
    over subsequent months (Month 0, Month 1, Month 2, etc.).
    """
    today = date.today()
    cohort_data = []

    # Find earliest subscription per customer
    first_sub_stmt = (
        select(
            Subscription.customer_id,
            func.min(Subscription.start_date).label("first_date")
        )
        .group_by(Subscription.customer_id)
    )
    first_subs = db.execute(first_sub_stmt).fetchall()

    # Group by cohort month
    cohort_customers: Dict[str, List[str]] = {}
    for cid, fdate in first_subs:
        if fdate:
            c_month = fdate.strftime("%Y-%m")
            if c_month not in cohort_customers:
                cohort_customers[c_month] = []
            cohort_customers[c_month].append(cid)

    # Build cohort retention for past N months
    sorted_cohorts = sorted(cohort_customers.keys())[-lookback_months:]

    for c_month in sorted_cohorts:
        c_users = cohort_customers[c_month]
        initial_count = len(c_users)
        if initial_count == 0:
            continue

        retention_rates = []
        cy, cm = map(int, c_month.split("-"))

        # For Month 0 to Month 5
        for offset in range(6):
            target_year = cy + (cm - 1 + offset) // 12
            target_month = ((cm - 1 + offset) % 12) + 1
            as_of_date = date(target_year, target_month, 1)

            if as_of_date > today:
                retention_rates.append(None)
                continue

            # Count how many of c_users were still active
            stmt_active = (
                select(func.count(distinct(Subscription.customer_id)))
                .where(
                    and_(
                        Subscription.customer_id.in_(c_users),
                        Subscription.status == "ACTIVE",
                        Subscription.start_date <= as_of_date,
                        (Subscription.expiry_date.is_(None) | (Subscription.expiry_date >= as_of_date)),
                    )
                )
            )
            active_cnt = db.execute(stmt_active).scalar_one_or_none() or 0
            rate = round((active_cnt / initial_count) * 100, 1)
            retention_rates.append(rate)

        cohort_data.append({
            "cohort": c_month,
            "cohort_size": initial_count,
            "retention": retention_rates,
            "drilldown": {
                "label": f"Cohort {c_month} Customers",
                "url": f"/p3/finance/customers?cohort={c_month}",
                "filters": {"cohort": c_month}
            }
        })

    return {
        "intervals": ["Month 0", "Month 1", "Month 2", "Month 3", "Month 4", "Month 5"],
        "cohorts": cohort_data
    }
