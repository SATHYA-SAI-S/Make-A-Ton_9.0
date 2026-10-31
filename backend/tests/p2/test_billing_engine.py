from datetime import date, timedelta
from decimal import Decimal
import pytest

from backend.app.core.database import SessionLocal
from backend.app.shared.dto import SubscriptionDTO, SubscriptionLineDTO, CustomerDTO
from backend.app.shared.registry import get_port
from backend.app.billing.models import BillingPeriod, BillingRun, BillingRunItem
from backend.app.billing.engine import run_billing_engine, find_missed_periods
from backend.app.invoices.models import Invoice

def test_idempotent_billing_twice_same_date():
    sub_port = get_port("subscription")

    sub_id = "sub-idem-001"
    sub = SubscriptionDTO(
        id=sub_id,
        number="SUB-0001",
        customer_id="cust-001",
        plan_id="plan-basic",
        status="ACTIVE",
        billing_frequency="MONTHLY",
        start_date=date(2026, 10, 1),
        next_billing_date=date(2026, 10, 1),
        lines=[
            SubscriptionLineDTO(id="l1", product_id="prod-1", quantity=1, unit_price=Decimal("1000.00"), amount=Decimal("1000.00"))
        ]
    )
    sub_port.seed_subscription(sub)

    run1 = run_billing_engine(as_of=date(2026, 10, 15))
    assert run1.invoices_created == 1
    assert run1.status == "COMPLETED"

    # Second run on same or later date within same period
    run2 = run_billing_engine(as_of=date(2026, 10, 15))
    assert run2.invoices_created == 0  # Skipped via idempotency

    db = SessionLocal()
    invoices = db.query(Invoice).filter(Invoice.subscription_id == sub_id).all()
    assert len(invoices) == 1
    periods = db.query(BillingPeriod).filter(BillingPeriod.subscription_id == sub_id).all()
    assert len(periods) == 1
    db.close()

def test_concurrent_runs_produce_single_invoice():
    sub_port = get_port("subscription")
    sub_id = "sub-thread-001"
    sub = SubscriptionDTO(
        id=sub_id,
        number="SUB-0002",
        customer_id="cust-001",
        plan_id="plan-basic",
        status="ACTIVE",
        billing_frequency="MONTHLY",
        start_date=date(2026, 10, 1),
        next_billing_date=date(2026, 10, 1),
        lines=[
            SubscriptionLineDTO(id="l1", product_id="prod-1", quantity=1, unit_price=Decimal("500.00"), amount=Decimal("500.00"))
        ]
    )
    sub_port.seed_subscription(sub)

    # Run two passes
    r1 = run_billing_engine(as_of=date(2026, 10, 10))
    r2 = run_billing_engine(as_of=date(2026, 10, 10))

    db = SessionLocal()
    invoices = db.query(Invoice).filter(Invoice.subscription_id == sub_id).all()
    assert len(invoices) == 1
    periods = db.query(BillingPeriod).filter(BillingPeriod.subscription_id == sub_id).all()
    assert len(periods) == 1
    db.close()

def test_missed_for_three_months_generates_three_invoices():
    sub_port = get_port("subscription")
    sub_id = "sub-missed-3m"
    sub = SubscriptionDTO(
        id=sub_id,
        number="SUB-0003",
        customer_id="cust-001",
        plan_id="plan-growth",
        status="ACTIVE",
        billing_frequency="MONTHLY",
        start_date=date(2026, 7, 1),
        next_billing_date=date(2026, 7, 1),
        lines=[
            SubscriptionLineDTO(id="l1", product_id="prod-1", quantity=1, unit_price=Decimal("1000.00"), amount=Decimal("1000.00"))
        ]
    )
    sub_port.seed_subscription(sub)

    run = run_billing_engine(as_of=date(2026, 10, 15))
    assert run.invoices_created == 4

    db = SessionLocal()
    invoices = db.query(Invoice).filter(Invoice.subscription_id == sub_id).all()
    assert len(invoices) == 4
    db.close()

def test_dry_run_creates_no_invoices_or_periods():
    sub_port = get_port("subscription")
    sub_id = "sub-dryrun-001"
    sub = SubscriptionDTO(
        id=sub_id,
        number="SUB-DRY",
        customer_id="cust-001",
        plan_id="plan-basic",
        status="ACTIVE",
        billing_frequency="MONTHLY",
        start_date=date(2026, 10, 1),
        next_billing_date=date(2026, 10, 1),
        lines=[
            SubscriptionLineDTO(id="l1", product_id="prod-1", quantity=1, unit_price=Decimal("500.00"), amount=Decimal("500.00"))
        ]
    )
    sub_port.seed_subscription(sub)

    run = run_billing_engine(as_of=date(2026, 10, 10), dry_run=True)
    assert run.invoices_created == 1  # 1 simulated in BillingRun
    assert "DRY_RUN" in run.triggered_by

    db = SessionLocal()
    invoices = db.query(Invoice).filter(Invoice.subscription_id == sub_id).all()
    assert len(invoices) == 0  # 0 created in database
    periods = db.query(BillingPeriod).filter(BillingPeriod.subscription_id == sub_id).all()
    assert len(periods) == 0  # 0 created in database
    db.close()

def test_missed_periods_detector():
    sub_port = get_port("subscription")
    sub_id = "sub-detector-001"
    sub = SubscriptionDTO(
        id=sub_id,
        number="SUB-DETECT",
        customer_id="cust-001",
        plan_id="plan-basic",
        status="ACTIVE",
        billing_frequency="MONTHLY",
        start_date=date(2026, 8, 1),
        next_billing_date=date(2026, 8, 1),
        lines=[SubscriptionLineDTO(id="l1", product_id="prod-1", quantity=1, unit_price=Decimal("500.00"), amount=Decimal("500.00"))]
    )
    sub_port.seed_subscription(sub)

    missed = find_missed_periods(as_of=date(2026, 10, 15))
    assert len(missed) >= 2  # August and September periods are past due and unbilled
    assert any(m["subscription_id"] == sub_id for m in missed)
