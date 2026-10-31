from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import Base, engine, SessionLocal
from backend.app.billing.models import BillingPeriod, BillingRun, BillingRunItem
from backend.app.invoices.models import Invoice, InvoiceLine
from backend.app.payments.models import Payment, PaymentAllocation

from sqlalchemy import text
from alembic.migration import MigrationContext
from alembic.operations import Operations
import backend.migrations.versions_p2.p2_0002_analytics_views as views_mig

def test_unique_billing_period_constraint():
    db = SessionLocal()
    p1 = BillingPeriod(
        subscription_id="sub-123",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        status="BILLED"
    )
    db.add(p1)
    db.commit()

    # Attempt inserting identical subscription and period must raise IntegrityError
    p2 = BillingPeriod(
        subscription_id="sub-123",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        status="BILLED"
    )
    db.add(p2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()

def test_invoice_creation_and_derived_is_overdue():
    db = SessionLocal()
    # Case A: Invoice confirmed, balance > 0, due date in the past -> is_overdue == True
    past_due = Invoice(
        number="INV-2026-000001",
        customer_id="cust-1",
        status="CONFIRMED",
        invoice_date=date.today() - timedelta(days=20),
        due_date=date.today() - timedelta(days=5),
        subtotal=Decimal("1000.00"),
        total=Decimal("1180.00"),
        amount_paid=Decimal("0.00"),
        balance=Decimal("1180.00"),
        snapshot={"customer_name": "Acme"}
    )
    db.add(past_due)
    db.commit()
    assert past_due.is_overdue is True

    # Case B: Once fully paid, is_overdue is False
    past_due.amount_paid = Decimal("1180.00")
    past_due.balance = Decimal("0.00")
    past_due.status = "PAID"
    db.commit()
    assert past_due.is_overdue is False
    db.close()

def test_payment_and_allocation_integrity():
    db = SessionLocal()
    pay = Payment(
        customer_id="cust-1",
        method="UPI",
        amount=Decimal("1000.00"),
        unallocated_amount=Decimal("200.00")
    )
    db.add(pay)
    db.commit()

    alloc = PaymentAllocation(
        payment_id=pay.id,
        invoice_id="inv-123",
        amount=Decimal("800.00")
    )
    db.add(alloc)
    db.commit()

    db.refresh(pay)
    assert len(pay.allocations) == 1
    assert pay.allocations[0].amount == Decimal("800.00")
    db.close()

def test_analytics_views_compilation_and_querying():
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            views_mig.upgrade()

    db = SessionLocal()
    # Test all 3 Person 3 views
    c_inv = db.execute(text("SELECT COUNT(*) FROM v_invoice_summary")).scalar()
    c_pay = db.execute(text("SELECT COUNT(*) FROM v_payment_summary")).scalar()
    c_out = db.execute(text("SELECT COUNT(*) FROM v_outstanding")).scalar()

    assert c_inv >= 0
    assert c_pay >= 0
    assert c_out >= 0
    db.close()
