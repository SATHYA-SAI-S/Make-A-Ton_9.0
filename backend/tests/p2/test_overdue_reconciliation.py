from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.invoices.models import Invoice
from backend.app.payments.models import Payment, PaymentAllocation
from backend.app.payments.service import record_payment
from backend.app.overdue.models import PaymentFollowup
from backend.app.overdue.service import (
    get_overdue_invoices,
    get_overdue_summary,
    evaluate_and_send_reminders,
    record_manual_followup
)
from backend.app.reconciliation.service import (
    generate_reconciliation_report,
    auto_allocate_unallocated_credits
)

client = TestClient(app)

def create_invoice(customer_id: str, due_date: date, total: Decimal = Decimal("1000.00"), status: str = "CONFIRMED") -> Invoice:
    db = SessionLocal()
    inv = Invoice(
        number=f"INV-OD-{due_date.isoformat()}-{Decimal(total)}",
        customer_id=customer_id,
        status=status,
        invoice_date=due_date - timedelta(days=15),
        due_date=due_date,
        subtotal=total,
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        total=total,
        amount_paid=Decimal("0.00"),
        balance=total,
        currency="INR",
        snapshot={}
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    db.close()
    return inv

def test_overdue_invoices_detection_and_tiers():
    today = date.today()
    # Due 4 days ago -> Tier 1 (1-7 days)
    inv1 = create_invoice("cust-od-1", due_date=today - timedelta(days=4), total=Decimal("500.00"))
    # Due 10 days ago -> Tier 2 (8-14 days)
    inv2 = create_invoice("cust-od-1", due_date=today - timedelta(days=10), total=Decimal("800.00"))
    # Due 20 days ago -> Tier 3 (15+ days)
    inv3 = create_invoice("cust-od-2", due_date=today - timedelta(days=20), total=Decimal("1200.00"))
    # Due 5 days in future -> NOT overdue
    inv4 = create_invoice("cust-od-3", due_date=today + timedelta(days=5), total=Decimal("900.00"))

    overdue = get_overdue_invoices(as_of=today)
    assert len(overdue) == 3

    tier_map = {item["invoice_id"]: item["tier"] for item in overdue}
    assert tier_map[inv1.id] == 1
    assert tier_map[inv2.id] == 2
    assert tier_map[inv3.id] == 3

    summary = get_overdue_summary(as_of=today)
    assert summary["total_overdue_count"] == 3
    assert summary["total_overdue_amount"] == "2500.00"
    assert summary["tiers"]["tier_1"]["count"] == 1
    assert summary["tiers"]["tier_2"]["count"] == 1
    assert summary["tiers"]["tier_3"]["count"] == 1

def test_evaluate_and_send_reminders_idempotency():
    today = date.today()
    inv = create_invoice("cust-rem-1", due_date=today - timedelta(days=5))

    # First run sends Tier 1 reminder
    res1 = evaluate_and_send_reminders(as_of=today)
    assert res1["reminders_sent"] >= 1

    db = SessionLocal()
    followups = db.query(PaymentFollowup).filter_by(invoice_id=inv.id, tier=1).all()
    assert len(followups) == 1
    assert "Tier 1" in followups[0].notes
    db.close()

    # Second run skips already sent Tier 1 reminder
    res2 = evaluate_and_send_reminders(as_of=today)
    assert res2["reminders_sent"] == 0
    assert res2["reminders_skipped"] >= 1

def test_manual_followup_recording():
    today = date.today()
    inv = create_invoice("cust-mf-1", due_date=today - timedelta(days=3))

    followup = record_manual_followup(
        invoice_id=inv.id,
        notes="Customer called, promised payment by Friday",
        promised_payment_date=today + timedelta(days=4),
        channel="PHONE",
        status="PROMISED"
    )

    assert followup.invoice_id == inv.id
    assert followup.channel == "PHONE"
    assert followup.status == "PROMISED"

    # API read
    resp = client.get(f"/api/v1/overdue/followups/{inv.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["notes"] == "Customer called, promised payment by Friday"

def test_reconciliation_healthy_and_discrepancy_detection():
    # Healthy case
    inv = create_invoice("cust-rec-1", due_date=date.today(), total=Decimal("1000.00"))
    pay = record_payment(
        customer_id="cust-rec-1",
        method="CARD",
        amount=Decimal("1000.00"),
        allocations=[{"invoice_id": inv.id, "amount": Decimal("1000.00")}]
    )

    report = generate_reconciliation_report()
    assert report["is_healthy"] is True
    assert report["discrepancies_count"] == 0

    # Introduce discrepancy artificially: tamper amount_paid without matching allocation
    db = SessionLocal()
    db_inv = db.query(Invoice).filter_by(id=inv.id).first()
    db_inv.amount_paid = Decimal("500.00")
    db.commit()
    db.close()

    tampered_report = generate_reconciliation_report()
    assert tampered_report["is_healthy"] is False
    assert tampered_report["discrepancies_count"] > 0
    types = [d["type"] for d in tampered_report["discrepancies"]]
    assert "INVOICE_PAID_MISMATCH" in types

def test_auto_allocate_unallocated_credits():
    today = date.today()
    cust_id = "cust-auto-alloc"
    inv1 = create_invoice(cust_id, due_date=today - timedelta(days=10), total=Decimal("600.00"))
    inv2 = create_invoice(cust_id, due_date=today - timedelta(days=2), total=Decimal("400.00"))

    # Unallocated payment of 1000
    pay = record_payment(
        customer_id=cust_id,
        method="BANK_TRANSFER",
        amount=Decimal("1000.00")
    )
    assert pay.unallocated_amount == Decimal("1000.00")

    # Run auto-allocation
    result = auto_allocate_unallocated_credits(customer_id=cust_id)
    assert result["status"] == "COMPLETED"
    assert result["allocations_made"] == 2
    assert result["total_allocated"] == "1000.00"

    db = SessionLocal()
    check_inv1 = db.query(Invoice).filter_by(id=inv1.id).first()
    check_inv2 = db.query(Invoice).filter_by(id=inv2.id).first()
    check_pay = db.query(Payment).filter_by(id=pay.id).first()

    assert check_inv1.status == "PAID"
    assert check_inv1.balance == Decimal("0.00")
    assert check_inv2.status == "PAID"
    assert check_inv2.balance == Decimal("0.00")
    assert check_pay.unallocated_amount == Decimal("0.00")
    db.close()

def test_overdue_and_reconciliation_api_routes():
    # GET /api/v1/overdue/invoices
    resp_inv = client.get("/api/v1/overdue/invoices")
    assert resp_inv.status_code == 200

    # GET /api/v1/overdue/summary
    resp_sum = client.get("/api/v1/overdue/summary")
    assert resp_sum.status_code == 200
    assert "total_overdue_count" in resp_sum.json()

    # POST /api/v1/overdue/trigger-reminders
    resp_trig = client.post("/api/v1/overdue/trigger-reminders", json={})
    assert resp_trig.status_code == 200

    # GET /api/v1/reconciliation/report
    resp_rec = client.get("/api/v1/reconciliation/report")
    assert resp_rec.status_code == 200
    assert "metrics" in resp_rec.json()
