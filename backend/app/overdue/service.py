from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.errors import AppException, NotFoundException
from backend.app.core.money import to_decimal, round_money
from backend.app.shared.events import DomainEvent, publish
from backend.app.shared.registry import get_port
from backend.app.invoices.models import Invoice
from backend.app.overdue.models import PaymentFollowup

def get_tier_for_days_overdue(days: int) -> int:
    if days <= 7:
        return 1
    elif days <= 14:
        return 2
    else:
        return 3

def get_overdue_invoices(
    as_of: Optional[date] = None,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        target_date = as_of or date.today()
        cust_port = get_port("customer")

        invoices = db.query(Invoice).filter(
            Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
            Invoice.balance > Decimal("0.00"),
            Invoice.due_date < target_date
        ).order_by(Invoice.due_date.asc()).all()

        results = []
        for inv in invoices:
            days = (target_date - inv.due_date).days
            tier = get_tier_for_days_overdue(days)
            cust = cust_port.get(inv.customer_id)

            results.append({
                "invoice_id": inv.id,
                "invoice_number": inv.number,
                "customer_id": inv.customer_id,
                "customer_name": cust.name if cust else "Valued Customer",
                "customer_email": cust.email if cust else None,
                "due_date": inv.due_date.isoformat(),
                "days_overdue": days,
                "tier": tier,
                "total": str(inv.total),
                "amount_paid": str(inv.amount_paid),
                "balance": str(inv.balance),
                "status": inv.status
            })
        return results
    finally:
        if owns_session:
            db.close()

def get_overdue_summary(
    as_of: Optional[date] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    overdue_items = get_overdue_invoices(as_of=as_of, db=db)

    total_amount = Decimal("0.00")
    tier_counts = {1: 0, 2: 0, 3: 0}
    tier_amounts = {1: Decimal("0.00"), 2: Decimal("0.00"), 3: Decimal("0.00")}

    for item in overdue_items:
        bal = to_decimal(item["balance"])
        t = item["tier"]
        total_amount = round_money(total_amount + bal)
        tier_counts[t] += 1
        tier_amounts[t] = round_money(tier_amounts[t] + bal)

    return {
        "as_of": (as_of or date.today()).isoformat(),
        "total_overdue_count": len(overdue_items),
        "total_overdue_amount": str(total_amount),
        "tiers": {
            "tier_1": {"count": tier_counts[1], "amount": str(tier_amounts[1])},
            "tier_2": {"count": tier_counts[2], "amount": str(tier_amounts[2])},
            "tier_3": {"count": tier_counts[3], "amount": str(tier_amounts[3])}
        }
    }

def evaluate_and_send_reminders(
    as_of: Optional[date] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        target_date = as_of or date.today()
        cust_port = get_port("customer")
        notif_port = get_port("notification")

        invoices = db.query(Invoice).filter(
            Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
            Invoice.balance > Decimal("0.00"),
            Invoice.due_date < target_date
        ).all()

        sent_count = 0
        skipped_count = 0

        for inv in invoices:
            days = (target_date - inv.due_date).days
            tier = get_tier_for_days_overdue(days)

            # Check if reminder already sent for this invoice and tier
            existing = db.query(PaymentFollowup).filter(
                PaymentFollowup.invoice_id == inv.id,
                PaymentFollowup.tier == tier
            ).first()

            if existing:
                skipped_count += 1
                continue

            cust = cust_port.get(inv.customer_id)
            cust_name = cust.name if cust else "Customer"
            cust_email = cust.email if cust else "billing@customer.com"

            # Dispatch notification
            template_name = f"overdue_reminder_{tier}"
            notif_port.send(
                template=template_name,
                to=cust_email,
                context={
                    "customer_name": cust_name,
                    "invoice_number": inv.number,
                    "amount_due": str(inv.balance),
                    "due_date": str(inv.due_date),
                    "days_overdue": days,
                    "tier": tier
                },
                customer_id=inv.customer_id,
                db_session=db
            )

            # Record automated followup
            followup = PaymentFollowup(
                invoice_id=inv.id,
                customer_id=inv.customer_id,
                tier=tier,
                channel="EMAIL",
                notes=f"Automated Tier {tier} reminder sent ({days} days overdue)",
                status="PENDING"
            )
            db.add(followup)
            sent_count += 1

            publish(DomainEvent(
                event_name="overdue.reminder_sent",
                payload={
                    "invoice_id": inv.id,
                    "customer_id": inv.customer_id,
                    "tier": tier,
                    "days_overdue": days,
                    "balance": str(inv.balance)
                }
            ))

        if owns_session:
            db.commit()

        return {
            "as_of": target_date.isoformat(),
            "invoices_evaluated": len(invoices),
            "reminders_sent": sent_count,
            "reminders_skipped": skipped_count
        }
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()

def record_manual_followup(
    invoice_id: str,
    notes: str,
    promised_payment_date: Optional[date] = None,
    channel: str = "PHONE",
    status: str = "PROMISED",
    db: Optional[Session] = None
) -> PaymentFollowup:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        inv = db.query(Invoice).filter_by(id=invoice_id).first()
        if not inv:
            raise NotFoundException(f"Invoice {invoice_id} not found")

        followup = PaymentFollowup(
            invoice_id=inv.id,
            customer_id=inv.customer_id,
            tier=None,
            channel=(channel or "PHONE").upper(),
            notes=notes,
            promised_payment_date=promised_payment_date,
            status=status.upper() if status else "PENDING"
        )
        db.add(followup)

        if owns_session:
            db.commit()
            db.refresh(followup)

        return followup
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()
