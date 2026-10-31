import hmac
import hashlib
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppException
from app.core.money import to_decimal, round_money
from app.payments.models import Payment
from app.payments.service import record_payment, record_failed_payment, record_refund

def create_gateway_order(
    amount: Decimal,
    currency: str = "INR",
    invoice_id: Optional[str] = None,
    customer_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generates mock test-mode order payload for checkout frontend."""
    dec_amount = round_money(to_decimal(amount))
    order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
    key = getattr(settings, "PAYMENT_GATEWAY_KEY", None) or getattr(settings, "RAZORPAY_KEY_ID", "mock_key_test_123")
    return {
        "order_id": order_id,
        "amount": str(dec_amount),
        "amount_subunits": int(dec_amount * 100),
        "currency": currency or "INR",
        "key_id": key,
        "invoice_id": invoice_id,
        "customer_id": customer_id
    }

def verify_gateway_signature(
    payload_bytes: bytes,
    signature: str,
    secret: Optional[str] = None
) -> bool:
    """Verifies HMAC SHA-256 signature on raw webhook request body."""
    sec = secret or getattr(settings, "PAYMENT_GATEWAY_WEBHOOK_SECRET", None) or getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret_p2")
    expected = hmac.new(sec.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def process_gateway_webhook(
    event_data: Dict[str, Any],
    raw_body: Optional[bytes] = None,
    signature: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Idempotent gateway webhook processor.
    Validates HMAC signature when provided, prevents duplicate execution via gateway_event_id.
    """
    if signature and raw_body:
        if not verify_gateway_signature(raw_body, signature):
            raise AppException("Invalid webhook signature", 401)

    event_id = event_data.get("id") or event_data.get("event_id")
    if not event_id:
        raise AppException("Missing gateway event_id in webhook payload", 400)

    event_type = event_data.get("event") or event_data.get("event_type")
    payload = event_data.get("payload", {})

    # 1. Payment Success
    if event_type in ("payment.succeeded", "payment.captured"):
        cust_id = payload.get("customer_id")
        amt = to_decimal(payload.get("amount", "0.00"))
        method = payload.get("method", "CARD")
        reference = payload.get("reference") or payload.get("payment_id")
        allocs = payload.get("allocations")

        if not allocs and payload.get("invoice_id"):
            allocs = [{"invoice_id": payload["invoice_id"], "amount": amt}]

        payment = record_payment(
            customer_id=cust_id,
            method=method,
            amount=amt,
            reference=reference,
            notes=f"Gateway event {event_id}",
            allocations=allocs,
            gateway_event_id=event_id,
            db=db
        )
        return {"status": "SUCCESS", "event_id": event_id, "payment_id": payment.id}

    # 2. Payment Failed
    elif event_type == "payment.failed":
        cust_id = payload.get("customer_id")
        amt = to_decimal(payload.get("amount", "0.00"))
        method = payload.get("method", "CARD")
        reason = payload.get("reason", "Payment failed at gateway")

        payment = record_failed_payment(
            customer_id=cust_id,
            method=method,
            amount=amt,
            error_reason=reason,
            gateway_event_id=event_id,
            db=db
        )
        return {"status": "SUCCESS", "event_id": event_id, "payment_id": payment.id}

    # 3. Refund Processed
    elif event_type == "refund.processed":
        payment_id = payload.get("payment_id")
        amt = to_decimal(payload.get("amount", "0.00"))
        reason = payload.get("reason", "Gateway refund")

        refund = record_refund(
            payment_id=payment_id,
            amount=amt,
            reason=reason,
            db=db
        )
        return {"status": "SUCCESS", "event_id": event_id, "refund_id": refund.id}

    return {"status": "IGNORED", "event_id": event_id, "event_type": event_type}
