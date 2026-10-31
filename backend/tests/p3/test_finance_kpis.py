"""
Unit & Integration Tests for Finance Metrics & KPI APIs (P3-T06).
Validates mathematical normalization, SQL aggregation, and API response accuracy.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.analytics.metrics import (
    calculate_arpc,
    calculate_arr,
    calculate_churn_rate,
    calculate_collection_rate,
    calculate_pct_change,
    normalize_mrr,
)
from backend.app.core.database import Base, get_db
from backend.app.finance.models import (
    Customer,
    Invoice,
    InvoiceLine,
    Payment,
    Plan,
    Refund,
    Subscription,
    SubscriptionLine,
)
from backend.app.main import app

# 1. Pure Unit Tests for Financial Metric Calculations
def test_mrr_normalization():
    assert normalize_mrr("100.00", "MONTHLY") == Decimal("100.00")
    assert normalize_mrr(Decimal("12000.00"), "YEARLY") == Decimal("1000.00")
    # Weekly: 120 * 52 / 12 = 520.00
    assert normalize_mrr("120.00", "WEEKLY") == Decimal("520.00")
    # Daily: 10 * 365 / 12 = 304.16666... -> 304.17
    assert normalize_mrr("10.00", "DAILY") == Decimal("304.17")


def test_arr_calculation():
    assert calculate_arr("1000.00") == Decimal("12000.00")
    assert calculate_arr(Decimal("1563.50")) == Decimal("18762.00")


def test_arpc_calculation():
    assert calculate_arpc("10000.00", 5) == Decimal("2000.00")
    assert calculate_arpc("10000.00", 0) == Decimal("0.00")


def test_churn_rate_calculation():
    # 2 lost out of 100 = 2.00%
    assert calculate_churn_rate(2, 100) == Decimal("2.00")
    # 0 starting = 0.00%
    assert calculate_churn_rate(5, 0) == Decimal("0.00")


def test_collection_rate_calculation():
    # 900 collected out of 1000 due = 90.00%
    assert calculate_collection_rate("900.00", "1000.00") == Decimal("90.00")
    # 0 due with 0 collected = 0.00%
    assert calculate_collection_rate("0.00", "0.00") == Decimal("0.00")
    # 100 collected with 0 due = 100.00%
    assert calculate_collection_rate("100.00", "0.00") == Decimal("100.00")


def test_pct_change_calculation():
    assert calculate_pct_change("110.00", "100.00") == Decimal("10.00")
    assert calculate_pct_change("80.00", "100.00") == Decimal("-20.00")
    assert calculate_pct_change("50.00", "0.00") == Decimal("100.00")


# 2. Database Integration & API Tests with Seeded Known Values
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed Customers
    c1 = Customer(id="cust-001", name="Acme Corp", email="acme@example.com")
    c2 = Customer(id="cust-002", name="Beta LLC", email="beta@example.com")
    c3 = Customer(id="cust-003", name="Gamma Inc", email="gamma@example.com")
    c4 = Customer(id="cust-004", name="Delta Co", email="delta@example.com")
    c5 = Customer(id="cust-005", name="Epsilon Ltd", email="epsilon@example.com")
    c6 = Customer(id="cust-006", name="Zeta Corp", email="zeta@example.com")
    db.add_all([c1, c2, c3, c4, c5, c6])

    # Seed Plans
    p_monthly = Plan(id="plan_monthly", name="Pro Monthly", price=Decimal("2000.00"), billing_frequency="MONTHLY")
    p_yearly = Plan(id="plan_yearly", name="Enterprise Annual", price=Decimal("120000.00"), billing_frequency="YEARLY")
    p_weekly = Plan(id="plan_weekly", name="Starter Weekly", price=Decimal("300.00"), billing_frequency="WEEKLY")
    p_daily = Plan(id="plan_daily", name="Micro Daily", price=Decimal("10.00"), billing_frequency="DAILY")
    db.add_all([p_monthly, p_yearly, p_weekly, p_daily])

    # Seed Subscriptions
    # 1. c1 - Monthly Active (MRR 2000.00)
    s1 = Subscription(
        id="sub-001", number="SUB-001", customer_id="cust-001", plan_id="plan_monthly",
        status="ACTIVE", start_date=date(2026, 1, 1), expiry_date=date(2027, 1, 1)
    )
    # 2. c2 - Yearly Active (MRR 120000 / 12 = 10000.00)
    s2 = Subscription(
        id="sub-002", number="SUB-002", customer_id="cust-002", plan_id="plan_yearly",
        status="ACTIVE", start_date=date(2026, 1, 1), expiry_date=date(2027, 1, 1)
    )
    # 3. c3 - Weekly Active (MRR 300 * 52 / 12 = 1300.00)
    s3 = Subscription(
        id="sub-003", number="SUB-003", customer_id="cust-003", plan_id="plan_weekly",
        status="ACTIVE", start_date=date(2026, 1, 1), expiry_date=date(2027, 1, 1)
    )
    # 4. c4 - Daily Active (MRR 10 * 365 / 12 = 304.17)
    s4 = Subscription(
        id="sub-004", number="SUB-004", customer_id="cust-004", plan_id="plan_daily",
        status="ACTIVE", start_date=date(2026, 1, 1), expiry_date=date(2027, 1, 1)
    )
    # 5. c5 - PAUSED (Excluded from MRR)
    s5 = Subscription(
        id="sub-005", number="SUB-005", customer_id="cust-005", plan_id="plan_monthly",
        status="PAUSED", start_date=date(2026, 1, 1)
    )
    # 6. c6 - CLOSED (Excluded from MRR)
    s6 = Subscription(
        id="sub-006", number="SUB-006", customer_id="cust-006", plan_id="plan_monthly",
        status="CLOSED", close_reason="CANCELLED", start_date=date(2026, 1, 1), expiry_date=date(2026, 10, 10)
    )
    db.add_all([s1, s2, s3, s4, s5, s6])

    # Seed Invoices (Period: 2026-10-01 to 2026-10-31)
    # Inv 1: c1, Total 2000, paid 2000, balance 0 (Paid)
    inv1 = Invoice(
        id="inv-001", number="INV-001", customer_id="cust-001", subscription_id="sub-001",
        status="CONFIRMED", invoice_date=date(2026, 10, 5), due_date=date(2026, 10, 15),
        total=Decimal("2000.00"), amount_paid=Decimal("2000.00"), balance=Decimal("0.00")
    )
    # Inv 2: c2, Total 10000, paid 4000, balance 6000 (Partially Paid & Overdue if checked after Oct 10)
    inv2 = Invoice(
        id="inv-002", number="INV-002", customer_id="cust-002", subscription_id="sub-002",
        status="PARTIALLY_PAID", invoice_date=date(2026, 10, 5), due_date=date(2026, 10, 10),
        total=Decimal("10000.00"), amount_paid=Decimal("4000.00"), balance=Decimal("6000.00")
    )
    # Inv 3: c3, Total 1300, paid 0, balance 1300 (Confirmed, due Oct 30)
    inv3 = Invoice(
        id="inv-003", number="INV-003", customer_id="cust-003", subscription_id="sub-003",
        status="CONFIRMED", invoice_date=date(2026, 10, 15), due_date=date(2026, 10, 30),
        total=Decimal("1300.00"), amount_paid=Decimal("0.00"), balance=Decimal("1300.00")
    )
    # Inv 4: c4, Cancelled (Excluded)
    inv4 = Invoice(
        id="inv-004", number="INV-004", customer_id="cust-004", subscription_id="sub-004",
        status="CANCELLED", invoice_date=date(2026, 10, 12), due_date=date(2026, 10, 20),
        total=Decimal("500.00"), amount_paid=Decimal("0.00"), balance=Decimal("500.00")
    )
    db.add_all([inv1, inv2, inv3, inv4])

    # Seed Payments
    p1 = Payment(
        id="pay-001", customer_id="cust-001", method="UPI",
        amount=Decimal("2000.00"), payment_date=date(2026, 10, 5), status="RECORDED"
    )
    p2 = Payment(
        id="pay-002", customer_id="cust-002", method="BANK_TRANSFER",
        amount=Decimal("4000.00"), payment_date=date(2026, 10, 8), status="RECORDED"
    )
    p3 = Payment(
        id="pay-003", customer_id="cust-003", method="CARD",
        amount=Decimal("500.00"), payment_date=date(2026, 10, 9), status="FAILED"  # Excluded!
    )
    db.add_all([p1, p2, p3])

    # Seed Refund
    ref1 = Refund(
        id="ref-001", payment_id="pay-001", customer_id="cust-001",
        amount=Decimal("500.00"), refund_date=date(2026, 10, 20), status="PROCESSED"
    )
    db.add(ref1)

    db.commit()
    yield db
    db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_finance_overview_kpis(client):
    """Asserts every single KPI to the exact rupee and percentage on seeded dataset."""
    headers = {"Authorization": "Bearer dev-admin-token"}
    response = client.get(
        "/api/v1/finance/overview?start_date=2026-10-01&end_date=2026-10-31",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    kpis = data["kpis"]

    # 1. MRR: 2000 + 10000 + 1300 + 304.17 = 13604.17
    assert kpis["mrr"]["value"] == "13604.17"

    # 2. ARR: 13604.17 * 12 = 163250.04
    assert kpis["arr"]["value"] == "163250.04"

    # 3. Active Subscriptions: 4 (s1, s2, s3, s4; s5 paused, s6 closed)
    assert kpis["active_subscriptions"]["value"] == 4

    # 4. Active Customers: 4 (c1, c2, c3, c4)
    assert kpis["active_customers"]["value"] == 4

    # 5. ARPC: 13604.17 / 4 = 3401.04
    assert kpis["arpc"]["value"] == "3401.04"

    # 6. Revenue Received: (2000 + 4000) - 500 = 5500.00
    assert kpis["revenue_received"]["value"] == "5500.00"

    # 7. Total Invoiced: 2000 + 10000 + 1300 = 13300.00 (inv4 cancelled)
    assert kpis["total_invoiced"]["value"] == "13300.00"

    # 8. Outstanding: inv2 (6000) + inv3 (1300) = 7300.00
    assert kpis["outstanding_balance"]["value"] == "7300.00"

    # 9. Overdue: As of 2026-10-31, inv2 (due 10-10) is overdue for 6000.00
    # Inv 3 is due 10-30, which is < 10-31 so it is also overdue!
    # Let's check overdue amount as of 10-31: 6000.00 + 1300.00 = 7300.00, count = 2
    assert Decimal(kpis["overdue_amount"]["value"]) == Decimal("7300.00")
    assert kpis["overdue_count"]["value"] == 2

    # 10. Collection Rate: 6000 collected / 13300 due = 45.11%
    assert kpis["collection_rate_pct"]["value"] == 45.11


def test_finance_overview_frequency_filter(client):
    """Filters overview by frequency=MONTHLY."""
    headers = {"Authorization": "Bearer dev-admin-token"}
    response = client.get(
        "/api/v1/finance/overview?start_date=2026-10-01&end_date=2026-10-31&frequency=MONTHLY",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Only Monthly plan subscription: 2000.00
    assert data["kpis"]["mrr"]["value"] == "2000.00"
    assert data["kpis"]["active_subscriptions"]["value"] == 1


def test_finance_overview_customer_filter(client):
    """Filters overview by customer_id=cust-002."""
    headers = {"Authorization": "Bearer dev-admin-token"}
    response = client.get(
        "/api/v1/finance/overview?start_date=2026-10-01&end_date=2026-10-31&customer_id=cust-002",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Customer 2 has yearly plan (10000.00 MRR) and paid 4000.00
    assert data["kpis"]["mrr"]["value"] == "10000.00"
    assert data["kpis"]["revenue_received"]["value"] == "4000.00"


def test_finance_security_customer_forbidden(client):
    """Customer role is rejected from accessing Finance Intelligence (403 Forbidden)."""
    headers = {"Authorization": "Bearer dev-customer-token"}
    response = client.get("/api/v1/finance/overview", headers=headers)
    assert response.status_code == 403


def test_metric_definitions_endpoint(client):
    """Verifies that mathematical definitions endpoint returns proper explanations."""
    headers = {"Authorization": "Bearer dev-staff-token"}
    response = client.get("/api/v1/finance/metrics/definitions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "mrr" in data
    assert "normalization" in data["mrr"]
    assert "DAILY" in data["mrr"]["normalization"]
