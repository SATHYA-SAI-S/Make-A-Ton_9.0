"""
Unit & Integration Tests for Cohort Retention (P3-T10) & Revenue Concentration (P3-T11).
Validates mathematical retention reproduction (100/92/85/78), deterministic ties, and 100% share conservation.
"""
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.finance.cohorts import get_cohort_cell_customers, get_cohort_retention_matrix
from backend.app.finance.concentration import get_detailed_revenue_concentration
from backend.app.finance.models import Customer, Invoice, Plan, Subscription
from backend.app.main import app


@pytest.fixture
def cohort_seeded_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    plan = Plan(id="p-standard", name="Standard Plan", price=Decimal("100.00"), billing_frequency="MONTHLY")
    db.add(plan)

    # Seed 100 customers for January 2026 cohort
    # Target retention: Month 0: 100, Month 1: 92, Month 2: 85, Month 3: 78
    customers = []
    subscriptions = []

    for i in range(1, 101):
        cid = f"cust-jan-{i:03d}"
        cust = Customer(id=cid, name=f"Customer Jan {i}", email=f"jan{i}@example.com")
        customers.append(cust)

        # Expiry logic to achieve exact 100 -> 92 -> 85 -> 78 retention:
        # Customers 93..100 cancel after Month 0 (cancelled on 2026-01-31) -> 92 remain in Month 1
        # Customers 86..92 cancel after Month 1 (cancelled on 2026-02-28) -> 85 remain in Month 2
        # Customers 79..85 cancel after Month 2 (cancelled on 2026-03-31) -> 78 remain in Month 3
        if i > 92:
            status = "CLOSED"
            close_reason = "CANCELLED"
            exp_date = date(2026, 1, 31)
        elif i > 85:
            status = "CLOSED"
            close_reason = "CANCELLED"
            exp_date = date(2026, 2, 28)
        elif i > 78:
            status = "CLOSED"
            close_reason = "CANCELLED"
            exp_date = date(2026, 3, 31)
        else:
            status = "ACTIVE"
            close_reason = None
            exp_date = date(2027, 1, 1)

        sub = Subscription(
            id=f"sub-jan-{i:03d}",
            number=f"SUB-JAN-{i:03d}",
            customer_id=cid,
            plan_id="p-standard",
            status=status,
            close_reason=close_reason,
            start_date=date(2026, 1, 1),
            expiry_date=exp_date,
        )
        subscriptions.append(sub)

    db.add_all(customers)
    db.add_all(subscriptions)
    db.commit()

    yield db
    db.close()


@pytest.fixture
def concentration_seeded_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    plan_ent = Plan(id="plan-ent", name="Enterprise", price=Decimal("10000.00"), billing_frequency="MONTHLY")
    plan_pro = Plan(id="plan-pro", name="Pro Plan", price=Decimal("2000.00"), billing_frequency="MONTHLY")
    plan_basic = Plan(id="plan-basic", name="Basic Plan", price=Decimal("500.00"), billing_frequency="MONTHLY")
    db.add_all([plan_ent, plan_pro, plan_basic])

    # Seed 15 customers to test Top 10 + Others
    # Include a tie: cust-tie-A and cust-tie-B have identical MRR
    for i in range(1, 16):
        cid = f"cust-conc-{i:02d}"
        if i == 5:
            cid = "cust-tie-B"
        elif i == 6:
            cid = "cust-tie-A"

        c = Customer(id=cid, name=f"Concentration Cust {i}", email=f"conc{i}@example.com")
        db.add(c)

        # Vary MRR:
        # Cust 1: 50,000 (5 enterprise)
        # Cust 2: 30,000 (3 enterprise)
        # Cust 3: 20,000 (2 enterprise)
        # Cust 4: 10,000 (1 enterprise)
        # Cust 5 & 6: 10,000 (Tie!)
        # Cust 7-15: smaller amounts
        if i == 1:
            p = plan_ent
        elif i <= 6:
            p = plan_ent
        elif i <= 10:
            p = plan_pro
        else:
            p = plan_basic

        s = Subscription(
            id=f"sub-conc-{i}",
            number=f"SUB-CONC-{i}",
            customer_id=cid,
            plan_id=p.id,
            status="ACTIVE",
            start_date=date(2026, 1, 1)
        )
        db.add(s)

        # Seed invoice
        inv = Invoice(
            id=f"inv-conc-{i}",
            number=f"INV-CONC-{i}",
            customer_id=cid,
            status="CONFIRMED",
            invoice_date=date(2026, 10, 1),
            due_date=date(2026, 10, 15),
            total=p.price,
            amount_paid=p.price,
            balance=Decimal("0.00")
        )
        db.add(inv)

    db.commit()
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


