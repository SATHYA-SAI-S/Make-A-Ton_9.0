"""
Unit & Integration Tests for The 10 Finance Visualizations Backend (P3-T08).
Validates mathematical calculations, empty data resilience, and drilldown link integrity.
"""
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.finance.models import (
    Customer,
    Invoice,
    Payment,
    Plan,
    Refund,
    Subscription,
)
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

    # Seed Customers
    c1 = Customer(id="c-ch-1", name="Alpha Alpha", email="alpha@example.com")
    c2 = Customer(id="c-ch-2", name="Beta Beta", email="beta@example.com")
    db.add_all([c1, c2])

    # Seed Plans
    p1 = Plan(id="plan_monthly", name="Monthly Pro", price=Decimal("3000.00"), billing_frequency="MONTHLY")
    p2 = Plan(id="plan_yearly", name="Yearly Enterprise", price=Decimal("120000.00"), billing_frequency="YEARLY")
    db.add_all([p1, p2])

    # Seed Subscriptions
    s1 = Subscription(
        id="s-ch-1", number="SUB-CH-1", customer_id="c-ch-1", plan_id="plan_monthly",
        status="ACTIVE", start_date=date(2026, 6, 1), expiry_date=date(2027, 6, 1)
    )
    s2 = Subscription(
        id="s-ch-2", number="SUB-CH-2", customer_id="c-ch-2", plan_id="plan_yearly",
        status="ACTIVE", start_date=date(2026, 8, 1), expiry_date=date(2027, 8, 1)
    )
    s_closed = Subscription(
        id="s-ch-3", number="SUB-CH-3", customer_id="c-ch-1", plan_id="plan_monthly",
        status="CLOSED", close_reason="CANCELLED", start_date=date(2026, 1, 1), expiry_date=date(2026, 10, 1)
    )
    db.add_all([s1, s2, s_closed])

    # Seed Invoices
    inv1 = Invoice(
        id="inv-ch-1", number="INV-CH-1", customer_id="c-ch-1", subscription_id="s-ch-1",
        status="PAID", invoice_date=date(2026, 10, 1), due_date=date(2026, 10, 15),
        total=Decimal("3000.00"), amount_paid=Decimal("3000.00"), balance=Decimal("0.00")
    )
    inv2 = Invoice(
        id="inv-ch-2", number="INV-CH-2", customer_id="c-ch-2", subscription_id="s-ch-2",
        status="PARTIALLY_PAID", invoice_date=date(2026, 10, 5), due_date=date(2026, 10, 20),
        total=Decimal("10000.00"), amount_paid=Decimal("4000.00"), balance=Decimal("6000.00")
    )
    inv3 = Invoice(
        id="inv-ch-3", number="INV-CH-3", customer_id="c-ch-2", subscription_id="s-ch-2",
        status="CONFIRMED", invoice_date=date(2026, 8, 1), due_date=date(2026, 8, 15),
        total=Decimal("5000.00"), amount_paid=Decimal("0.00"), balance=Decimal("5000.00")
    )
    db.add_all([inv1, inv2, inv3])

    # Seed Payments
    pay1 = Payment(
        id="pay-ch-1", customer_id="c-ch-1", method="UPI",
        amount=Decimal("3000.00"), payment_date=date(2026, 10, 2), status="RECORDED"
    )
    pay2 = Payment(
        id="pay-ch-2", customer_id="c-ch-2", method="BANK_TRANSFER",
        amount=Decimal("4000.00"), payment_date=date(2026, 10, 10), status="RECORDED"
    )
    db.add_all([pay1, pay2])

    db.commit()
    yield db
    db.close()


@pytest.fixture
def empty_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    yield db
    db.close()


def get_client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# 1. Chart 1: Revenue Performance
def test_chart_revenue_performance(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/revenue-performance?start_date=2026-08-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) >= 2

    # Verify October month
    oct_data = next((d for d in data if d["period"] == "2026-10"), None)
    assert oct_data is not None
    # Invoiced in Oct: 3000 + 10000 = 13000.00
    assert oct_data["invoiced"] == "13000.00"
    # Collected in Oct: 3000 + 4000 = 7000.00
    assert oct_data["collected"] == "7000.00"
    # Drilldown link present
    assert "drilldown" in oct_data
    assert oct_data["drilldown"]["filters"]["period"] == "2026-10"


