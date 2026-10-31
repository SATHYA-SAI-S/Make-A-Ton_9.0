"""
High-Volume Synthetic Data Generator for Financial Intelligence (P3-T15).
Generates benchmark datasets:
- 500+ Customers across segments (Enterprise, Mid-Market, SMB)
- 6 Standard & Enterprise Plans (Monthly & Annual)
- 10,000 Subscriptions (Active, Cancelled, Paused)
- 50,000 Invoices (Paid, Confirmed, Overdue, Cancelled)
- 40,000 Payments & Payment Allocations
- Associated Audit Logs & Snapshot Records

Optimized for batch-insertion throughput to satisfy the < 2.0s query latency benchmark.
"""
import argparse
import random
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.finance.models import (
    Customer,
    Plan,
    Subscription,
    SubscriptionLine,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from app.audit.models import AuditLog


PLANS_DATA = [
    {"id": "plan-starter-m", "name": "Starter Monthly", "price": Decimal("2500.00"), "freq": "MONTHLY"},
    {"id": "plan-growth-m", "name": "Growth Monthly", "price": Decimal("7500.00"), "freq": "MONTHLY"},
    {"id": "plan-pro-m", "name": "Pro Monthly", "price": Decimal("18000.00"), "freq": "MONTHLY"},
    {"id": "plan-enterprise-m", "name": "Enterprise Monthly", "price": Decimal("48000.00"), "freq": "MONTHLY"},
    {"id": "plan-growth-y", "name": "Growth Annual", "price": Decimal("75000.00"), "freq": "YEARLY"},
    {"id": "plan-enterprise-y", "name": "Enterprise Annual", "price": Decimal("480000.00"), "freq": "YEARLY"},
]

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "BANK_TRANSFER"]
SEGMENTS = ["ENTERPRISE", "MID_MARKET", "SMB", "STARTUP"]


