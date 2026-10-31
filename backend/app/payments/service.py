from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.errors import AppException, NotFoundException
from backend.app.core.money import to_decimal, round_money
from backend.app.shared.events import DomainEvent, publish
from backend.app.shared.registry import get_port
from backend.app.payments.models import Payment, PaymentAllocation, PaymentRefund
from backend.app.invoices.models import Invoice

VALID_METHODS = {"UPI", "CARD", "BANK_TRANSFER", "CASH", "OTHER"}

def get_locked_invoice(db: Session, invoice_id: str) -> Optional[Invoice]:
    query = db.query(Invoice).filter(Invoice.id == invoice_id)
    if "postgresql" in str(db.bind.url if db.bind else ""):
        query = query.with_for_update()
    return query.first()

def record_payment(
    customer_id: str,
    method: str,
    amount: Decimal,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    allocations: Optional[List[Dict[str, Any]]] = None,
    gateway_event_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Payment:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        method_upper = (method or "").upper()
        if method_upper not in VALID_METHODS:
            raise AppException(f"Invalid payment method: {method}. Allowed: {sorted(list(VALID_METHODS))}", 400)

        pay_amount = round_money(to_decimal(amount))
        if pay_amount <= Decimal("0.00"):
            raise AppException("Payment amount must be greater than zero", 400)

        # Webhook idempotency
        if gateway_event_id:
            existing = db.query(Payment).filter_by(gateway_event_id=gateway_event_id).first()
            if existing:
                return existing

        total_alloc = Decimal("0.00")
        validated_allocations = []

        if allocations:
            for item in allocations:
                inv_id = item.get("invoice_id")
                alloc_amt = round_money(to_decimal(item.get("amount", Decimal("0.00"))))
                if alloc_amt <= Decimal("0.00"):
                    continue

                inv = get_locked_invoice(db, inv_id)
                if not inv:
                    raise NotFoundException(f"Invoice {inv_id} not found")
                if inv.customer_id != customer_id:
                    raise AppException(f"Invoice {inv_id} does not belong to customer {customer_id}", 400)
                if inv.status not in ("CONFIRMED", "PARTIALLY_PAID"):
                    raise AppException(f"Invoice {inv.number} with status {inv.status} cannot receive payment", 400)
                if alloc_amt > inv.balance:
                    raise AppException(
                        f"Allocation amount {alloc_amt} exceeds remaining balance {inv.balance} on invoice {inv.number}",
                        400
                    )

                total_alloc = round_money(total_alloc + alloc_amt)
                if total_alloc > pay_amount:
                    raise AppException("Total allocated amount exceeds payment amount", 400)

                validated_allocations.append((inv, alloc_amt))

        unallocated = round_money(pay_amount - total_alloc)

        payment = Payment(
            customer_id=customer_id,
            method=method_upper,
            amount=pay_amount,
            unallocated_amount=unallocated,
            reference=reference,
            notes=notes,
            status="RECORDED",
            gateway_event_id=gateway_event_id
        )
        db.add(payment)
        db.flush()

        for inv, alloc_amt in validated_allocations:
            db.add(PaymentAllocation(
                payment_id=payment.id,
                invoice_id=inv.id,
                amount=alloc_amt
            ))
            inv.amount_paid = round_money(inv.amount_paid + alloc_amt)
            inv.balance = round_money(inv.total - inv.amount_paid)
            if inv.balance == Decimal("0.00"):
                inv.status = "PAID"
            else:
                inv.status = "PARTIALLY_PAID"

        if owns_session:
            db.commit()
            db.refresh(payment)

        # Notify customer
        cust_port = get_port("customer")
        cust = cust_port.get(customer_id)
        if cust and cust.email:
            notif_port = get_port("notification")
            notif_port.send(
                template="payment_received",
                to=cust.email,
                context={
                    "customer_name": cust.name,
                    "payment_id": payment.id,
                    "amount": str(payment.amount),
                    "method": payment.method,
                    "reference": payment.reference or ""
                },
                customer_id=customer_id,
                db_session=db
            )

        publish(DomainEvent(
            event_name="payment.received",
            payload={
                "payment_id": payment.id,
                "customer_id": customer_id,
                "amount": str(payment.amount),
                "unallocated": str(payment.unallocated_amount)
            }
        ))

        return payment
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()

def allocate_payment(
    payment_id: str,
    allocations: List[Dict[str, Any]],
    db: Optional[Session] = None
) -> Payment:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundException(f"Payment {payment_id} not found")
        if payment.status != "RECORDED":
            raise AppException(f"Cannot allocate payment with status {payment.status}", 400)

        total_alloc = Decimal("0.00")
        validated_allocations = []

        for item in allocations:
            inv_id = item.get("invoice_id")
            alloc_amt = round_money(to_decimal(item.get("amount", Decimal("0.00"))))
            if alloc_amt <= Decimal("0.00"):
                continue

            inv = get_locked_invoice(db, inv_id)
            if not inv:
                raise NotFoundException(f"Invoice {inv_id} not found")
            if inv.customer_id != payment.customer_id:
                raise AppException(f"Invoice {inv_id} does not belong to customer {payment.customer_id}", 400)
            if inv.status not in ("CONFIRMED", "PARTIALLY_PAID"):
                raise AppException(f"Invoice {inv.number} with status {inv.status} cannot receive payment", 400)
            if alloc_amt > inv.balance:
                raise AppException(
                    f"Allocation amount {alloc_amt} exceeds balance {inv.balance} on invoice {inv.number}",
                    400
                )

            total_alloc = round_money(total_alloc + alloc_amt)
            if total_alloc > payment.unallocated_amount:
                raise AppException("Total allocated exceeds unallocated payment amount", 400)

            validated_allocations.append((inv, alloc_amt))

        for inv, alloc_amt in validated_allocations:
            db.add(PaymentAllocation(
                payment_id=payment.id,
                invoice_id=inv.id,
                amount=alloc_amt
            ))
            inv.amount_paid = round_money(inv.amount_paid + alloc_amt)
            inv.balance = round_money(inv.total - inv.amount_paid)
            if inv.balance == Decimal("0.00"):
                inv.status = "PAID"
            else:
                inv.status = "PARTIALLY_PAID"

        payment.unallocated_amount = round_money(payment.unallocated_amount - total_alloc)

        if owns_session:
            db.commit()
            db.refresh(payment)

        publish(DomainEvent(
            event_name="payment.allocated",
            payload={"payment_id": payment.id, "allocated_now": str(total_alloc), "unallocated": str(payment.unallocated_amount)}
        ))

        return payment
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()

def record_refund(
    payment_id: str,
    amount: Decimal,
    reason: Optional[str] = None,
    db: Optional[Session] = None
) -> PaymentRefund:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundException(f"Payment {payment_id} not found")
        if payment.status == "FAILED":
            raise AppException("Cannot refund a failed payment", 400)

        ref_amt = round_money(to_decimal(amount))
        if ref_amt <= Decimal("0.00"):
            raise AppException("Refund amount must be greater than zero", 400)

        total_existing_refunds = sum(r.amount for r in payment.refunds)
        available_to_refund = round_money(payment.amount - total_existing_refunds)
        if ref_amt > available_to_refund:
            raise AppException(f"Refund amount {ref_amt} exceeds refundable balance {available_to_refund}", 400)

        # 1. First consume unallocated amount if available
        if ref_amt <= payment.unallocated_amount:
            payment.unallocated_amount = round_money(payment.unallocated_amount - ref_amt)
        else:
            # Reversing allocations
            to_reverse = round_money(ref_amt - payment.unallocated_amount)
            payment.unallocated_amount = Decimal("0.00")

            # Reverse from allocations in LIFO order
            for alloc in list(reversed(payment.allocations)):
                rev = min(alloc.amount, to_reverse)
                alloc.amount = round_money(alloc.amount - rev)
                to_reverse = round_money(to_reverse - rev)

                inv = get_locked_invoice(db, alloc.invoice_id)
                if inv:
                    inv.amount_paid = round_money(inv.amount_paid - rev)
                    inv.balance = round_money(inv.total - inv.amount_paid)
                    if inv.amount_paid == Decimal("0.00"):
                        inv.status = "CONFIRMED"
                    else:
                        inv.status = "PARTIALLY_PAID"

                if alloc.amount == Decimal("0.00"):
                    db.delete(alloc)

                if to_reverse == Decimal("0.00"):
                    break

        refund = PaymentRefund(
            payment_id=payment.id,
            amount=ref_amt,
            reason=reason or "Customer requested refund"
        )
        db.add(refund)

        # If fully refunded, mark status
        if round_money(total_existing_refunds + ref_amt) == payment.amount:
            payment.status = "REFUNDED"

        if owns_session:
            db.commit()
            db.refresh(refund)

        publish(DomainEvent(
            event_name="payment.refunded",
            payload={"payment_id": payment.id, "refund_amount": str(ref_amt), "status": payment.status}
        ))

        return refund
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()

def record_failed_payment(
    customer_id: str,
    method: str,
    amount: Decimal,
    error_reason: str,
    gateway_event_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Payment:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        pay_amount = round_money(to_decimal(amount))
        payment = Payment(
            customer_id=customer_id,
            method=(method or "OTHER").upper(),
            amount=pay_amount,
            unallocated_amount=Decimal("0.00"),
            status="FAILED",
            notes=error_reason,
            gateway_event_id=gateway_event_id
        )
        db.add(payment)

        if owns_session:
            db.commit()
            db.refresh(payment)

        cust_port = get_port("customer")
        cust = cust_port.get(customer_id)
        if cust and cust.email:
            notif_port = get_port("notification")
            notif_port.send(
                template="payment_failed",
                to=cust.email,
                context={
                    "customer_name": cust.name,
                    "amount": str(pay_amount),
                    "reason": error_reason
                },
                customer_id=customer_id,
                db_session=db
            )

        publish(DomainEvent(
            event_name="payment.failed",
            payload={"payment_id": payment.id, "customer_id": customer_id, "amount": str(pay_amount), "reason": error_reason}
        ))

        return payment
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()