# 2. Chart 2: Subscription Distribution
def test_chart_subscription_distribution(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/subscription-distribution?as_of=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_active_subscriptions"] == 2
    # MRR: 3000.00 (Monthly) + 10000.00 (Yearly 120000/12) = 13000.00
    assert data["total_mrr"] == "13000.00"

    # Frequency check
    by_freq = data["by_frequency"]
    assert len(by_freq) == 2
    for item in by_freq:
        assert item["frequency"] in ["MONTHLY", "YEARLY"]
        assert "drilldown" in item


# 3. Chart 3: Invoice Aging Buckets
def test_chart_invoice_aging(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    # As of 2026-10-31:
    # inv2: due 2026-10-20 -> (10-31 - 10-20) = 11 days overdue -> '1_30' bucket, balance 6000.00
    # inv3: due 2026-08-15 -> (10-31 - 08-15) = 77 days overdue -> '61_90' bucket, balance 5000.00
    res = client.get("/api/v1/finance/charts/invoice-aging?as_of=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_outstanding"] == "11000.00"
    b_1_30 = next(b for b in data["buckets"] if b["bucket"] == "1_30")
    assert b_1_30["amount"] == "6000.00"
    assert b_1_30["count"] == 1

    b_61_90 = next(b for b in data["buckets"] if b["bucket"] == "61_90")
    assert b_61_90["amount"] == "5000.00"
    assert b_61_90["count"] == 1


# 4. Chart 4: Subscription Growth
def test_chart_subscription_growth(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/subscription-growth?start_date=2026-06-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


# 5. Chart 5: MRR Trend
def test_chart_mrr_trend(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/mrr-trend?start_date=2026-06-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    latest = data[-1]
    assert "mrr" in latest
    assert "arr" in latest
    assert "rolling_avg_3m" in latest


# 6. Chart 6: MRR Waterfall
def test_chart_mrr_waterfall(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/mrr-waterfall?start_date=2026-09-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "starting_mrr" in data
    assert "ending_mrr" in data
    assert "steps" in data
    assert len(data["steps"]) == 6


# 7. Chart 7: Cohort Retention Heatmap
def test_chart_cohorts(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/cohorts?lookback_months=6", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "intervals" in data
    assert "cohorts" in data


# 8. Chart 8: Revenue Concentration
def test_chart_revenue_concentration(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/concentration?top_n=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "top_customers" in data
    assert "pareto_summary" in data


# 9. Chart 9: Collection Funnel
def test_chart_collection_funnel(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/collection-funnel?start_date=2026-08-01&end_date=2026-10-31", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "stages" in data
    stages = data["stages"]
    assert len(stages) == 4
    stage_names = [s["stage"] for s in stages]
    assert stage_names == ["GENERATED", "CONFIRMED", "PARTIALLY_PAID", "PAID"]


# 10. Chart 10: Forecast Baseline
def test_chart_forecast_baseline(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/forecast?horizon_months=12", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["horizon_months"] == 12
    assert len(data["baseline"]) == 12


# 11. Empty Data Resilience (Returns empty structures / zeros, never 500 error)
def test_empty_database_chart_resilience(empty_db):
    client = get_client(empty_db)
    headers = {"Authorization": "Bearer dev-admin-token"}

    # Performance
    r1 = client.get("/api/v1/finance/charts/revenue-performance", headers=headers)
    assert r1.status_code == 200
    assert r1.json() == []

    # Distribution
    r2 = client.get("/api/v1/finance/charts/subscription-distribution", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["total_active_subscriptions"] == 0

    # Aging
    r3 = client.get("/api/v1/finance/charts/invoice-aging", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["total_outstanding"] == "0.00"

    # Growth
    r4 = client.get("/api/v1/finance/charts/subscription-growth", headers=headers)
    assert r4.status_code == 200
    assert r4.json() == []


# 12. Security Test: Customer is Forbidden
def test_charts_security_customer_forbidden(seeded_db):
    client = get_client(seeded_db)
    headers = {"Authorization": "Bearer dev-customer-token"}
    res = client.get("/api/v1/finance/charts/revenue-performance", headers=headers)
    assert res.status_code == 403
