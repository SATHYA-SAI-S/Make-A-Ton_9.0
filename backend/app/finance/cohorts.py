"""
Cohort Retention Analysis Service (P3-T10).
Groups customers by acquisition month and tracks active/paused retention over time.
Provides cell drilldown into distinct customer records.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.orm import Session

from backend.app.analytics.cache import cached
from backend.app.finance.models import Customer, Plan, Subscription
from backend.app.finance.overview import compute_mrr_sql


def _add_months(start_date: date, months: int) -> date:
    """Adds months to a given date safely."""
    year = start_date.year + (start_date.month - 1 + months) // 12
    month = ((start_date.month - 1 + months) % 12) + 1
    return date(year, month, 1)


@cached("cohort_retention_matrix", ttl=300)
def get_cohort_retention_matrix(
    db: Session,
    lookback_months: int = 12,
    max_offsets: int = 6,
) -> Dict[str, Any]:
    """
    Computes triangular cohort retention matrix.
    Each row is an acquisition cohort (month of first subscription).
    Each column is an offset (Month 0, Month 1, Month 2, ...).
    Returns percentage holding an ACTIVE or PAUSED subscription.
    Future months return None (null).
    """
    today = date.today()

    # Step 1: Find first subscription start date for each customer
    first_sub_stmt = (
        select(
            Subscription.customer_id,
            func.min(Subscription.start_date).label("first_date")
        )
        .group_by(Subscription.customer_id)
    )
    customer_cohorts: Dict[str, str] = {}
    cohort_customers: Dict[str, List[str]] = {}

    for cid, fdate in db.execute(first_sub_stmt).fetchall():
        if fdate:
            c_key = fdate.strftime("%Y-%m")
            customer_cohorts[cid] = c_key
            if c_key not in cohort_customers:
                cohort_customers[c_key] = []
            cohort_customers[c_key].append(cid)

    # Sort cohorts chronologically and take the last N months
    all_cohort_keys = sorted(cohort_customers.keys())
    selected_cohorts = all_cohort_keys[-lookback_months:] if len(all_cohort_keys) > lookback_months else all_cohort_keys

    matrix = []
    intervals = [f"Month {i}" for i in range(max_offsets)]

    for c_key in selected_cohorts:
        c_users = cohort_customers[c_key]
        initial_count = len(c_users)
        if initial_count == 0:
            continue

        cy, cm = map(int, c_key.split("-"))
        cohort_start = date(cy, cm, 1)

        retention_row = []
        counts_row = []

        for offset in range(max_offsets):
            eval_date = _add_months(cohort_start, offset)
            # Future month check
            if eval_date > today:
                retention_row.append(None)
                counts_row.append(None)
                continue

            # In month 0, all cohort customers joined (100.0%)
            if offset == 0:
                retention_row.append(100.0)
                counts_row.append(initial_count)
                continue

            # Offset >= 1: Check how many held an active subscription as of eval_date
            # A subscription was active at eval_date if it started before/on eval_date
            # and had not yet expired (expiry_date >= eval_date or expiry_date is null).
            stmt = (
                select(func.count(distinct(Subscription.customer_id)))
                .where(
                    and_(
                        Subscription.customer_id.in_(c_users),
                        Subscription.start_date <= eval_date,
                        or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= eval_date),
                        or_(
                            Subscription.status.in_(["ACTIVE", "PAUSED"]),
                            Subscription.close_reason.in_(["EXPIRED", "EARLY_CLOSURE", "CANCELLED"]),
                        ),
                    )
                )
            )
            retained_count = db.execute(stmt).scalar_one_or_none() or 0
            rate = round((retained_count / initial_count) * 100, 1)
            retention_row.append(rate)
            counts_row.append(retained_count)

        matrix.append({
            "cohort": c_key,
            "cohort_size": initial_count,
            "retention": retention_row,
            "retained_counts": counts_row,
            "drilldown": {
                "label": f"Cohort {c_key} Customers",
                "url": f"/p3/finance/cohorts?cohort={c_key}",
                "filters": {"cohort": c_key}
            }
        })

    return {
        "intervals": intervals,
        "cohorts": matrix,
    }


def get_cohort_cell_customers(
    db: Session,
    cohort: str,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Returns the exact customer accounts belonging to a specific cohort and offset cell.
    Lists customer details, subscription status, and current MRR contribution.
    """
    today = date.today()
    cy, cm = map(int, cohort.split("-"))
    cohort_start = date(cy, cm, 1)
    eval_date = _add_months(cohort_start, offset)

    # 1. Identify cohort customers (customers whose first sub was in `cohort`)
    first_sub_stmt = (
        select(
            Subscription.customer_id,
            func.min(Subscription.start_date).label("first_date")
        )
        .group_by(Subscription.customer_id)
    )
    cohort_cids = []
    for cid, fdate in db.execute(first_sub_stmt).fetchall():
        if fdate and fdate.strftime("%Y-%m") == cohort:
            cohort_cids.append(cid)

    if not cohort_cids:
        return {"cohort": cohort, "offset": offset, "total": 0, "customers": []}

    # 2. If eval_date > today, future cell has no data
    if eval_date > today:
        return {"cohort": cohort, "offset": offset, "total": 0, "customers": [], "status": "FUTURE"}

    # 3. If offset == 0, all cohort customers
    if offset == 0:
        target_cids = cohort_cids
    else:
        # Customers with active or live subscriptions as of eval_date
        stmt = (
            select(Subscription.customer_id)
            .distinct()
            .where(
                and_(
                    Subscription.customer_id.in_(cohort_cids),
                    Subscription.start_date <= eval_date,
                    or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= eval_date),
                    or_(
                        Subscription.status.in_(["ACTIVE", "PAUSED"]),
                        Subscription.close_reason.in_(["EXPIRED", "EARLY_CLOSURE", "CANCELLED"]),
                    ),
                )
            )
        )
        target_cids = [r[0] for r in db.execute(stmt).fetchall()]

    customers_data = []
    for cid in target_cids:
        cust = db.query(Customer).filter(Customer.id == cid).first()
        if not cust:
            continue
        c_mrr = compute_mrr_sql(db, as_of=today, customer_id=cid)
        active_sub = (
            db.query(Subscription)
            .filter(Subscription.customer_id == cid, Subscription.status == "ACTIVE")
            .first()
        )
        customers_data.append({
            "customer_id": cid,
            "name": cust.name,
            "email": cust.email,
            "status": cust.status,
            "current_plan": active_sub.plan.name if active_sub and active_sub.plan else "N/A",
            "current_mrr": str(c_mrr),
        })

    return {
        "cohort": cohort,
        "offset": offset,
        "eval_date": eval_date.isoformat(),
        "total": len(customers_data),
        "customers": customers_data,
    }
