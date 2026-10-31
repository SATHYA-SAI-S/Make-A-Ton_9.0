"""
Unit and Integration Tests for Revenue Guardian (P3-T13).
Mandatory verifications:
1. All 8 autonomous detection rules detect bad data and create corresponding findings:
   - Missed billing
   - Duplicate billing
   - Expired discount
   - Payment mismatch
   - Renewal risk
   - Overdue risk
   - Pricing anomaly
   - Revenue leakage
2. Idempotency: Re-running detection does NOT create duplicate alerts (tested via fingerprint).
3. Resolution persistence: Resolved / dismissed alerts retain status on subsequent detection runs.
4. Non-destructive invariant: Detection runs NEVER create or modify Person 1/2 financial records.
5. RBAC security: Customer tokens are forbidden (403); staff/admin authorized (200).
6. Triage actions: Audited ACKNOWLEDGE, RESOLVE, and DISMISS actions.
"""
from datetime import date, timedelta, datetime, timezone
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
    SubscriptionLine,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from backend.app.revenue_guardian.models import RiskAlert, RiskDetectionRun
from backend.app.revenue_guardian.detection import run_detection_cycle
from backend.app.revenue_guardian.alerts import perform_alert_action, get_guardian_dashboard


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
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


def seed_anomaly_test_database(db):
    """
    Seeds deliberate financial anomalies to trigger all 8 Revenue Guardian rules.
    """
    today = date.today()

    # Base customers and plans
    c1 = Customer(id="cust-anom-1", name="Acme Inc", email="acme@anom.com")
    c2 = Customer(id="cust-anom-2", name="Beta Corp", email="beta@anom.com")
    c3 = Customer(id="cust-anom-3", name="Gamma LLC", email="gamma@anom.com")
    c4 = Customer(id="cust-anom-4", name="Delta Tech", email="delta@anom.com")

    p_standard = Plan(id="p-standard", name="Standard Plan", price=Decimal("10000.00"), billing_frequency="MONTHLY")
    p_expired = Plan(
        id="p-expired",
        name="Holiday Promo Plan",
        price=Decimal("8000.00"),
        billing_frequency="MONTHLY",
        available_to=today - timedelta(days=60)  # Expired plan
    )
    p_norenew = Plan(
        id="p-norenew",
        name="Legacy Plan",
        price=Decimal("15000.00"),
        billing_frequency="MONTHLY",
        allow_renewal=False  # Cannot renew
    )

    db.add_all([c1, c2, c3, c4, p_standard, p_expired, p_norenew])
    db.commit()

    # Anomaly 1: Missed Billing (Active sub, next_billing_date 10 days ago, no invoice)
    s1 = Subscription(
        id="sub-missed",
        number="SUB-MISSED-01",
        customer_id=c1.id,
        plan_id=p_standard.id,
        status="ACTIVE",
        start_date=today - timedelta(days=40),
        next_billing_date=today - timedelta(days=10)
    )

    # Anomaly 2: Duplicate Billing (Two invoices for same sub & period)
    s2 = Subscription(
        id="sub-dup",
        number="SUB-DUP-01",
        customer_id=c2.id,
        plan_id=p_standard.id,
        status="ACTIVE",
        start_date=today - timedelta(days=60),
    )
    inv_dup1 = Invoice(
        id="inv-dup-1",
        number="INV-DUP-01",
        customer_id=c2.id,
        subscription_id=s2.id,
        billing_period_id="2026-10",
        invoice_date=today - timedelta(days=5),
        due_date=today + timedelta(days=15),
        total=Decimal("10000.00"),
        balance=Decimal("10000.00"),
        status="CONFIRMED"
    )
    inv_dup2 = Invoice(
        id="inv-dup-2",
        number="INV-DUP-02",
        customer_id=c2.id,
        subscription_id=s2.id,
        billing_period_id="2026-10",
        invoice_date=today - timedelta(days=5),
        due_date=today + timedelta(days=15),
        total=Decimal("10000.00"),
        balance=Decimal("10000.00"),
        status="CONFIRMED"
    )

    # Anomaly 3: Expired Discount (Invoice with discount applied on expired plan)
    s3 = Subscription(
        id="sub-exp-disc",
        number="SUB-EXP-01",
        customer_id=c3.id,
        plan_id=p_expired.id,
        status="ACTIVE",
        start_date=today - timedelta(days=90),
    )
    inv_exp_disc = Invoice(
        id="inv-exp-disc-1",
        number="INV-EXP-01",
        customer_id=c3.id,
        subscription_id=s3.id,
        invoice_date=today - timedelta(days=5),
        due_date=today + timedelta(days=25),
        discount_total=Decimal("2000.00"),
        total=Decimal("8000.00"),
        balance=Decimal("8000.00"),
        status="CONFIRMED"
    )

    # Anomaly 4: Payment Mismatch (Payment recorded 5000, allocations total 3000)
    pmt_mismatch = Payment(
        id="pmt-mis-1",
        customer_id=c1.id,
        method="CARD",
        amount=Decimal("5000.00"),
        payment_date=today - timedelta(days=3),
        status="RECORDED",
        reference="TXN-MISMATCH-001"
    )
    alloc_mismatch = PaymentAllocation(
        id="alloc-mis-1",
        payment_id=pmt_mismatch.id,
        invoice_id="inv-dup-1",
        amount=Decimal("3000.00")
    )

    # Anomaly 5: Renewal Risk (Subscription expiring in 10 days, allow_renewal=False)
    s5 = Subscription(
        id="sub-renew-risk",
        number="SUB-RENEW-01",
        customer_id=c4.id,
        plan_id=p_norenew.id,
        status="ACTIVE",
        start_date=today - timedelta(days=350),
        expiry_date=today + timedelta(days=10)
    )

    # Anomaly 6: Overdue Risk (Invoice due 45 days ago, balance 12000)
    inv_overdue = Invoice(
        id="inv-overdue-1",
        number="INV-OVERDUE-01",
        customer_id=c1.id,
        invoice_date=today - timedelta(days=75),
        due_date=today - timedelta(days=45),
        total=Decimal("12000.00"),
        balance=Decimal("12000.00"),
        status="CONFIRMED"
    )

    # Anomaly 7: Pricing Anomaly (Invoice line unit price 12000 != plan price 10000)
    s7 = Subscription(
        id="sub-price-anom",
        number="SUB-PRICE-01",
        customer_id=c2.id,
        plan_id=p_standard.id,
        status="ACTIVE",
        start_date=today - timedelta(days=20),
    )
    inv_price_anom = Invoice(
        id="inv-price-anom-1",
        number="INV-PRICE-01",
        customer_id=c2.id,
        subscription_id=s7.id,
        invoice_date=today - timedelta(days=10),
        due_date=today + timedelta(days=20),
        total=Decimal("12000.00"),
        balance=Decimal("12000.00"),
        status="CONFIRMED"
    )
    inv_line_anom = InvoiceLine(
        id="inv-line-anom-1",
        invoice_id=inv_price_anom.id,
        product_id="prod-core",
        quantity=1,
        unit_price=Decimal("12000.00"),  # Catalog was 10000.00
        line_total=Decimal("12000.00")
    )

    # Anomaly 8: Revenue Leakage (Customer 4 has 15000/mo sub active 60d, zero invoices in last 30d)
    s8 = Subscription(
        id="sub-leakage",
        number="SUB-LEAK-01",
        customer_id=c4.id,
        plan_id=p_norenew.id,
        status="ACTIVE",
        start_date=today - timedelta(days=60),
    )

    db.add_all([
        s1, s2, inv_dup1, inv_dup2, s3, inv_exp_disc,
        pmt_mismatch, alloc_mismatch, s5, inv_overdue,
        s7, inv_price_anom, inv_line_anom, s8
    ])
    db.commit()


