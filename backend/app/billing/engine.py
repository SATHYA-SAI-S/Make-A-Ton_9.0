import zlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine
from backend.app.core.money import to_decimal, round_money
from backend.app.shared.dto import SubscriptionDTO, CustomerDTO, TaxLineInputDTO
from backend.app.shared.events import DomainEvent, publish
from backend.app.shared.registry import get_port
from backend.app.billing.models import BillingPeriod, BillingRun, BillingRunItem
from backend.app.billing.calculator import calculate_pricing
from backend.app.invoices.models import Invoice, InvoiceLine
from backend.app.invoices.service import generate_invoice_number, create_invoice_snapshot
from backend.app.taxes.service import compute_tax
from backend.app.discounts.service import eligible_discounts, record_redemption

def get_period_delta(frequency: str) -> relativedelta:
    freq = (frequency or "MONTHLY").upper()
    if freq == "DAILY":
        return relativedelta(days=1)
    elif freq == "WEEKLY":
        return relativedelta(weeks=1)
    elif freq == "YEARLY":
        return relativedelta(years=1)
    else:
        return relativedelta(months=1)

def compute_unbilled_periods(
    start_date: date,
    frequency: str,
    as_of: date,
    existing_periods: List[Tuple[date, date]]
) -> List[Tuple[date, date]]:
    """Calculates all sequential unbilled periods up to as_of date."""
    delta = get_period_delta(frequency)
    periods = []
    curr_start = start_date

    existing_set = set(existing_periods)

    while curr_start <= as_of:
        curr_end = curr_start + delta - timedelta(days=1)
        if (curr_start, curr_end) not in existing_set:
            periods.append((curr_start, curr_end))
        curr_start = curr_end + timedelta(days=1)

    return periods

