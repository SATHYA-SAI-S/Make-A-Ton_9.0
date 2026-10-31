"""
Unit and Integration tests for Financial Forecasting & Scenario Simulator (P3-T12).
Verifies:
1. Hand-calculated exact results for (+15% growth, 5% churn, 90% collection).
2. Zero assumptions equal baseline projection.
3. Step explanations match explainable model formulation.
4. Additive expansion and price-change adjustments.
5. Scenario persistence in forecast_scenarios table.
6. RBAC security: Customer role denied; staff/admin allowed.
7. Strict financial isolation invariant: Simulation never modifies financial tables.
"""
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.finance.models import (
    Customer,
    Plan,
    Subscription,
    Invoice,
    Payment,
    ForecastScenario,
)
from backend.app.finance.forecasting import (
    simulate_curve,
    run_forecast_simulation,
    save_forecast_scenario,
    list_forecast_scenarios,
    get_forecast_scenario,
    delete_forecast_scenario,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer dev-admin-token"}


@pytest.fixture
def customer_headers():
    return {"Authorization": "Bearer dev-customer-token"}


def test_hand_calculated_simulation_example():
    """
    Test: the example (+15% growth, 5% churn, 90% collection) matches a hand-calculated result.
    Starting MRR = 100,000.00.
    Month 1:
      100000 * (1 + 0.15 - 0.05) = 110000.00
      ARR = 110000 * 12 = 1320000.00
      Invoiced = 110000.00
      Collected = 110000 * 0.90 = 99000.00
      Outstanding = 110000 - 99000 = 11000.00
    Month 2:
      110000 * 1.10 = 121000.00
      ARR = 121000 * 12 = 1452000.00
      Invoiced = 121000.00
      Collected = 121000 * 0.90 = 108900.00
      Outstanding = 12100.00
    Month 3:
      121000 * 1.10 = 133100.00
      ARR = 133100 * 12 = 1597200.00
      Invoiced = 133100.00
      Collected = 133100 * 0.90 = 119790.00
      Outstanding = 13310.00
    """
    starting_mrr = Decimal("100000.00")
    assumptions = {
        "new_growth_pct": 15.0,
        "churn_pct": 5.0,
        "expansion_pct": 0.0,
        "contraction_pct": 0.0,
        "collection_rate_pct": 90.0,
        "price_increase_pct": 0.0,
        "discount_pct": 0.0,
    }
    curve = simulate_curve(
        starting_mrr=starting_mrr,
        assumptions=assumptions,
        horizon_months=3,
        start_date=date(2026, 1, 1),
    )

    assert len(curve) == 3

    # Month 1
    m1 = curve[0]
    assert m1["month"] == "2026-02"
    assert m1["mrr"] == "110000.00"
    assert m1["arr"] == "1320000.00"
    assert m1["projected_invoiced"] == "110000.00"
    assert m1["projected_collected"] == "99000.00"
    assert m1["projected_outstanding"] == "11000.00"
    assert "Starting MRR 100000.00 * (1 + 0.15 - 0.05)" in m1["step_explanation"]

    # Month 2
    m2 = curve[1]
    assert m2["month"] == "2026-03"
    assert m2["mrr"] == "121000.00"
    assert m2["arr"] == "1452000.00"
    assert m2["projected_invoiced"] == "121000.00"
    assert m2["projected_collected"] == "108900.00"
    assert m2["projected_outstanding"] == "12100.00"
    assert "Starting MRR 110000.00 * (1 + 0.15 - 0.05)" in m2["step_explanation"]

    # Month 3
    m3 = curve[2]
    assert m3["month"] == "2026-04"
    assert m3["mrr"] == "133100.00"
    assert m3["arr"] == "1597200.00"
    assert m3["projected_invoiced"] == "133100.00"
    assert m3["projected_collected"] == "119790.00"
    assert m3["projected_outstanding"] == "13310.00"


def test_zero_assumptions_equal_baseline(db_session):
    """
    Test: zero assumptions equal baseline projection.
    """
    plan = Plan(id="plan-core", name="Core Plan", price=Decimal("5000.00"), billing_frequency="MONTHLY")
    cust = Customer(id="cust-1", name="Acme Corp", email="acme@example.com")
    sub = Subscription(
        id="sub-1",
        number="SUB-001",
        customer_id="cust-1",
        plan_id="plan-core",
        status="ACTIVE",
        start_date=date(2026, 1, 1),
    )
    db_session.add_all([plan, cust, sub])
    db_session.commit()

    # Run with empty / zero assumptions
    res = run_forecast_simulation(db=db_session, horizon_months=6, assumptions={})

    baseline = res["baseline"]
    projection = res["projection"]

    assert len(baseline) == 6
    assert len(projection) == 6

    # Verify each month matches exactly
    for b, p in zip(baseline, projection):
        assert b["month"] == p["month"]
        assert b["mrr"] == p["mrr"]
        assert b["arr"] == p["arr"]
        assert b["projected_invoiced"] == p["projected_invoiced"]
        assert b["projected_collected"] == p["projected_collected"]
        assert b["projected_outstanding"] == p["projected_outstanding"]


def test_additive_expansion_and_price_adjustments():
    """
    Test expansion, contraction and price increase formulation.
    Starting: 184500.00
    new_growth: 12%, churn: 3%, contraction: 1% -> net factor 1.08 -> 199260.00
    expansion: 4% of 184500 = 7380.00
    Total next MRR = 199260 + 7380 = 206640.00
    """
    starting_mrr = Decimal("184500.00")
    assumptions = {
        "new_growth_pct": 12.0,
        "churn_pct": 3.0,
        "contraction_pct": 1.0,
        "expansion_pct": 4.0,
        "collection_rate_pct": 92.0,
    }
    curve = simulate_curve(
        starting_mrr=starting_mrr,
        assumptions=assumptions,
        horizon_months=1,
        start_date=date(2026, 10, 1),
    )

    m1 = curve[0]
    assert m1["mrr"] == "206640.00"
    assert "Starting MRR 184500.00 * (1 + 0.12 - 0.03 - 0.01) + expansion 7380.00" in m1["step_explanation"]
    # Collected at 92%: 206640 * 0.92 = 190108.80
    assert m1["projected_collected"] == "190108.80"
    assert m1["projected_outstanding"] == "16531.20"


def test_api_simulate_endpoint(client, admin_headers, customer_headers, db_session):
    """
    Test /api/v1/finance/forecast/simulate API endpoint with authentication and RBAC.
    """
    # 1. Customer token gets 403 Forbidden
    resp = client.post(
        "/api/v1/finance/forecast/simulate",
        json={"horizon_months": 12, "assumptions": {"new_growth_pct": 10.0}},
        headers=customer_headers,
    )
    assert resp.status_code == 403

    # 2. Staff/Admin gets 200 with complete projection
    resp = client.post(
        "/api/v1/finance/forecast/simulate",
        json={
            "horizon_months": 12,
            "starting_mrr": 50000.00,
            "assumptions": {
                "new_growth_pct": 10.0,
                "churn_pct": 2.0,
                "expansion_pct": 3.0,
                "contraction_pct": 1.0,
                "collection_rate_pct": 95.0,
                "price_increase_pct": 0.0,
            },
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "baseline" in data
    assert "projection" in data
    assert "summary" in data
    assert len(data["projection"]) == 12
    assert Decimal(data["summary"]["starting_mrr"]) == Decimal("50000.00")
    assert Decimal(data["summary"]["ending_mrr"]) > Decimal("50000.00")


def test_scenario_crud_lifecycle(client, admin_headers, db_session):
    """
    Test saving, listing, fetching and deleting simulation scenarios.
    """
    # Create scenario
    create_resp = client.post(
        "/api/v1/finance/forecast/scenarios",
        json={
            "name": "Q1 Aggressive Growth",
            "description": "Simulation with 15% new growth",
            "horizon_months": 6,
            "assumptions": {
                "new_growth_pct": 15.0,
                "churn_pct": 3.0,
                "collection_rate_pct": 92.0,
            },
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    scenario_id = create_resp.json()["id"]
    assert scenario_id is not None

    # List scenarios
    list_resp = client.get("/api/v1/finance/forecast/scenarios", headers=admin_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(s["id"] == scenario_id for s in items)

    # Get single scenario
    get_resp = client.get(f"/api/v1/finance/forecast/scenarios/{scenario_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    single = get_resp.json()
    assert single["name"] == "Q1 Aggressive Growth"
    assert "projection" in single
    assert len(single["projection"]) == 6

    # Delete scenario
    del_resp = client.delete(f"/api/v1/finance/forecast/scenarios/{scenario_id}", headers=admin_headers)
    assert del_resp.status_code == 200

    # Verify deleted
    get_again = client.get(f"/api/v1/finance/forecast/scenarios/{scenario_id}", headers=admin_headers)
    assert get_again.status_code == 404


def test_financial_tables_isolation_invariant(client, admin_headers, db_session):
    """
    Strict Person 3 Invariant:
    Simulation must NEVER write or mutate financial tables (subscriptions, invoices, payments).
    """
    # Count rows before simulation
    subs_before = db_session.query(Subscription).count()
    invs_before = db_session.query(Invoice).count()
    pmts_before = db_session.query(Payment).count()

    # Run simulations
    client.post(
        "/api/v1/finance/forecast/simulate",
        json={
            "horizon_months": 24,
            "starting_mrr": 75000.0,
            "assumptions": {"new_growth_pct": 25.0, "collection_rate_pct": 80.0},
        },
        headers=admin_headers,
    )

    # Count rows after simulation
    subs_after = db_session.query(Subscription).count()
    invs_after = db_session.query(Invoice).count()
    pmts_after = db_session.query(Payment).count()

    assert subs_before == subs_after
    assert invs_before == invs_after
    assert pmts_before == pmts_after