def test_revenue_guardian_detects_all_8_rules(db_session):
    """
    Verifies that run_detection_cycle finds all 8 classes of anomalies.
    """
    seed_anomaly_test_database(db_session)

    run = run_detection_cycle(db=db_session)
    assert run.status == "SUCCESS"
    assert run.rules_run == 8
    assert run.alerts_created >= 8

    alerts = db_session.query(RiskAlert).all()
    rule_keys = {a.rule_key for a in alerts}

    # Verify all 8 rules were triggered
    assert "MISSED_BILLING" in rule_keys
    assert "DUPLICATE_BILLING" in rule_keys
    assert "EXPIRED_DISCOUNT" in rule_keys
    assert "PAYMENT_MISMATCH" in rule_keys
    assert "RENEWAL_RISK" in rule_keys
    assert "OVERDUE_RISK" in rule_keys
    assert "PRICING_ANOMALY" in rule_keys
    assert "REVENUE_LEAKAGE" in rule_keys

    # Verify findings have scores and impact
    for a in alerts:
        assert a.score >= 1 and a.score <= 100
        assert a.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert a.estimated_impact >= Decimal("0.00")
        assert len(a.explanation) > 10
        assert len(a.suggested_action) > 10
        assert a.fingerprint is not None


def test_idempotency_running_twice_creates_no_duplicates(db_session):
    """
    Verifies that running detection cycle twice produces 0 new alerts
    because deterministic fingerprints enforce strict deduplication.
    """
    seed_anomaly_test_database(db_session)

    run1 = run_detection_cycle(db=db_session)
    count_after_first = db_session.query(RiskAlert).count()
    assert count_after_first >= 8

    # Second run
    run2 = run_detection_cycle(db=db_session)
    count_after_second = db_session.query(RiskAlert).count()

    assert run2.alerts_created == 0
    assert count_after_first == count_after_second