def try_advisory_lock(db: Session, key_str: str) -> bool:
    """PostgreSQL advisory lock using 32-bit CRC32 int key. On SQLite always succeeds."""
    if "postgresql" in str(db.bind.url):
        lock_id = zlib.crc32(key_str.encode("utf-8")) & 0x7FFFFFFF
        res = db.execute(text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": lock_id}).scalar()
        return bool(res)
    return True

def bill_single_subscription(
    subscription: SubscriptionDTO,
    as_of: date,
    db: Session,
    customer: CustomerDTO,
    auto_confirm: bool = False,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Bills a single subscription for all unbilled periods up to as_of.
    Idempotent and isolated inside a subtransaction / savepoint.
    """
    sub_id = subscription.id

    # Advisory lock on subscription
    if not try_advisory_lock(db, f"sub_lock_{sub_id}"):
        return [{"status": "SKIPPED", "period": None, "reason": "Locked by concurrent process"}]

    # Load existing billed periods for subscription
    existing = db.query(BillingPeriod.period_start, BillingPeriod.period_end)\
                 .filter(BillingPeriod.subscription_id == sub_id).all()
    existing_tuples = [(r[0], r[1]) for r in existing]

    start_date = subscription.next_billing_date or subscription.start_date
    unbilled = compute_unbilled_periods(start_date, subscription.billing_frequency, as_of, existing_tuples)

    if not unbilled:
        return []

    results = []

    for p_start, p_end in unbilled:
        # Check idempotency guard in DB
        already_billed = db.query(BillingPeriod).filter(
            BillingPeriod.subscription_id == sub_id,
            BillingPeriod.period_start == p_start,
            BillingPeriod.period_end == p_end
        ).first()

        if already_billed:
            results.append({"status": "SKIPPED", "period": (p_start, p_end), "reason": "Already billed"})
            continue

        if dry_run:
            results.append({"status": "DRY_RUN", "period": (p_start, p_end), "invoice_number": "DRY_RUN_INV"})
            continue

        # Prepare line calculation
        lines_input = []
        tax_lines_input = []
        for l in subscription.lines:
            line_dict = {
                "product_id": l.product_id,
                "variant_id": l.variant_id,
                "description": f"Subscription line for product {l.product_id}",
                "quantity": l.quantity,
                "unit_price": l.unit_price
            }
            lines_input.append(line_dict)
            tax_lines_input.append(TaxLineInputDTO(
                product_id=l.product_id,
                variant_id=l.variant_id,
                quantity=l.quantity,
                unit_price=l.unit_price
            ))

        # 1. Discounts
        discounts = eligible_discounts(tax_lines_input, as_of=p_start, db=db, lock_rules=True)
        prod_discounts = {}
        sub_discount = Decimal("0.00")
        applied_rule_ids = []

        for d in discounts:
            applied_rule_ids.append((d.rule_id, d.amount))
            if d.scope == "PRODUCT":
                pass
            else:
                sub_discount += d.amount

        # 2. Tax computation
        tax_breakdowns = compute_tax(tax_lines_input, customer, as_of=p_start, db=db)
        total_tax_rate = sum(tb.rate for tb in tax_breakdowns)

        # 3. Pricing Calculator
        calc_result = calculate_pricing(
            lines_input=lines_input,
            product_discounts=prod_discounts,
            subscription_discount=sub_discount,
            tax_rate=total_tax_rate,
            tax_breakdowns=tax_breakdowns
        )

        # 4. Insert Billing Period with Unique constraint guard
        bp = BillingPeriod(
            subscription_id=sub_id,
            period_start=p_start,
            period_end=p_end,
            status="BILLED"
        )
        db.add(bp)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            results.append({"status": "SKIPPED", "period": (p_start, p_end), "reason": "Period duplicate conflict"})
            continue

        # 5. Create Invoice & Snapshot
        inv_number = generate_invoice_number(db)
        inv_status = "CONFIRMED" if auto_confirm else "DRAFT"
        due_date = p_start + timedelta(days=subscription.payment_terms_days or 15)

        snapshot_data = create_invoice_snapshot(
            customer=customer,
            plan_name=subscription.plan_id,
            lines_data=lines_input,
            tax_rules_used=[tb.rule_name for tb in tax_breakdowns]
        )

        invoice = Invoice(
            number=inv_number,
            customer_id=customer.id,
            subscription_id=sub_id,
            billing_period_id=bp.id,
            status=inv_status,
            invoice_date=p_start,
            due_date=due_date,
            subtotal=calc_result.subtotal,
            discount_total=calc_result.discount_total,
            tax_total=calc_result.tax_total,
            total=calc_result.total,
            amount_paid=Decimal("0.00"),
            balance=calc_result.total,
            currency=subscription.currency or "INR",
            snapshot=snapshot_data
        )
        db.add(invoice)
        db.flush()

        # Link billing period
        bp.invoice_id = invoice.id

        # Insert Invoice lines
        for cl in calc_result.lines:
            db.add(InvoiceLine(
                invoice_id=invoice.id,
                product_id=cl.product_id,
                variant_id=cl.variant_id,
                description=cl.description or "Subscription item",
                quantity=Decimal(cl.quantity),
                unit_price=cl.unit_price,
                discount_amount=cl.discount_amount,
                tax_rate=cl.tax_rate,
                tax_amount=cl.tax_amount,
                line_total=cl.line_total
            ))

        # Record discount redemptions
        for r_id, r_amt in applied_rule_ids:
            record_redemption(
                rule_id=r_id,
                amount=r_amt,
                db=db,
                invoice_id=invoice.id,
                customer_id=customer.id,
                subscription_id=sub_id
            )

        # 6. Update Subscription next_billing_date
        next_date = p_end + timedelta(days=1)
        sub_port = get_port("subscription")
        sub_port.set_next_billing_date(sub_id, next_date)

        # 7. Events & Notification
        publish(DomainEvent(
            event_name="invoice.generated",
            payload={"invoice_id": invoice.id, "number": invoice.number, "total": str(invoice.total)}
        ))

        notif_port = get_port("notification")
        notif_port.send(
            template="invoice_generated",
            to=customer.email,
            context={
                "customer_name": customer.name,
                "invoice_number": invoice.number,
                "period_start": str(p_start),
                "period_end": str(p_end),
                "currency": invoice.currency,
                "total": str(invoice.total),
                "due_date": str(due_date)
            },
            customer_id=customer.id,
            db_session=db
        )

        results.append({
            "status": "SUCCESS",
            "period": (p_start, p_end),
            "invoice_id": invoice.id,
            "invoice_number": invoice.number,
            "total": invoice.total
        })

    return results

def run_billing_engine(
    as_of: Optional[date] = None,
    dry_run: bool = False,
    triggered_by: str = "SCHEDULER"
) -> BillingRun:
    """
    Main entry point for recurring billing.
    Iterates billable active subscriptions and isolates errors per subscription.
    """
    target_date = as_of or date.today()
    sub_port = get_port("subscription")
    cust_port = get_port("customer")

    db = SessionLocal()
    billing_run = BillingRun(
        started_at=datetime.now(timezone.utc),
        status="RUNNING",
        triggered_by=f"DRY_RUN_{triggered_by}" if dry_run else triggered_by
    )
    db.add(billing_run)
    db.commit()
    db.refresh(billing_run)

    billable_subs = sub_port.list_billable(target_date)
    billing_run.subscriptions_checked = len(billable_subs)

    invoices_created = 0
    failures = 0

    for sub in billable_subs:
        cust = cust_port.get(sub.customer_id)
        if not cust:
            cust = CustomerDTO(id=sub.customer_id, name="Unknown Customer", email="billing@customer.com", state_code="KA")

        # Savepoint per subscription to isolate failures
        try:
            with db.begin_nested():
                sub_results = bill_single_subscription(sub, target_date, db, cust, dry_run=dry_run)
                for res in sub_results:
                    if res["status"] in ("SUCCESS", "DRY_RUN"):
                        invoices_created += 1
                        db.add(BillingRunItem(
                            run_id=billing_run.id,
                            subscription_id=sub.id,
                            period_start=res["period"][0] if res["period"] else target_date,
                            period_end=res["period"][1] if res["period"] else target_date,
                            invoice_id=res.get("invoice_id"),
                            result=res["status"]
                        ))
                    elif res["status"] == "SKIPPED":
                        db.add(BillingRunItem(
                            run_id=billing_run.id,
                            subscription_id=sub.id,
                            period_start=res["period"][0] if res["period"] else target_date,
                            period_end=res["period"][1] if res["period"] else target_date,
                            result="SKIPPED",
                            error=res.get("reason")
                        ))
            db.commit()
        except Exception as e:
            db.rollback()
            failures += 1
            db.add(BillingRunItem(
                run_id=billing_run.id,
                subscription_id=sub.id,
                period_start=sub.start_date,
                period_end=target_date,
                result="FAILED",
                error=str(e)
            ))
            db.commit()

    billing_run.finished_at = datetime.now(timezone.utc)
    billing_run.status = "COMPLETED" if failures == 0 else "PARTIAL_FAILURE"
    billing_run.invoices_created = invoices_created
    billing_run.failures = failures
    db.commit()
    db.refresh(billing_run)

    publish(DomainEvent(
        event_name="billing.run_completed",
        payload={"run_id": billing_run.id, "invoices_created": invoices_created, "failures": failures}
    ))

    db.close()
    return billing_run

def find_missed_periods(as_of: Optional[date] = None, db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Missed billing detector: identifies active subscriptions that have due periods without invoices.
    Directly consumed by Person 3 Revenue Guardian and finance alerts.
    """
    target_date = as_of or date.today()
    sub_port = get_port("subscription")
    active_subs = sub_port.list_billable(target_date)

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    missed = []
    try:
        for sub in active_subs:
            existing = db.query(BillingPeriod.period_start, BillingPeriod.period_end)\
                         .filter(BillingPeriod.subscription_id == sub.id).all()
            existing_tuples = [(r[0], r[1]) for r in existing]
            unbilled = compute_unbilled_periods(sub.start_date, sub.billing_frequency, target_date, existing_tuples)
            
            for p_start, p_end in unbilled:
                # If period end is already in the past, it's missed
                if p_end < target_date:
                    missed.append({
                        "subscription_id": sub.id,
                        "subscription_number": sub.number,
                        "customer_id": sub.customer_id,
                        "period_start": str(p_start),
                        "period_end": str(p_end),
                        "frequency": sub.billing_frequency
                    })
        return missed
    finally:
        if owns_session:
            db.close()
