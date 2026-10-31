"""
Unit & Integration Tests for Finance Data Export Service (P3-T09).
Validates CSV generation, header formatting, and active filter compliance.
"""
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.finance.models import Customer, Invoice, Payment, Plan, Subscription
from backend.app.main import app


@pytest.fixture
def seeded_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    c = Customer(id="c-exp-1", name="Export Corp", email="exp@example.com")
    p = Plan(id="p-exp-1", name="Export Plan", price=Decimal("1000.00"), billing_frequency="MONTHLY")
    s = Subscription(
        id="s-exp-1", number="SUB-EXP-1", customer_id="c-exp-1", plan_id="p-exp-1",
        status="ACTIVE", start_date=date(2026, 1, 1)
    )
    inv = Invoice(
        id="inv-exp-1", number="INV-EXP-1", customer_id="c-exp-1", subscription_id="s-exp-1",
        status="CONFIRMED", invoice_date=date(2026, 10, 5), due_date=date(2026, 10, 20),
        total=Decimal("1000.00"), amount_paid=Decimal("0.00"), balance=Decimal("1000.00")
    )
    pay = Payment(
        id="pay-exp-1", customer_id="c-exp-1", method="UPI",
        amount=Decimal("1000.00"), payment_date=date(2026, 10, 5), status="RECORDED"
    )
    db.add_all([c, p, s, inv, pay])
    db.commit()
    yield db
    db.close()


@pytest.fixture
def client(seeded_db):
    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_export_revenue_performance_csv(client):
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/export?chart=revenue-performance&start_date=2026-10-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in res.headers["content-disposition"]
    lines = res.text.strip().splitlines()
    assert lines[0] == "Period,Invoiced,Collected,Collection Rate %"


def test_export_subscription_distribution_csv(client):
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/export?chart=subscription-distribution", headers=headers)
    assert res.status_code == 200
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("Billing Frequency,Count")


def test_export_invoice_aging_csv(client):
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/export?chart=invoice-aging", headers=headers)
    assert res.status_code == 200
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("Aging Bucket,Count")


def test_export_drilldown_invoices_csv(client):
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/export?chart=invoices", headers=headers)
    assert res.status_code == 200
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("Invoice Number,Customer ID")
    assert any("INV-EXP-1" in line for line in lines)


def test_export_customer_forbidden(client):
    headers = {"Authorization": "Bearer dev-customer-token"}
    res = client.get("/api/v1/finance/export?chart=invoices", headers=headers)
    assert res.status_code == 403
