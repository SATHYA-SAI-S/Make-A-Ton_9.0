"""
Finance Overview & KPI Service.
Implements pure SQL-aggregated metric calculations according to docs/p3/metrics.md.
No python row-loops; all heavy aggregates are computed directly in SQL with GROUP BY and FILTER.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import (
    and_,
    case,
    distinct,
    func,
    or_,
    select
)
from sqlalchemy.orm import Session

from backend.app.analytics.metrics import (
    TWO_PLACES,
    calculate_arpc,
    calculate_arr,
    calculate_churn_rate,
    calculate_collection_rate,
    calculate_pct_change,
    normalize_mrr,
)
from backend.app.analytics.cache import cached
from backend.app.core.money import to_money
from backend.app.finance.models import (
    Customer,
    Invoice,
    Payment,
    Plan,
    Refund,
    Subscription,
    SubscriptionLine,
)


def _get_period_bounds(start_date: Optional[date], end_date: Optional[date]) -> Tuple[date, date, date, date]:
    """Calculates current period and equivalent previous period bounds."""
    today = date.today()
    if not end_date:
        end_date = today
    if not start_date:
        # Default to 30 days prior
        start_date = end_date - timedelta(days=29)

    period_len = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_len - 1)
    return start_date, end_date, prev_start, prev_end


def compute_mrr_sql(
    db: Session,
    as_of: date,
    plan_id: Optional[str] = None,
    frequency: Optional[str] = None,
    customer_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Decimal:
    """
    Computes total normalized MRR directly via SQL aggregation.
    Formula: Line quantity * unit_price (or plan.price), normalized by frequency.
    Only ACTIVE subscriptions count toward MRR (PAUSED excluded).
    """
    # Subquery for sum of lines per subscription
    lines_subq = (
        select(
            SubscriptionLine.subscription_id.label("sub_id"),
            func.coalesce(func.sum(SubscriptionLine.quantity * SubscriptionLine.unit_price), 0).label("lines_sum")
        )
        .group_by(SubscriptionLine.subscription_id)
        .subquery()
    )

    # Base price: line sum if > 0, else plan.price
    sub_price = case(
        (lines_subq.c.lines_sum > 0, lines_subq.c.lines_sum),
        else_=Plan.price
    )

    # Normalization formula
    norm_mrr_expr = case(
        (func.upper(Plan.billing_frequency) == "DAILY", sub_price * Decimal("365") / Decimal("12")),
        (func.upper(Plan.billing_frequency) == "WEEKLY", sub_price * Decimal("52") / Decimal("12")),
        (func.upper(Plan.billing_frequency) == "YEARLY", sub_price / Decimal("12")),
        else_=sub_price
    )

    # Subscriptions must be ACTIVE as of the date
    target_status = status_filter or "ACTIVE"
    conditions = [
        Subscription.status == target_status,
        Subscription.start_date <= as_of,
        or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= as_of),
    ]

    if plan_id:
        conditions.append(Subscription.plan_id == plan_id)
    if customer_id:
        conditions.append(Subscription.customer_id == customer_id)
    if frequency:
        conditions.append(func.upper(Plan.billing_frequency) == frequency.upper())

    stmt = (
        select(func.coalesce(func.sum(norm_mrr_expr), 0))
        .select_from(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .outerjoin(lines_subq, Subscription.id == lines_subq.c.sub_id)
        .where(and_(*conditions))
    )

    result = db.execute(stmt).scalar_one_or_none()
    return to_money(result or 0)


def compute_subscription_counts_sql(
    db: Session,
    as_of: date,
    plan_id: Optional[str] = None,
    frequency: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> Tuple[int, int]:
    """
    Returns (active_subscriptions, active_customers) as of a given date via SQL.
    """
    conditions = [
        Subscription.status == "ACTIVE",
        Subscription.start_date <= as_of,
        or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= as_of),
    ]
    if plan_id:
        conditions.append(Subscription.plan_id == plan_id)
    if customer_id:
        conditions.append(Subscription.customer_id == customer_id)
    if frequency:
        conditions.append(func.upper(Plan.billing_frequency) == frequency.upper())

    stmt = (
        select(
            func.count(distinct(Subscription.id)),
            func.count(distinct(Subscription.customer_id))
        )
        .select_from(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(and_(*conditions))
    )
    row = db.execute(stmt).first()
    active_subs = row[0] if row else 0
    active_custs = row[1] if row else 0
    return active_subs, active_custs


def compute_cash_and_invoicing_sql(
    db: Session,
    start: date,
    end: date,
    customer_id: Optional[str] = None,
) -> Tuple[Decimal, Decimal]:
    """
    Returns (revenue_received, total_invoiced) in period via SQL.
    Revenue received = Payments (RECORDED) - Refunds in period.
    Total invoiced = Invoices (status != 'CANCELLED') in period.
    """
    # 1. Payments in period
    p_conds = [
        Payment.status == "RECORDED",
        Payment.payment_date >= start,
        Payment.payment_date <= end,
    ]
    if customer_id:
        p_conds.append(Payment.customer_id == customer_id)

    stmt_payments = select(func.coalesce(func.sum(Payment.amount), 0)).where(and_(*p_conds))
    payments_sum = to_money(db.execute(stmt_payments).scalar_one_or_none() or 0)

    # 2. Refunds in period
    r_conds = [
        Refund.status == "PROCESSED",
        Refund.refund_date >= start,
        Refund.refund_date <= end,
    ]
    if customer_id:
        r_conds.append(Refund.customer_id == customer_id)

    stmt_refunds = select(func.coalesce(func.sum(Refund.amount), 0)).where(and_(*r_conds))
    refunds_sum = to_money(db.execute(stmt_refunds).scalar_one_or_none() or 0)

    net_revenue = to_money(payments_sum - refunds_sum)

    # 3. Total Invoiced in period
    inv_conds = [
        Invoice.status != "CANCELLED",
        Invoice.invoice_date >= start,
        Invoice.invoice_date <= end,
    ]
    if customer_id:
        inv_conds.append(Invoice.customer_id == customer_id)

    stmt_invoiced = select(func.coalesce(func.sum(Invoice.total), 0)).where(and_(*inv_conds))
    invoiced_sum = to_money(db.execute(stmt_invoiced).scalar_one_or_none() or 0)

    return net_revenue, invoiced_sum


def compute_outstanding_and_overdue_sql(
    db: Session,
    as_of: date,
    customer_id: Optional[str] = None,
) -> Tuple[Decimal, Decimal, int]:
    """
    Returns (outstanding_balance, overdue_amount, overdue_count) as of a date via SQL.
    """
    conds = [
        Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
        Invoice.balance > 0,
        Invoice.invoice_date <= as_of,
    ]
    if customer_id:
        conds.append(Invoice.customer_id == customer_id)

    stmt = select(
        func.coalesce(func.sum(Invoice.balance), 0).label("outstanding"),
        func.coalesce(
            func.sum(
                case((Invoice.due_date < as_of, Invoice.balance), else_=0)
            ),
            0
        ).label("overdue"),
        func.count(
            case((Invoice.due_date < as_of, Invoice.id), else_=None)
        ).label("overdue_count")
    ).where(and_(*conds))

    row = db.execute(stmt).first()
    outstanding = to_money(row[0] if row else 0)
    overdue = to_money(row[1] if row else 0)
    overdue_count = int(row[2]) if row and row[2] else 0

    return outstanding, overdue, overdue_count


def compute_collection_rate_sql(
    db: Session,
    start: date,
    end: date,
    customer_id: Optional[str] = None,
) -> Decimal:
    """
    Computes Collection Rate % = (Collected towards invoices due in period / Amount due in period) * 100.
    """
    conds = [
        Invoice.status != "CANCELLED",
        Invoice.due_date >= start,
        Invoice.due_date <= end,
    ]
    if customer_id:
        conds.append(Invoice.customer_id == customer_id)

    stmt = select(
        func.coalesce(func.sum(Invoice.total), 0).label("due_total"),
        func.coalesce(func.sum(Invoice.amount_paid), 0).label("collected_total")
    ).where(and_(*conds))

    row = db.execute(stmt).first()
    due_total = to_money(row[0] if row else 0)
    collected_total = to_money(row[1] if row else 0)

    return calculate_collection_rate(collected_total, due_total)


def compute_churn_rate_sql(
    db: Session,
    start: date,
    end: date,
    customer_id: Optional[str] = None,
) -> Decimal:
    """
    Computes Customer Churn Rate % = (Lost customers in period / Active customers at start) * 100.
    Lost = Customer whose last active subscription closed with reason in (EXPIRED, EARLY_CLOSURE, CANCELLED)
           and has 0 active subscriptions at end date.
    """
    # Active customers at start date
    start_conds = [
        Subscription.status == "ACTIVE",
        Subscription.start_date <= start,
        or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= start),
    ]
    if customer_id:
        start_conds.append(Subscription.customer_id == customer_id)

    stmt_start = select(func.count(distinct(Subscription.customer_id))).where(and_(*start_conds))
    starting_customers = db.execute(stmt_start).scalar_one_or_none() or 0

    if starting_customers == 0:
        return Decimal("0.00")

    # Customers with closed subscriptions in period
    closed_conds = [
        Subscription.status == "CLOSED",
        Subscription.close_reason.in_(["EXPIRED", "EARLY_CLOSURE", "CANCELLED"]),
        Subscription.expiry_date >= start,
        Subscription.expiry_date <= end,
    ]
    if customer_id:
        closed_conds.append(Subscription.customer_id == customer_id)

    stmt_closed = select(Subscription.customer_id).distinct().where(and_(*closed_conds))
    closed_customer_ids = [r[0] for r in db.execute(stmt_closed).fetchall()]

    if not closed_customer_ids:
        return Decimal("0.00")

    # Filter to those who have ZERO active subscriptions remaining at end date
    active_now_stmt = (
        select(Subscription.customer_id)
        .distinct()
        .where(
            and_(
                Subscription.customer_id.in_(closed_customer_ids),
                Subscription.status == "ACTIVE",
                Subscription.start_date <= end,
                or_(Subscription.expiry_date.is_(None), Subscription.expiry_date >= end),
            )
        )
    )
    still_active_ids = set(r[0] for r in db.execute(active_now_stmt).fetchall())
    lost_customers_count = len([cid for cid in closed_customer_ids if cid not in still_active_ids])

    return calculate_churn_rate(lost_customers_count, starting_customers)


def compute_subscription_movements_sql(
    db: Session,
    start: date,
    end: date,
    customer_id: Optional[str] = None,
) -> Tuple[int, int, int]:
    """
    Returns (new_subscriptions, renewals, closed_subscriptions) in period via SQL.
    """
    # New subscriptions started in period
    new_conds = [
        Subscription.start_date >= start,
        Subscription.start_date <= end,
    ]
    if customer_id:
        new_conds.append(Subscription.customer_id == customer_id)

    stmt_new = select(func.count(Subscription.id)).where(and_(*new_conds))
    new_count = db.execute(stmt_new).scalar_one_or_none() or 0

    # Renewals in period (close_reason is null and start_date > created_at date or status is ACTIVE with past created_at)
    # or explicit renewals
    stmt_renewals = select(func.count(Subscription.id)).where(
        and_(
            Subscription.start_date >= start,
            Subscription.start_date <= end,
            Subscription.number.like("%-REN%"),
            *([Subscription.customer_id == customer_id] if customer_id else [])
        )
    )
    renewals_count = db.execute(stmt_renewals).scalar_one_or_none() or 0

    # Closed subscriptions in period
    closed_conds = [
        Subscription.status == "CLOSED",
        Subscription.expiry_date >= start,
        Subscription.expiry_date <= end,
    ]
    if customer_id:
        closed_conds.append(Subscription.customer_id == customer_id)

    stmt_closed = select(func.count(Subscription.id)).where(and_(*closed_conds))
    closed_count = db.execute(stmt_closed).scalar_one_or_none() or 0

    return new_count, renewals_count, closed_count


@cached("finance_overview", ttl=300)
def get_finance_overview_data(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    plan_id: Optional[str] = None,
    frequency: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes complete Finance Overview response with current period,
    previous period, and percentage changes.
    Matches schema in docs/p3/api.md section 4.
    """
    cur_start, cur_end, prev_start, prev_end = _get_period_bounds(start_date, end_date)

    # Current period metrics
    mrr_cur = compute_mrr_sql(db, cur_end, plan_id, frequency, customer_id, status)
    arr_cur = calculate_arr(mrr_cur)
    subs_cur, custs_cur = compute_subscription_counts_sql(db, cur_end, plan_id, frequency, customer_id)
    arpc_cur = calculate_arpc(mrr_cur, custs_cur)
    rev_cur, inv_cur = compute_cash_and_invoicing_sql(db, cur_start, cur_end, customer_id)
    out_cur, over_amt_cur, over_cnt_cur = compute_outstanding_and_overdue_sql(db, cur_end, customer_id)
    coll_cur = compute_collection_rate_sql(db, cur_start, cur_end, customer_id)
    churn_cur = compute_churn_rate_sql(db, cur_start, cur_end, customer_id)
    new_cur, ren_cur, closed_cur = compute_subscription_movements_sql(db, cur_start, cur_end, customer_id)

    # Previous period metrics
    mrr_prev = compute_mrr_sql(db, prev_end, plan_id, frequency, customer_id, status)
    arr_prev = calculate_arr(mrr_prev)
    subs_prev, custs_prev = compute_subscription_counts_sql(db, prev_end, plan_id, frequency, customer_id)
    arpc_prev = calculate_arpc(mrr_prev, custs_prev)
    rev_prev, inv_prev = compute_cash_and_invoicing_sql(db, prev_start, prev_end, customer_id)
    out_prev, over_amt_prev, over_cnt_prev = compute_outstanding_and_overdue_sql(db, prev_end, customer_id)
    coll_prev = compute_collection_rate_sql(db, prev_start, prev_end, customer_id)
    churn_prev = compute_churn_rate_sql(db, prev_start, prev_end, customer_id)
    new_prev, ren_prev, closed_prev = compute_subscription_movements_sql(db, prev_start, prev_end, customer_id)

    return {
        "kpis": {
            "mrr": {
                "value": str(mrr_cur),
                "previous": str(mrr_prev),
                "change_pct": float(calculate_pct_change(mrr_cur, mrr_prev)),
            },
            "arr": {
                "value": str(arr_cur),
                "previous": str(arr_prev),
                "change_pct": float(calculate_pct_change(arr_cur, arr_prev)),
            },
            "active_subscriptions": {
                "value": subs_cur,
                "previous": subs_prev,
                "change_pct": float(calculate_pct_change(subs_cur, subs_prev)),
            },
            "active_customers": {
                "value": custs_cur,
                "previous": custs_prev,
                "change_pct": float(calculate_pct_change(custs_cur, custs_prev)),
            },
            "arpc": {
                "value": str(arpc_cur),
                "previous": str(arpc_prev),
                "change_pct": float(calculate_pct_change(arpc_cur, arpc_prev)),
            },
            "revenue_received": {
                "value": str(rev_cur),
                "previous": str(rev_prev),
                "change_pct": float(calculate_pct_change(rev_cur, rev_prev)),
            },
            "total_invoiced": {
                "value": str(inv_cur),
                "previous": str(inv_prev),
                "change_pct": float(calculate_pct_change(inv_cur, inv_prev)),
            },
            "outstanding_balance": {
                "value": str(out_cur),
                "previous": str(out_prev),
                "change_pct": float(calculate_pct_change(out_cur, out_prev)),
            },
            "overdue_amount": {
                "value": str(over_amt_cur),
                "previous": str(over_amt_prev),
                "change_pct": float(calculate_pct_change(over_amt_cur, over_amt_prev)),
            },
            "overdue_count": {
                "value": over_cnt_cur,
                "previous": over_cnt_prev,
                "change_pct": float(calculate_pct_change(over_cnt_cur, over_cnt_prev)),
            },
            "collection_rate_pct": {
                "value": float(coll_cur),
                "previous": float(coll_prev),
                "change_pct": float(coll_cur - coll_prev),
            },
            "customer_churn_rate_pct": {
                "value": float(churn_cur),
                "previous": float(churn_prev),
                "change_pct": float(churn_cur - churn_prev),
            },
            "new_subscriptions": {
                "value": new_cur,
                "previous": new_prev,
                "change_pct": float(calculate_pct_change(new_cur, new_prev)),
            },
            "renewals_count": {
                "value": ren_cur,
                "previous": ren_prev,
                "change_pct": float(calculate_pct_change(ren_cur, ren_prev)),
            },
            "churn_subscriptions": {
                "value": closed_cur,
                "previous": closed_prev,
                "change_pct": float(calculate_pct_change(closed_cur, closed_prev)),
            },
        },
        "period": {
            "start": cur_start.isoformat(),
            "end": cur_end.isoformat(),
            "previous_start": prev_start.isoformat(),
            "previous_end": prev_end.isoformat(),
        },
    }