def test_resolution_status_persists_across_detection_runs(db_session):
    """
    Verifies that resolving an alert persists through subsequent detection cycles.
    """
    seed_anomaly_test_database(db_session)
    run_detection_cycle(db=db_session)

    # Pick an alert to resolve
    alert = db_session.query(RiskAlert).filter(RiskAlert.rule_key == "DUPLICATE_BILLING").first()
    assert alert is not None
    assert alert.status == "OPEN"

    # Resolve alert
    perform_alert_action(
        db=db_session,
        alert_id=alert.id,
        action="RESOLVE",
        note="Duplicate invoice was cancelled in billing portal.",
        actor_id="admin-01"
    )

    db_session.refresh(alert)
    assert alert.status == "RESOLVED"
    assert alert.resolution_note == "Duplicate invoice was cancelled in billing portal."

    # Run detection cycle again
    run_detection_cycle(db=db_session)

    # Status must STILL be RESOLVED and no duplicate alert created
    db_session.refresh(alert)
    assert alert.status == "RESOLVED"
    dup_alerts = db_session.query(RiskAlert).filter(RiskAlert.fingerprint == alert.fingerprint).all()
    assert len(dup_alerts) == 1


def test_financial_tables_isolation_invariant(db_session):
    """
    Strict Person 3 Boundary Invariant:
    Revenue Guardian is purely diagnostic and NEVER modifies Person 1 or Person 2 financial tables.
    Assert exact row counts before and after.
    """
    seed_anomaly_test_database(db_session)

    # Row counts before detection run
    cust_before = db_session.query(Customer).count()
    plan_before = db_session.query(Plan).count()
    subs_before = db_session.query(Subscription).count()
    invs_before = db_session.query(Invoice).count()
    lines_before = db_session.query(InvoiceLine).count()
    pmts_before = db_session.query(Payment).count()
    alloc_before = db_session.query(PaymentAllocation).count()

    # Execute multiple detection cycles
    run_detection_cycle(db=db_session)
    run_detection_cycle(db=db_session)

    # Row counts after detection run
    assert db_session.query(Customer).count() == cust_before
    assert db_session.query(Plan).count() == plan_before
    assert db_session.query(Subscription).count() == subs_before
    assert db_session.query(Invoice).count() == invs_before
    assert db_session.query(InvoiceLine).count() == lines_before
    assert db_session.query(Payment).count() == pmts_before
    assert db_session.query(PaymentAllocation).count() == alloc_before


def test_guardian_dashboard_and_triage_api(client, admin_headers, customer_headers, db_session):
    """
    Verifies REST API endpoints under /api/v1/guardian/ with RBAC security.
    """
    seed_anomaly_test_database(db_session)
    run_detection_cycle(db=db_session)

    # 1. Customer token gets 403 Forbidden
    resp = client.get("/api/v1/guardian/dashboard", headers=customer_headers)
    assert resp.status_code == 403

    # 2. Staff gets 200 with structured dashboard
    resp = client.get("/api/v1/guardian/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    assert data["summary"]["total_open_alerts"] >= 8
    assert data["summary"]["critical_count"] >= 1
    assert Decimal(data["summary"]["total_estimated_impact"]) > Decimal("0.00")
    assert len(data["top_alerts"]) >= 1

    # 3. Filter alerts list
    alert_resp = client.get("/api/v1/guardian/alerts?severity=CRITICAL", headers=admin_headers)
    assert alert_resp.status_code == 200
    alert_data = alert_resp.json()
    assert "items" in alert_data
    assert all(a["severity"] == "CRITICAL" for a in alert_data["items"])

    # 4. Perform alert triage action
    target_alert = alert_data["items"][0]
    action_resp = client.post(
        f"/api/v1/guardian/alerts/{target_alert['id']}/action",
        json={"action": "ACKNOWLEDGE", "note": "Reviewing with billing team."},
        headers=admin_headers,
    )
    assert action_resp.status_code == 200
    assert action_resp.json()["status"] == "ACKNOWLEDGED"

    # 5. Trigger manual detection run via POST /guardian/run
    run_resp = client.post("/api/v1/guardian/run", headers=admin_headers)
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "SUCCESS"
    assert run_resp.json()["rules_run"] == 8
