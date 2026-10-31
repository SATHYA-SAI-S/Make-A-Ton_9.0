"""
Unit & Integration Tests for Performance Layer (P3-T07).
Validates caching, event invalidation, query count avoidance, and snapshot tasks.
"""
from datetime import date, datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.analytics.beat_schedule import BEAT
from backend.app.analytics.cache import (
    cached,
    get_cached_value,
    invalidate_cache,
    set_cached_value,
)
from backend.app.analytics.models import AnalyticsSnapshot, RevenueSnapshot
from backend.app.analytics.tasks import (
    rebuild_revenue_snapshots,
    refresh_materialized_views,
)
from backend.app.core.database import Base, get_db
from backend.app.finance.models import Customer, Invoice, Payment, Plan, Subscription
from backend.app.finance.overview import get_finance_overview_data
from backend.app.shared.events import publish


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    # Create the view for testing
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE VIEW IF NOT EXISTS mv_revenue_monthly_summary AS
                SELECT 
                    SUBSTR(invoice_date, 1, 7) AS month_key,
                    COUNT(id) AS total_invoices,
                    COALESCE(SUM(total), 0) AS total_invoiced,
                    COALESCE(SUM(amount_paid), 0) AS total_collected,
                    COALESCE(SUM(balance), 0) AS total_outstanding
                FROM invoices
                WHERE status != 'CANCELLED'
                GROUP BY SUBSTR(invoice_date, 1, 7)
                """
            )
        )
        conn.commit()

    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed initial test record
    cust = Customer(id="c-perf-1", name="Perf Corp", email="perf@example.com")
    plan = Plan(id="p-perf-1", name="Perf Plan", price=Decimal("1500.00"), billing_frequency="MONTHLY")
    sub = Subscription(
        id="s-perf-1", number="SUB-PERF-1", customer_id="c-perf-1", plan_id="p-perf-1",
        status="ACTIVE", start_date=date(2026, 1, 1)
    )
    inv = Invoice(
        id="i-perf-1", number="INV-PERF-1", customer_id="c-perf-1", subscription_id="s-perf-1",
        status="CONFIRMED", invoice_date=date(2026, 10, 5), due_date=date(2026, 10, 20),
        total=Decimal("1500.00"), amount_paid=Decimal("500.00"), balance=Decimal("1000.00")
    )
    pay = Payment(
        id="pay-perf-1", customer_id="c-perf-1", method="UPI",
        amount=Decimal("500.00"), payment_date=date(2026, 10, 5), status="RECORDED"
    )
    db.add_all([cust, plan, sub, inv, pay])
    db.commit()

    yield db, engine
    db.close()


def test_cache_hit_returns_identical_data(db_session):
    """Verifies that calling a cached function twice returns identical cached payload."""
    db, _ = db_session
    invalidate_cache()

    # Call 1: Miss and compute
    res1 = get_finance_overview_data(
        db=db,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31)
    )

    # Call 2: Hit from cache
    res2 = get_finance_overview_data(
        db=db,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31)
    )

    assert res1 == res2
    assert res2["kpis"]["mrr"]["value"] == "1500.00"
    assert res2["kpis"]["revenue_received"]["value"] == "500.00"


def test_cache_query_count_avoided_on_hit(db_session):
    """Asserts that on a cache hit, zero SQL SELECT statements are executed against DB."""
    db, engine = db_session
    invalidate_cache()

    query_count = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)

    try:
        # First execution (cold cache)
        query_count = 0
        get_finance_overview_data(
            db=db,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            plan_id="p-perf-1"
        )
        cold_query_count = query_count
        assert cold_query_count > 0, "Cold call should execute SQL queries"

        # Second execution (warm cache hit)
        query_count = 0
        get_finance_overview_data(
            db=db,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            plan_id="p-perf-1"
        )
        assert query_count == 0, f"Cache hit must execute 0 queries, but executed {query_count}"
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_cache_invalidation_after_payment_event(db_session):
    """Asserts that publishing a payment.recorded event invalidates finance caches."""
    db, _ = db_session
    invalidate_cache()

    # Populate cache
    res1 = get_finance_overview_data(
        db=db,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31)
    )
    assert res1["kpis"]["revenue_received"]["value"] == "500.00"

    # Simulate payment recorded event published by billing/payment module
    publish(
        event_name="payment.recorded",
        payload={"payment_id": "pay-new-001", "amount": "1000.00"},
        actor_id="system"
    )

    # Now add payment to DB
    new_pay = Payment(
        id="pay-new-001", customer_id="c-perf-1", method="UPI",
        amount=Decimal("1000.00"), payment_date=date(2026, 10, 12), status="RECORDED"
    )
    db.add(new_pay)
    db.commit()

    # Call again - cache was invalidated, so it computes fresh figures
    res2 = get_finance_overview_data(
        db=db,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31)
    )
    assert res2["kpis"]["revenue_received"]["value"] == "1500.00"


def test_rebuild_revenue_snapshots_task(db_session):
    """Asserts that rebuild_revenue_snapshots task accurately computes and stores snapshot records."""
    db, _ = db_session
    # Monkey-patch SessionLocal in tasks module to use our test db
    import backend.app.analytics.tasks as tasks_module
    orig_session_local = tasks_module.SessionLocal

    try:
        tasks_module.SessionLocal = lambda: db
        count = tasks_module.rebuild_revenue_snapshots(period="2026-10")
        assert count == 1

        snapshot = db.query(RevenueSnapshot).filter(RevenueSnapshot.period == "2026-10").first()
        assert snapshot is not None
        assert snapshot.period == "2026-10"
        assert snapshot.mrr == Decimal("1500.00")
        assert snapshot.arr == Decimal("18000.00")
        assert snapshot.invoiced == Decimal("1500.00")
        assert snapshot.active_subscriptions == 1
        assert snapshot.customers == 1
    finally:
        tasks_module.SessionLocal = orig_session_local


def test_refresh_materialized_views_task(db_session):
    """Verifies that refresh_materialized_views runs cleanly."""
    db, _ = db_session
    import backend.app.analytics.tasks as tasks_module
    orig_session_local = tasks_module.SessionLocal

    try:
        tasks_module.SessionLocal = lambda: db
        success = tasks_module.refresh_materialized_views()
        assert success is True
    finally:
        tasks_module.SessionLocal = orig_session_local


def test_beat_schedule_definitions():
    """Asserts that Celery beat schedule dict contains the expected cron tasks."""
    assert "rebuild-revenue-snapshots-nightly" in BEAT
    assert "refresh-materialized-views-hourly" in BEAT
    assert BEAT["rebuild-revenue-snapshots-nightly"]["schedule"] == 86400.0
    assert BEAT["refresh-materialized-views-hourly"]["schedule"] == 3600.0
