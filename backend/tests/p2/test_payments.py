import hmac
import hashlib
import json
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.main import app
from backend.app.shared.dto import CustomerDTO
from backend.app.shared.registry import get_port
from backend.app.invoices.models import Invoice
from backend.app.payments.models import Payment, PaymentAllocation, PaymentRefund
from backend.app.payments.service import (
    record_payment,
    allocate_payment,
    record_refund,
    record_failed_payment
)
from backend.app.payments.gateway import (
    create_gateway_order,
    verify_gateway_signature,
    process_gateway_webhook
)

client = TestClient(app)

def seed_invoice(
    customer_id: str = "cust-p9-001",
    total: Decimal = Decimal("1000.00"),
    status: str = "CONFIRMED"
) -> Invoice:
    db = SessionLocal()
    inv = Invoice(
        number=f"INV-TEST-{Decimal(total)}",
        customer_id=customer_id,
        status=status,
        invoice_date=date.today(),
        due_date=date.today(),
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

def test_payment_methods_and_validation():
    # Valid methods
    for method in ["UPI", "CARD", "BANK_TRANSFER", "CASH", "OTHER"]:
        pay = record_payment(
            customer_id="cust-001",
            method=method,
            amount=Decimal("500.00"),
            reference=f"REF-{method}"
        )
        assert pay.status == "RECORDED"
        assert pay.method == method
        assert pay.amount == Decimal("500.00")
        assert pay.unallocated_amount == Decimal("500.00")

    # Invalid method rejected
    with pytest.raises(AppException) as exc:
        record_payment(customer_id="cust-001", method="BITCOIN", amount=Decimal("100.00"))
    assert exc.value.status_code == 400

    # Negative / zero amount rejected
    with pytest.raises(AppException) as exc:
        record_payment(customer_id="cust-001", method="UPI", amount=Decimal("-50.00"))
    assert exc.value.status_code == 400

def test_split_payment_one_payment_multiple_invoices():
    inv1 = seed_invoice(customer_id="cust-split", total=Decimal("1000.00"))
    inv2 = seed_invoice(customer_id="cust-split", total=Decimal("500.00"))

    # Pay 1200: 1000 to inv1 (becomes PAID), 200 to inv2 (becomes PARTIALLY_PAID)
    pay = record_payment(
        customer_id="cust-split",
        method="BANK_TRANSFER",
        amount=Decimal("1200.00"),
        reference="TXN-SPLIT-001",
        allocations=[
            {"invoice_id": inv1.id, "amount": Decimal("1000.00")},
            {"invoice_id": inv2.id, "amount": Decimal("200.00")}
        ]
    )

    assert pay.unallocated_amount == Decimal("0.00")
    assert len(pay.allocations) == 2

    db = SessionLocal()
    updated_inv1 = db.query(Invoice).filter_by(id=inv1.id).first()
    updated_inv2 = db.query(Invoice).filter_by(id=inv2.id).first()

    assert updated_inv1.status == "PAID"
    assert updated_inv1.amount_paid == Decimal("1000.00")
    assert updated_inv1.balance == Decimal("0.00")

    assert updated_inv2.status == "PARTIALLY_PAID"
    assert updated_inv2.amount_paid == Decimal("200.00")
    assert updated_inv2.balance == Decimal("300.00")
    db.close()

def test_multiple_payments_one_invoice():
    inv = seed_invoice(customer_id="cust-multi", total=Decimal("1000.00"))

    # Payment 1 of 400
    p1 = record_payment(
        customer_id="cust-multi",
        method="UPI",
        amount=Decimal("400.00"),
        allocations=[{"invoice_id": inv.id, "amount": Decimal("400.00")}]
    )

    db = SessionLocal()
    check1 = db.query(Invoice).filter_by(id=inv.id).first()
    assert check1.status == "PARTIALLY_PAID"
    assert check1.amount_paid == Decimal("400.00")
    assert check1.balance == Decimal("600.00")
    db.close()

    # Payment 2 of 600 finishes the invoice
    p2 = record_payment(
        customer_id="cust-multi",
        method="CARD",
        amount=Decimal("600.00"),
        allocations=[{"invoice_id": inv.id, "amount": Decimal("600.00")}]
    )

    db = SessionLocal()
    check2 = db.query(Invoice).filter_by(id=inv.id).first()
    assert check2.status == "PAID"
    assert check2.amount_paid == Decimal("1000.00")
    assert check2.balance == Decimal("0.00")
    db.close()

def test_over_allocation_rejected():
    inv = seed_invoice(customer_id="cust-over", total=Decimal("500.00"))

    # Attempt to allocate 600 to 500 invoice
    with pytest.raises(AppException) as exc:
        record_payment(
            customer_id="cust-over",
            method="UPI",
            amount=Decimal("1000.00"),
            allocations=[{"invoice_id": inv.id, "amount": Decimal("600.00")}]
        )
    assert exc.value.status_code == 400
    assert "exceeds" in str(exc.value.detail).lower()

def test_unallocated_payment_and_subsequent_allocation():
    inv = seed_invoice(customer_id="cust-post-alloc", total=Decimal("800.00"))

    # Record unallocated advance payment of 1000
    pay = record_payment(
        customer_id="cust-post-alloc",
        method="BANK_TRANSFER",
        amount=Decimal("1000.00")
    )
    assert pay.unallocated_amount == Decimal("1000.00")
    assert len(pay.allocations) == 0

    # Allocate 800 later
    updated_pay = allocate_payment(
        payment_id=pay.id,
        allocations=[{"invoice_id": inv.id, "amount": Decimal("800.00")}]
    )
    assert updated_pay.unallocated_amount == Decimal("200.00")

    db = SessionLocal()
    checked_inv = db.query(Invoice).filter_by(id=inv.id).first()
    assert checked_inv.status == "PAID"
    assert checked_inv.balance == Decimal("0.00")
    db.close()

def test_refund_reverses_allocation_and_restores_balance():
    inv = seed_invoice(customer_id="cust-ref", total=Decimal("500.00"))

    # Pay 500 (invoice becomes PAID)
    pay = record_payment(
        customer_id="cust-ref",
        method="CARD",
        amount=Decimal("500.00"),
        allocations=[{"invoice_id": inv.id, "amount": Decimal("500.00")}]
    )

    db = SessionLocal()
    assert db.query(Invoice).filter_by(id=inv.id).first().status == "PAID"
    db.close()

    # Refund 500
    refund = record_refund(payment_id=pay.id, amount=Decimal("500.00"), reason="Service cancelled")
    assert refund.amount == Decimal("500.00")

    db = SessionLocal()
    refreshed_pay = db.query(Payment).filter_by(id=pay.id).first()
    assert refreshed_pay.status == "REFUNDED"

    refreshed_inv = db.query(Invoice).filter_by(id=inv.id).first()
    assert refreshed_inv.status == "CONFIRMED"
    assert refreshed_inv.amount_paid == Decimal("0.00")
    assert refreshed_inv.balance == Decimal("500.00")
    db.close()

def test_gateway_order_and_webhook_with_hmac():
    # 1. Create order
    order = create_gateway_order(amount=Decimal("1500.00"), currency="INR")
    assert order["order_id"].startswith("order_mock_")
    assert order["amount"] == "1500.00"

    # 2. Webhook HMAC verification
    secret = getattr(settings, "PAYMENT_GATEWAY_WEBHOOK_SECRET", None) or getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret_p2")
    payload = {
        "id": "evt_gateway_001",
        "event": "payment.succeeded",
        "payload": {
            "customer_id": "cust-001",
            "amount": "1500.00",
            "method": "UPI",
            "reference": "UPI-GATEWAY-123"
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    assert verify_gateway_signature(raw_body, valid_sig, secret=secret) is True
    assert verify_gateway_signature(raw_body, "invalid_sig", secret=secret) is False

    # Process webhook first time
    res1 = process_gateway_webhook(event_data=payload, raw_body=raw_body, signature=valid_sig)
    assert res1["status"] == "SUCCESS"

    # Idempotency: Process same event_id second time
    res2 = process_gateway_webhook(event_data=payload, raw_body=raw_body, signature=valid_sig)
    assert res2["status"] == "SUCCESS"

    # Verify only 1 payment was created in DB for this event_id
    db = SessionLocal()
    matched = db.query(Payment).filter_by(gateway_event_id="evt_gateway_001").all()
    assert len(matched) == 1
    db.close()

def test_payment_port_and_outstanding():
    port = get_port("payment")
    cust_id = "cust-port-001"

    inv1 = seed_invoice(customer_id=cust_id, total=Decimal("2000.00"))
    inv2 = seed_invoice(customer_id=cust_id, total=Decimal("1000.00"))

    # Initial outstanding = 3000
    assert port.outstanding_for_customer(cust_id) == Decimal("3000.00")

    # Pay 1500: 1000 allocated to inv2, 500 unallocated
    record_payment(
        customer_id=cust_id,
        method="BANK_TRANSFER",
        amount=Decimal("1500.00"),
        allocations=[{"invoice_id": inv2.id, "amount": Decimal("1000.00")}]
    )

    # Remaining balances: inv1 has 2000, inv2 has 0. Unallocated credit is 500.
    # Net outstanding = 2000 - 500 = 1500
    assert port.outstanding_for_customer(cust_id) == Decimal("1500.00")

    payments = port.list_for_customer(cust_id)
    assert len(payments) == 1
    assert payments[0].amount == Decimal("1500.00")

def test_api_endpoints_via_client():
    inv = seed_invoice(customer_id="cust-api-001", total=Decimal("700.00"))

    # POST /api/v1/payments
    resp = client.post("/api/v1/payments", json={
        "customer_id": "cust-api-001",
        "method": "UPI",
        "amount": "700.00",
        "reference": "UPI-700",
        "allocations": [{"invoice_id": inv.id, "amount": "700.00"}]
    })
    assert resp.status_code == 201
    p_id = resp.json()["id"]

    # GET /api/v1/payments/{id}
    resp_get = client.get(f"/api/v1/payments/{p_id}")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["amount"] == "700.00"
    assert len(data["allocations"]) == 1

    # GET /api/v1/payments/customer/{cust_id}/outstanding
    resp_out = client.get("/api/v1/payments/customer/cust-api-001/outstanding")
    assert resp_out.status_code == 200
    assert resp_out.json()["outstanding_balance"] == "0.00"
