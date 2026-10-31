from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import SessionLocal
from app.core.money import to_decimal, round_money
from app.invoices.models import Invoice
from app.payments.models import Payment, PaymentAllocation, PaymentRefund
from app.payments.service import allocate_payment

def generate_reconciliation_report(db: Optional[Session] = None) -> Dict[str, Any]:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        discrepancies = []

        # 1. Audit Payments
        payments = db.query(Payment).all()
        total_payment_amount = Decimal("0.00")
        total_unallocated_amount = Decimal("0.00")

        for p in payments:
            amt = to_decimal(p.amount)
            unalloc = to_decimal(p.unallocated_amount)
            total_payment_amount = round_money(total_payment_amount + amt)
            total_unallocated_amount = round_money(total_unallocated_amount + unalloc)

            if p.status == "RECORDED":
                sum_allocs = sum((to_decimal(a.amount) for a in p.allocations), Decimal("0.00"))
                sum_refunds = sum((to_decimal(r.amount) for r in p.refunds), Decimal("0.00"))
                expected = round_money(sum_allocs + unalloc + sum_refunds)

                if amt != expected:
                    discrepancies.append({
                        "type": "PAYMENT_MISMATCH",
                        "entity_id": p.id,
                        "description": f"Payment {p.id} amount {amt} does not equal allocations ({sum_allocs}) + unallocated ({unalloc}) + refunds ({sum_refunds})"
                    })

        # 2. Audit Invoices
        invoices = db.query(Invoice).all()
        total_invoice_balance = Decimal("0.00")
        total_invoice_paid = Decimal("0.00")

        for inv in invoices:
            tot = to_decimal(inv.total)
            paid = to_decimal(inv.amount_paid)
            bal = to_decimal(inv.balance)

            total_invoice_balance = round_money(total_invoice_balance + bal)
            total_invoice_paid = round_money(total_invoice_paid + paid)

            allocs_for_inv = db.query(PaymentAllocation).filter_by(invoice_id=inv.id).all()
            sum_allocs = sum((to_decimal(a.amount) for a in allocs_for_inv), Decimal("0.00"))

            if paid != sum_allocs:
                discrepancies.append({
                    "type": "INVOICE_PAID_MISMATCH",
                    "entity_id": inv.id,
                    "description": f"Invoice {inv.number} amount_paid ({paid}) does not match sum of allocations ({sum_allocs})"
                })

            expected_bal = round_money(tot - paid)
            if bal != expected_bal:
                discrepancies.append({
                    "type": "INVOICE_BALANCE_MISMATCH",
                    "entity_id": inv.id,
                    "description": f"Invoice {inv.number} balance ({bal}) does not equal total - paid ({expected_bal})"
                })

            # Check status integrity
            if bal == Decimal("0.00") and inv.status not in ("PAID", "CANCELLED", "DRAFT"):
                discrepancies.append({
                    "type": "INVOICE_STATUS_MISMATCH",
                    "entity_id": inv.id,
                    "description": f"Invoice {inv.number} has zero balance but status is {inv.status}"
                })
            elif Decimal("0.00") < bal < tot and inv.status != "PARTIALLY_PAID":
                discrepancies.append({
                    "type": "INVOICE_STATUS_MISMATCH",
                    "entity_id": inv.id,
                    "description": f"Invoice {inv.number} has partial balance ({bal}) but status is {inv.status}"
                })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_healthy": len(discrepancies) == 0,
            "discrepancies_count": len(discrepancies),
            "total_payments_checked": len(payments),
            "total_invoices_checked": len(invoices),
            "metrics": {
                "total_payment_volume": str(total_payment_amount),
                "total_unallocated_volume": str(total_unallocated_amount),
                "total_invoice_balance": str(total_invoice_balance),
                "total_invoice_paid": str(total_invoice_paid)
            },
            "discrepancies": discrepancies
        }
    finally:
        if owns_session:
            db.close()

def auto_allocate_unallocated_credits(
    customer_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Finds customers with unallocated payment credits and open invoices,
    and auto-allocates credit FIFO against oldest due invoices.
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        query_pays = db.query(Payment).filter(
            Payment.status == "RECORDED",
            Payment.unallocated_amount > Decimal("0.00")
        )
        if customer_id:
            query_pays = query_pays.filter(Payment.customer_id == customer_id)

        payments_with_credit = query_pays.order_by(Payment.payment_date.asc()).all()

        allocations_made = 0
        total_allocated = Decimal("0.00")

        for p in payments_with_credit:
            if p.unallocated_amount <= Decimal("0.00"):
                continue

            open_invoices = db.query(Invoice).filter(
                Invoice.customer_id == p.customer_id,
                Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
                Invoice.balance > Decimal("0.00")
            ).order_by(Invoice.due_date.asc(), Invoice.created_at.asc()).all()

            for inv in open_invoices:
                if p.unallocated_amount <= Decimal("0.00"):
                    break

                alloc_amt = min(to_decimal(p.unallocated_amount), to_decimal(inv.balance))
                if alloc_amt <= Decimal("0.00"):
                    continue

                allocate_payment(
                    payment_id=p.id,
                    allocations=[{"invoice_id": inv.id, "amount": alloc_amt}],
                    db=db
                )
                allocations_made += 1
                total_allocated = round_money(total_allocated + alloc_amt)

        if owns_session:
            db.commit()

        return {
            "status": "COMPLETED",
            "allocations_made": allocations_made,
            "total_allocated": str(total_allocated)
        }
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()