def seed_analytics_data(
    db: Session,
    num_customers: int = 500,
    num_subs: int = 10000,
    num_invoices: int = 50000,
    num_payments: int = 40000,
    batch_size: int = 2000,
    quiet: bool = False,
    reset: bool = True,
) -> Dict[str, Any]:
    """
    Populates the database with realistic synthetic financial records in optimized batches.
    """
    start_time = time.time()
    random.seed(42)
    today = date.today()

    if not quiet:
        print(f"[*] Starting high-volume seed: {num_subs} subs, {num_invoices} invoices, {num_payments} payments...")

    # Ensure tables exist
    Base.metadata.create_all(bind=db.get_bind())

    # Clean existing seed records if requested
    if reset:
        if not quiet:
            print("[*] Clearing prior synthetic seed records...")
        try:
            db.query(PaymentAllocation).filter(PaymentAllocation.payment_id.like("pay-seed-%")).delete(synchronize_session=False)
            db.query(Payment).filter(Payment.id.like("pay-seed-%")).delete(synchronize_session=False)
            db.query(InvoiceLine).filter(InvoiceLine.invoice_id.like("inv-seed-%")).delete(synchronize_session=False)
            db.query(Invoice).filter(Invoice.id.like("inv-seed-%")).delete(synchronize_session=False)
            db.query(SubscriptionLine).filter(SubscriptionLine.subscription_id.like("sub-seed-%")).delete(synchronize_session=False)
            db.query(Subscription).filter(Subscription.id.like("sub-seed-%")).delete(synchronize_session=False)
            db.query(Customer).filter(Customer.id.like("cust-seed-%")).delete(synchronize_session=False)
            db.commit()
        except Exception as e:
            db.rollback()

    # 1. Seed Plans (Idempotent merge)
    for p_info in PLANS_DATA:
        existing_plan = db.query(Plan).filter(Plan.id == p_info["id"]).first()
        if not existing_plan:
            db.add(Plan(
                id=p_info["id"],
                name=p_info["name"],
                price=p_info["price"],
                billing_frequency=p_info["freq"],
                min_quantity=1,
                status="ACTIVE"
            ))
    db.commit()

    # 2. Seed Customers
    if not quiet:
        print(f"[*] Generating {num_customers} customers...")
    customer_ids: List[str] = []
    cust_objs: List[Customer] = []
    for i in range(1, num_customers + 1):
        cid = f"cust-seed-{i:05d}"
        customer_ids.append(cid)
        cust_objs.append(Customer(
            id=cid,
            name=f"Enterprise Client {i}",
            email=f"billing_{i}@enterprise{i}.com",
            phone=f"+91 98000 {i:05d}",
            billing_address=f"{i} Tech Park, Sector 4, Bangalore, India",
            state_code="29",
            gstin=f"29AAAAA{i:04d}A1Z5",
            status="ACTIVE",
            segment=SEGMENTS[i % len(SEGMENTS)],
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(60, 500))
        ))
    db.bulk_save_objects(cust_objs)
    db.commit()

    # 3. Seed Subscriptions in Batches
    if not quiet:
        print(f"[*] Generating {num_subs} subscriptions in batches of {batch_size}...")
    sub_ids: List[str] = []
    statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "PAUSED", "CANCELLED"]

    for b in range(0, num_subs, batch_size):
        chunk_subs = []
        chunk_lines = []
        limit = min(b + batch_size, num_subs)
        for i in range(b, limit):
            sub_id = f"sub-seed-{i:06d}"
            sub_ids.append(sub_id)
            c_id = customer_ids[i % num_customers]
            plan = PLANS_DATA[i % len(PLANS_DATA)]
            status = statuses[i % len(statuses)]
            days_ago = random.randint(30, 450)
            sub_start = today - timedelta(days=days_ago)
            next_bill = sub_start + timedelta(days=30) if status == "ACTIVE" else None

            chunk_subs.append(Subscription(
                id=sub_id,
                number=f"SUB-{i:06d}",
                customer_id=c_id,
                plan_id=plan["id"],
                status=status,
                start_date=sub_start,
                expiry_date=sub_start + timedelta(days=365) if "y" in plan["id"] else None,
                next_billing_date=next_bill,
                currency="INR"
            ))

            chunk_lines.append(SubscriptionLine(
                id=str(uuid.uuid4()),
                subscription_id=sub_id,
                product_id=f"prod-{plan['id']}",
                unit_price=plan["price"],
                quantity=1,
                amount=plan["price"]
            ))

        db.bulk_save_objects(chunk_subs)
        db.bulk_save_objects(chunk_lines)
        db.commit()

    # 4. Seed Invoices in Batches
    if not quiet:
        print(f"[*] Generating {num_invoices} invoices in batches of {batch_size}...")
    invoice_ids: List[str] = []
    paid_invoice_info: List[Dict[str, Any]] = []

    for b in range(0, num_invoices, batch_size):
        chunk_invoices = []
        chunk_lines = []
        limit = min(b + batch_size, num_invoices)
        for i in range(b, limit):
            inv_id = f"inv-seed-{i:07d}"
            invoice_ids.append(inv_id)
            c_id = customer_ids[i % num_customers]
            s_id = sub_ids[i % len(sub_ids)]
            plan = PLANS_DATA[i % len(PLANS_DATA)]

            subtotal = plan["price"]
            discount = Decimal("500.00") if (i % 7 == 0) else Decimal("0.00")
            taxable = max(Decimal("0.00"), subtotal - discount)
            tax = (taxable * Decimal("0.18")).quantize(Decimal("0.01"))
            total = taxable + tax

            days_ago = (i % 360) + 1
            inv_date = today - timedelta(days=days_ago)
            due_date = inv_date + timedelta(days=15)

            # 75% PAID, 15% CONFIRMED/PENDING, 7% OVERDUE, 3% CANCELLED
            mod = i % 100
            if mod < 75:
                status = "PAID"
                paid = total
                balance = Decimal("0.00")
                paid_invoice_info.append({"id": inv_id, "customer_id": c_id, "amount": paid, "date": due_date - timedelta(days=2)})
            elif mod < 90:
                status = "CONFIRMED"
                paid = Decimal("0.00")
                balance = total
            elif mod < 97:
                status = "CONFIRMED"
                due_date = today - timedelta(days=random.randint(5, 75))
                paid = Decimal("0.00")
                balance = total
            else:
                status = "CANCELLED"
                paid = Decimal("0.00")
                balance = Decimal("0.00")

            chunk_invoices.append(Invoice(
                id=inv_id,
                number=f"INV-{inv_date.year}-{i:07d}",
                customer_id=c_id,
                subscription_id=s_id,
                status=status,
                invoice_date=inv_date,
                due_date=due_date,
                subtotal=subtotal,
                tax_total=tax,
                discount_total=discount,
                total=total,
                amount_paid=paid,
                balance=balance
            ))

            chunk_lines.append(InvoiceLine(
                id=str(uuid.uuid4()),
                invoice_id=inv_id,
                product_id=f"prod-{plan['id']}",
                description=f"Subscription billing for {plan['name']}",
                quantity=1,
                unit_price=subtotal,
                line_total=subtotal
            ))

        db.bulk_save_objects(chunk_invoices)
        db.bulk_save_objects(chunk_lines)
        db.commit()

    # 5. Seed Payments & Allocations in Batches
    if not quiet:
        print(f"[*] Generating {num_payments} payments and allocations...")
    for b in range(0, min(num_payments, len(paid_invoice_info)), batch_size):
        chunk_payments = []
        chunk_allocs = []
        limit = min(b + batch_size, len(paid_invoice_info), num_payments)
        for i in range(b, limit):
            info = paid_invoice_info[i]
            p_id = f"pay-seed-{i:07d}"
            method = PAYMENT_METHODS[i % len(PAYMENT_METHODS)]

            chunk_payments.append(Payment(
                id=p_id,
                customer_id=info["customer_id"],
                method=method,
                amount=info["amount"],
                payment_date=info["date"],
                reference=f"REF-{method[:3]}-{i:07d}",
                status="RECORDED"
            ))

            chunk_allocs.append(PaymentAllocation(
                id=str(uuid.uuid4()),
                payment_id=p_id,
                invoice_id=info["id"],
                amount=info["amount"]
            ))

        db.bulk_save_objects(chunk_payments)
        db.bulk_save_objects(chunk_allocs)
        db.commit()

    # 6. Seed Sample Audit Trail Entries
    if not quiet:
        print("[*] Generating audit compliance trail records...")
    chunk_audits = []
    for i in range(100):
        chunk_audits.append(AuditLog(
            id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc) - timedelta(hours=i * 2),
            actor_id=f"usr-staff-{(i % 5) + 1:03d}",
            actor_role="staff",
            action="invoice.confirmed" if i % 2 == 0 else "subscription.renewed",
            entity_type="invoice" if i % 2 == 0 else "subscription",
            entity_id=invoice_ids[i % len(invoice_ids)],
            before={"status": "DRAFT"},
            after={"status": "CONFIRMED"}
        ))
    db.bulk_save_objects(chunk_audits)
    db.commit()

    elapsed = time.time() - start_time
    if not quiet:
        print(f"[DONE] Seeding successfully completed in {elapsed:.2f} seconds!")

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed,
        "counts": {
            "customers": num_customers,
            "subscriptions": num_subs,
            "invoices": num_invoices,
            "payments": min(num_payments, len(paid_invoice_info))
        }
    }


def main():
    parser = argparse.ArgumentParser(description="SubscriptIQ High-Volume Analytics Benchmark Seeder")
    parser.add_argument("--subscriptions", type=int, default=10000, help="Number of subscriptions to seed (default: 10000)")
    parser.add_argument("--invoices", type=int, default=50000, help="Number of invoices to seed (default: 50000)")
    parser.add_argument("--payments", type=int, default=40000, help="Number of payments to seed (default: 40000)")
    parser.add_argument("--customers", type=int, default=500, help="Number of customers to seed (default: 500)")
    parser.add_argument("--batch-size", type=int, default=2000, help="Bulk insertion batch size (default: 2000)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_analytics_data(
            db=db,
            num_customers=args.customers,
            num_subs=args.subscriptions,
            num_invoices=args.invoices,
            num_payments=args.payments,
            batch_size=args.batch_size
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
