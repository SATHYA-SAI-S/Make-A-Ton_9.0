"""
Celery background tasks for Analytics & Performance layer (P3-T07).
Rebuilds revenue snapshots, refreshes materialized views, and processes events.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.finance.overview import (
    compute_cash_and_invoicing_sql,
    compute_mrr_sql,
    compute_outstanding_and_overdue_sql,
    compute_subscription_counts_sql,
)
from app.analytics.models import AnalyticsSnapshot, RevenueSnapshot
from app.analytics.cache import invalidate_cache

logger = logging.getLogger("subscriptiq.analytics.tasks")


def rebuild_revenue_snapshots(period: Optional[str] = None, months_back: int = 12) -> int:
    """
    Computes and saves RevenueSnapshots for historical periods.
    If period is specified (e.g. '2026-10'), rebuilds only that period.
    Otherwise, rebuilds up to `months_back` months from today.
    """
    db: Session = SessionLocal()
    count = 0
    try:
        today = date.today()
        periods = []
        if period:
            periods.append(period)
        else:
            # Generate past N months periods
            cur_year = today.year
            cur_month = today.month
            for i in range(months_back):
                p_str = f"{cur_year:04d}-{cur_month:02d}"
                periods.append(p_str)
                cur_month -= 1
                if cur_month < 1:
                    cur_month = 12
                    cur_year -= 1

        for p_str in periods:
            y, m = map(int, p_str.split("-"))
            start_date = date(y, m, 1)
            # Find last day of month
            if m == 12:
                next_month = date(y + 1, 1, 1)
            else:
                next_month = date(y, m + 1, 1)
            end_date = next_month - timedelta(days=1)

            # Compute aggregates via SQL
            mrr_val = compute_mrr_sql(db, as_of=end_date)
            arr_val = mrr_val * Decimal("12")
            subs_val, custs_val = compute_subscription_counts_sql(db, as_of=end_date)
            rev_val, inv_val = compute_cash_and_invoicing_sql(db, start=start_date, end=end_date)
            out_val, _, _ = compute_outstanding_and_overdue_sql(db, as_of=end_date)

            # Upsert into revenue_snapshots
            snapshot = db.query(RevenueSnapshot).filter(RevenueSnapshot.period == p_str).first()
            if not snapshot:
                snapshot = RevenueSnapshot(period=p_str)
                db.add(snapshot)

            snapshot.mrr = mrr_val
            snapshot.arr = arr_val
            snapshot.invoiced = inv_val
            snapshot.collected = rev_val
            snapshot.outstanding = out_val
            snapshot.active_subscriptions = subs_val
            snapshot.customers = custs_val
            snapshot.computed_at = datetime.now(timezone.utc)
            count += 1

        db.commit()
        logger.info(f"Successfully rebuilt {count} revenue snapshots.")
        # Invalidate overview cache after snapshot refresh
        invalidate_cache("finance_overview")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rebuild revenue snapshots: {e}")
        raise e
    finally:
        db.close()


def refresh_materialized_views() -> bool:
    """
    Refreshes database materialized views concurrently if on PostgreSQL,
    or verifies view exists on SQLite.
    """
    db: Session = SessionLocal()
    try:
        bind = db.get_bind()
        if bind.dialect.name == "postgresql":
            db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_revenue_monthly_summary"))
            db.commit()
            logger.info("Successfully refreshed PostgreSQL materialized view mv_revenue_monthly_summary.")
        else:
            # SQLite check
            db.execute(text("SELECT COUNT(*) FROM mv_revenue_monthly_summary")).scalar()
            logger.info("Verified SQLite view mv_revenue_monthly_summary.")
        return True
    except Exception as e:
        logger.warning(f"Materialized view refresh failed or not applicable: {e}")
        return False
    finally:
        db.close()


# Event listener that triggers snapshot and cache refresh
def on_financial_event_trigger(event) -> None:
    """Triggered on billing.run_completed or payment.recorded."""
    try:
        # Invalidate cache immediately
        invalidate_cache()
        # In production with background workers enabled, rebuild snapshot
        import os
        if os.environ.get("ENABLE_BACKGROUND_SNAPSHOT_TRIGGERS", "false").lower() == "true":
            today = date.today()
            current_period = f"{today.year:04d}-{today.month:02d}"
            rebuild_revenue_snapshots(period=current_period)
    except Exception as e:
        logger.error(f"Event trigger snapshot rebuild error: {e}")


# Hook up event listeners
try:
    from app.shared.events import subscribe
    subscribe("billing.run_completed", on_financial_event_trigger)
    subscribe("payment.recorded", on_financial_event_trigger)
except ImportError:
    pass
