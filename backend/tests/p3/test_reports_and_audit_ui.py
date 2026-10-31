"""
Unit and Integration Tests for Financial Reports & Audit UI (P3-T14).
Mandatory verifications:
1. Reports Catalog returns all 6 core financial reports.
2. All 6 reports generate valid JSON structures.
3. Memory-efficient CSV streaming produces valid CSV data matching records.
4. ReportLab PDF generator produces valid PDF binary payloads (%PDF- header).
5. Audit logging, multi-dimensional querying, and ready-made views.
6. Audit field-level diff isolates changed fields only (unchanged fields omitted).
7. Strict RBAC enforcement: Customer tokens receive 403 Forbidden on reports & audit endpoints.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import io
import csv
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.finance.models import (
    Customer,
    Plan,
    Subscription,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from app.audit.models import AuditLog
from app.audit.service import emit_audit_event, compute_diff
from app.reports.pdf_generator import generate_report_pdf


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


@pytest.fixture
def seeded_db(db_session):
    """Seeds test data for report generation and audit trail verification."""
    today = date.today()

    # 1. Customers
    c1 = Customer(id="cust-rep-1", name="Alpha Enterprises", email="alpha@test.com")
    c2 = Customer(id="cust-rep-2", name="Beta Tech", email="beta@test.com")
    db_session.add_all([c1, c2])

    # 2. Plans
    p1 = Plan(id="plan-gold", name="Gold Tier", price=Decimal("10000.00"), billing_frequency="MONTHLY")
    p2 = Plan(id="plan-silver", name="Silver Tier", price=Decimal("5000.00"), billing_frequency="MONTHLY")
    db_session.add_all([p1, p2])

    # 3. Subscriptions
    s1 = Subscription(
        id="sub-rep-1",
        number="SUB-001",
        customer_id=c1.id,
        plan_id=p1.id,
        status="ACTIVE",
        start_date=today - timedelta(days=90),
    )
    s2 = Subscription(
        id="sub-rep-2",
        number="SUB-002",
        customer_id=c2.id,
        plan_id=p2.id,
        status="CANCELLED",
        start_date=today - timedelta(days=120),
    )
    db_session.add_all([s1, s2])

    # 4. Invoices
    inv1 = Invoice(
        id="inv-rep-1",
        customer_id=c1.id,
        subscription_id=s1.id,
        number="INV-2026-001",
        invoice_date=today - timedelta(days=60),
        due_date=today - timedelta(days=30),
        status="PAID",
        subtotal=Decimal("10000.00"),
        tax_total=Decimal("1800.00"),
        discount_total=Decimal("500.00"),
        total=Decimal("11300.00"),
        amount_paid=Decimal("11300.00"),
        balance=Decimal("0.00"),
    )
    inv2 = Invoice(
        id="inv-rep-2",
        customer_id=c2.id,
        subscription_id=s2.id,
        number="INV-2026-002",
        invoice_date=today - timedelta(days=15),
        due_date=today - timedelta(days=5),
        status="CONFIRMED",
        subtotal=Decimal("5000.00"),
        tax_total=Decimal("900.00"),
        discount_total=Decimal("0.00"),
        total=Decimal("5900.00"),
        amount_paid=Decimal("0.00"),
        balance=Decimal("5900.00"),
    )
    db_session.add_all([inv1, inv2])

    # 5. Invoice lines
    line1 = InvoiceLine(
        id="line-rep-1",
        invoice_id=inv1.id,
        product_id="prod-gold",
        description="Gold Tier Subscription",
        quantity=1,
        unit_price=Decimal("10000.00"),
        line_total=Decimal("10000.00"),
    )
    db_session.add(line1)

    # 6. Payment & Allocation
    pay1 = Payment(
        id="pay-rep-1",
        customer_id=c1.id,
        reference="PAY-REF-001",
        payment_date=today - timedelta(days=25),
        amount=Decimal("11300.00"),
        method="BANK_TRANSFER",
        status="RECORDED",
    )
    db_session.add(pay1)

    alloc1 = PaymentAllocation(
        id="alloc-rep-1",
        payment_id=pay1.id,
        invoice_id=inv1.id,
        amount=Decimal("11300.00"),
    )
    db_session.add(alloc1)

    db_session.commit()
    return db_session


def test_reports_catalog(client, admin_headers, customer_headers):
    """Verifies that catalog lists 6 financial reports and enforces RBAC."""
    # Staff / Admin access
    res = client.get("/api/v1/reports/catalog", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "reports" in data
    assert len(data["reports"]) == 6
    report_ids = [r["id"] for r in data["reports"]]
    assert "monthly-financial" in report_ids
    assert "revenue" in report_ids
    assert "outstanding-invoices" in report_ids
    assert "payments" in report_ids
    assert "subscriptions" in report_ids
    assert "discount-performance" in report_ids

    # Customer token access -> 403 Forbidden
    res_cust = client.get("/api/v1/reports/catalog", headers=customer_headers)
    assert res_cust.status_code == 403


def test_monthly_financial_report(client, seeded_db, admin_headers):
    """Tests monthly financial pack in JSON, CSV, and PDF formats."""
    # 1. JSON format
    res_json = client.get("/api/v1/reports/monthly-financial?format=json", headers=admin_headers)
    assert res_json.status_code == 200
    data = res_json.json()
    assert "headers" in data
    assert "rows" in data
    assert "summary" in data
    assert len(data["rows"]) >= 1

    # 2. CSV streaming format
    res_csv = client.get("/api/v1/reports/monthly-financial?format=csv", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert 'filename="monthly_financial_pack.csv"' in res_csv.headers["content-disposition"]
    csv_text = res_csv.text
    csv_reader = list(csv.reader(io.StringIO(csv_text)))
    assert len(csv_reader) >= 2  # Header + at least 1 data row
    assert "Month" in csv_reader[0]

    # 3. ReportLab PDF generation
    res_pdf = client.get("/api/v1/reports/monthly-financial?format=pdf", headers=admin_headers)
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert 'filename="monthly_financial_pack.pdf"' in res_pdf.headers["content-disposition"]
    assert res_pdf.content.startswith(b"%PDF-")


def test_revenue_ledger_report(client, seeded_db, admin_headers):
    """Tests revenue & invoicing ledger report."""
    res = client.get("/api/v1/reports/revenue?format=json", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 2  # 2 seeded invoices
    assert "INV-2026-001" in str(data["rows"])
    assert "INV-2026-002" in str(data["rows"])

    # CSV
    res_csv = client.get("/api/v1/reports/revenue?format=csv", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "INV-2026-001" in res_csv.text

    # PDF
    res_pdf = client.get("/api/v1/reports/revenue?format=pdf", headers=admin_headers)
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")


def test_outstanding_invoices_report(client, seeded_db, admin_headers):
    """Tests outstanding receivables & aging report."""
    res = client.get("/api/v1/reports/outstanding-invoices?format=json", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 1  # 1 unpaid invoice (inv-rep-2)
    assert "INV-2026-002" in str(data["rows"])

    # PDF
    res_pdf = client.get("/api/v1/reports/outstanding-invoices?format=pdf", headers=admin_headers)
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")


def test_payments_report(client, seeded_db, admin_headers):
    """Tests cash payments & settlements ledger report."""
    res = client.get("/api/v1/reports/payments?format=json", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 1
    assert "PAY-REF-001" in str(data["rows"])

    # CSV
    res_csv = client.get("/api/v1/reports/payments?format=csv", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "BANK_TRANSFER" in res_csv.text


def test_subscriptions_report(client, seeded_db, admin_headers):
    """Tests subscriptions portfolio report with filtering."""
    # All subscriptions
    res = client.get("/api/v1/reports/subscriptions?format=json", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 2

    # Filtered by ACTIVE
    res_active = client.get("/api/v1/reports/subscriptions?format=json&status=ACTIVE", headers=admin_headers)
    assert res_active.status_code == 200
    assert len(res_active.json()["rows"]) == 1
    assert "ACTIVE" in str(res_active.json()["rows"])


def test_discount_performance_report(client, seeded_db, admin_headers):
    """Tests discount performance and leakage report."""
    res = client.get("/api/v1/reports/discount-performance?format=json", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 1  # 1 invoice with discount (inv1 has 500.00 discount)
    assert "INV-2026-001" in str(data["rows"])


def test_audit_diff_changed_fields_only(client, seeded_db, admin_headers):
    """
    Verifies that audit field-level diff isolates changed fields only.
    Unchanged attributes MUST be omitted from the diff dictionary.
    """
    before_snap = {
        "price": 10000.00,
        "name": "Gold Tier Plan",
        "billing_frequency": "MONTHLY",
        "description": "Standard gold features"
    }
    after_snap = {
        "price": 12500.00,
        "name": "Gold Tier Plan",  # Unchanged
        "billing_frequency": "ANNUAL",  # Changed
        "description": "Standard gold features"  # Unchanged
    }

    log_id = emit_audit_event(
        actor_id="usr-staff-001",
        action="plan.updated",
        entity_type="plan",
        entity_id="plan-gold",
        before=before_snap,
        after=after_snap,
        actor_role="staff",
        db=seeded_db
    )

    # Direct function test
    diff = compute_diff(before_snap, after_snap)
    assert "price" in diff
    assert "billing_frequency" in diff
    assert "name" not in diff  # Must omit unchanged field
    assert "description" not in diff  # Must omit unchanged field
    assert diff["price"]["before"] == 10000.00
    assert diff["price"]["after"] == 12500.00
    assert diff["billing_frequency"]["before"] == "MONTHLY"
    assert diff["billing_frequency"]["after"] == "ANNUAL"

    # API detail test
    res = client.get(f"/api/v1/audit/logs/{log_id}", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == log_id
    assert "diff" in data
    assert "price" in data["diff"]
    assert "billing_frequency" in data["diff"]
    assert "name" not in data["diff"]


def test_audit_query_and_views(client, seeded_db, admin_headers, customer_headers):
    """Tests audit log querying and ready-made audit views."""
    # 1. Price modification history view
    res_price = client.get("/api/v1/audit/views/price-history", headers=admin_headers)
    assert res_price.status_code == 200

    # 2. Plan history view
    res_plan = client.get("/api/v1/audit/views/plan-history", headers=admin_headers)
    assert res_plan.status_code == 200

    # 3. Invoice cancellations view
    res_canc = client.get("/api/v1/audit/views/invoice-cancellations", headers=admin_headers)
    assert res_canc.status_code == 200

    # 4. Subscription lifecycle view
    res_life = client.get("/api/v1/audit/views/subscription-lifecycle", headers=admin_headers)
    assert res_life.status_code == 200

    # 5. Customer role forbidden
    res_cust = client.get("/api/v1/audit/logs", headers=customer_headers)
    assert res_cust.status_code == 403