# P3-T10 Tests: Cohorts
def test_reproduce_january_cohort_retention_example(cohort_seeded_db):
    """Reproduces the formal example: January cohort achieves Month 0=100%, M1=92%, M2=85%, M3=78%."""
    data = get_cohort_retention_matrix(db=cohort_seeded_db, lookback_months=12, max_offsets=6)
    cohorts = data["cohorts"]
    assert len(cohorts) >= 1

    jan_cohort = next(c for c in cohorts if c["cohort"] == "2026-01")
    assert jan_cohort["cohort_size"] == 100
    retention = jan_cohort["retention"]

    # Hand-computed retention checks matching problem statement
    assert retention[0] == 100.0  # Month 0 (Jan)
    assert retention[1] == 92.0   # Month 1 (Feb)
    assert retention[2] == 85.0   # Month 2 (Mar)
    assert retention[3] == 78.0   # Month 3 (Apr)


def test_cohort_cell_customers_drilldown(cohort_seeded_db):
    """Clicking a cell retrieves the exact retained customer accounts."""
    cell_data = get_cohort_cell_customers(db=cohort_seeded_db, cohort="2026-01", offset=1)
    assert cell_data["total"] == 92
    assert len(cell_data["customers"]) == 92
    # Verify Customer 93 is not in Month 1 (cancelled in Jan)
    cids = [c["customer_id"] for c in cell_data["customers"]]
    assert "cust-jan-001" in cids
    assert "cust-jan-092" in cids
    assert "cust-jan-093" not in cids


def test_cohort_api_endpoint(cohort_seeded_db):
    """Checks /api/v1/finance/charts/cohorts endpoint."""
    client = get_client(cohort_seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/cohorts?lookback_months=6&max_offsets=4", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["cohorts"]) >= 1


# P3-T11 Tests: Concentration
def test_revenue_concentration_shares_sum_to_100(concentration_seeded_db):
    """Verifies that top customer shares + others sum exactly to 100.0%."""
    data = get_detailed_revenue_concentration(db=concentration_seeded_db, top_n=10)
    top_share = data["pareto_summary"]["top_10_mrr_share_pct"]
    others_share = data["others_summary"]["mrr_share_pct"]
    assert Decimal(str(round(top_share + others_share, 2))) == Decimal("100.00")


def test_concentration_deterministic_tie_breaking(concentration_seeded_db):
    """Verifies deterministic sorting when two customers have identical MRR and revenue."""
    data = get_detailed_revenue_concentration(db=concentration_seeded_db, top_n=10)
    top_cids = [c["customer_id"] for c in data["top_customers"]]

    # Both cust-tie-A and cust-tie-B have 10,000 MRR
    # Due to deterministic customer_id tie-breaking: cust-tie-A must precede cust-tie-B
    assert "cust-tie-A" in top_cids
    assert "cust-tie-B" in top_cids
    idx_a = top_cids.index("cust-tie-A")
    idx_b = top_cids.index("cust-tie-B")
    assert idx_a < idx_b, "Tie must be broken deterministically by customer_id ASC"


def test_concentration_plan_breakdown(concentration_seeded_db):
    """Verifies each top customer includes plan-wise contribution details."""
    data = get_detailed_revenue_concentration(db=concentration_seeded_db, top_n=5)
    first_cust = data["top_customers"][0]
    assert len(first_cust["plan_breakdown"]) >= 1
    assert "plan_name" in first_cust["plan_breakdown"][0]
    assert "mrr" in first_cust["plan_breakdown"][0]


def test_concentration_api_endpoint(concentration_seeded_db):
    """Checks /api/v1/finance/charts/concentration endpoint."""
    client = get_client(concentration_seeded_db)
    headers = {"Authorization": "Bearer dev-admin-token"}
    res = client.get("/api/v1/finance/charts/concentration?top_n=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["top_customers"]) == 5
    assert "pareto_summary" in data
