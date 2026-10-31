from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine, SessionLocal
from backend.app.invoices.models import Invoice, InvoiceLine
from backend.app.invoices.service import (
    generate_invoice_number,
    confirm_invoice,
    cancel_invoice,
    generate_invoice_pdf
)
from backend.app.main import app

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_sequential_invoice_numbering():
    db = SessionLocal()
    num1 = generate_invoice_number(db)
    curr_year = date.today().year
    assert num1 == f"INV-{curr_year}-000001"

    inv1 = Invoice(
        number=num1,
        customer_id="c1",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        subtotal=Decimal("1000.00"),
        total=Decimal("1180.00"),
        balance=Decimal("1180.00")
    )
    db.add(inv1)
    db.commit()

    num2 = generate_invoice_number(db)
    assert num2 == f"INV-{curr_year}-000002"
    db.close()

def test_invoice_lifecycle_and_cancellation():
    db = SessionLocal()
    inv = Invoice(
        number="INV-2026-000010",
        customer_id="cust-1",
        status="DRAFT",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        subtotal=Decimal("500.00"),
        total=Decimal("500.00"),
        balance=Decimal("500.00")
    )
    db.add(inv)
    db.commit()

    # Confirm
    confirmed = confirm_invoice(inv.id, db)
    assert confirmed.status == "CONFIRMED"

    # Cancel
    cancelled = cancel_invoice(inv.id, reason="Customer requested termination", db=db)
    assert cancelled.status == "CANCELLED"
    assert cancelled.cancellation_reason == "Customer requested termination"
    db.close()

def test_cannot_cancel_partially_paid_invoice():
    db = SessionLocal()
    inv = Invoice(
        number="INV-2026-000020",
        customer_id="cust-1",
        status="CONFIRMED",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        subtotal=Decimal("1000.00"),
        total=Decimal("1000.00"),
        amount_paid=Decimal("400.00"),
        balance=Decimal("600.00")
    )
    db.add(inv)
    db.commit()

    from backend.app.core.errors import AppException
    with pytest.raises(AppException) as exc:
        cancel_invoice(inv.id, reason="Refund request", db=db)
    assert exc.value.code == "CANNOT_CANCEL"
    db.close()

def test_pdf_generation_returns_valid_pdf_bytes():
    db = SessionLocal()
    inv = Invoice(
        number="INV-2026-000030",
        customer_id="cust-1",
        status="CONFIRMED",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        subtotal=Decimal("2000.00"),
        discount_total=Decimal("200.00"),
        tax_total=Decimal("324.00"),
        total=Decimal("2124.00"),
        amount_paid=Decimal("0.00"),
        balance=Decimal("2124.00"),
        snapshot={
            "customer": {"name": "Test Acme", "email": "test@acme.com", "state_code": "KA"},
            "company": {"name": "Brightloop Software", "state_code": "KA", "gstin": "29AABCU9603R1Z7"},
            "plan_name": "Enterprise Cloud ERP"
        }
    )
    line = InvoiceLine(
        invoice=inv,
        product_id="prod-erp",
        description="Enterprise Cloud ERP Subscription",
        quantity=Decimal("1"),
        unit_price=Decimal("2000.00"),
        discount_amount=Decimal("200.00"),
        tax_rate=Decimal("18.00"),
        tax_amount=Decimal("324.00"),
        line_total=Decimal("2124.00")
    )
    db.add(inv)
    db.commit()

    pdf_bytes = generate_invoice_pdf(inv)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500
    db.close()

def test_customer_isolation_and_api():
    db = SessionLocal()
    inv1 = Invoice(
        number="INV-2026-000040",
        customer_id="cust-alice",
        status="CONFIRMED",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        subtotal=Decimal("100.00"),
        total=Decimal("100.00"),
        balance=Decimal("100.00")
    )
    db.add(inv1)
    db.commit()
    inv1_id = inv1.id
    db.close()

    client = TestClient(app)
    # Alice accesses own invoice -> 200
    res_alice = client.get(
        f"/api/v1/invoices/{inv1_id}",
        headers={"x-user-role": "customer", "x-customer-id": "cust-alice"}
    )
    assert res_alice.status_code == 200

    # Bob accesses Alice's invoice -> 403 Forbidden
    res_bob = client.get(
        f"/api/v1/invoices/{inv1_id}",
        headers={"x-user-role": "customer", "x-customer-id": "cust-bob"}
    )
    assert res_bob.status_code == 403

    # PDF download
    res_pdf = client.get(
        f"/api/v1/invoices/{inv1_id}/pdf",
        headers={"x-user-role": "customer", "x-customer-id": "cust-alice"}
    )
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF")
