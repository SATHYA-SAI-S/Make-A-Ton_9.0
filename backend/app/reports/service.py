"""
Financial Reports Service.
Provides data extraction, streaming CSV generation, and PDF document production
for the 6 core financial intelligence reports:
1. Monthly Financial Pack
2. Revenue Ledger Report
3. Outstanding Invoices & Aging Report
4. Payments & Settlements Report
5. Subscriptions Portfolio Report
6. Discount Performance & Leakage Report
"""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from typing import Generator, List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.core.money import to_money
from app.finance.models import (
    Customer,
    Plan,
    Subscription,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from app.finance.overview import normalize_mrr, compute_mrr_sql
from app.reports.pdf_generator import generate_report_pdf


def generate_csv_stream(headers: List[str], rows: List[List[Any]]) -> Generator[str, None, None]:
    """
    Streams CSV rows chunk by chunk using a memory-efficient generator.
    Avoids loading full CSV payload into memory.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow(headers)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    # Write rows
    for row in rows:
        formatted_row = [str(col) if col is not None else "" for col in row]
        writer.writerow(formatted_row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


# -------------------------------------------------------------
# 1. Monthly Financial Pack Report
# -------------------------------------------------------------
def get_monthly_financial_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=180)

    # Group invoices by month
    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.status != "CANCELLED"
    ).all()

    month_buckets: Dict[str, Dict[str, Decimal]] = {}
    for inv in invoices:
        m_key = inv.invoice_date.strftime("%Y-%m")
        if m_key not in month_buckets:
            month_buckets[m_key] = {
                "invoiced": Decimal("0.00"),
                "collected": Decimal("0.00"),
                "outstanding": Decimal("0.00"),
                "count": Decimal("0")
            }
        month_buckets[m_key]["invoiced"] += inv.total
        month_buckets[m_key]["collected"] += inv.amount_paid
        month_buckets[m_key]["outstanding"] += inv.balance
        month_buckets[m_key]["count"] += Decimal("1")

    headers = [
        "Month",
        "Total Invoices",
        "Total Invoiced (₹)",
        "Total Collected (₹)",
        "Outstanding AR (₹)",
        "Collection Rate (%)",
        "MRR Normalized (₹)",
        "ARR Equivalent (₹)"
    ]

    rows = []
    for m in sorted(month_buckets.keys()):
        data = month_buckets[m]
        inv_amt = data["invoiced"]
        col_amt = data["collected"]
        out_amt = data["outstanding"]
        col_rate = ((col_amt / inv_amt) * Decimal("100.00")).quantize(Decimal("0.1")) if inv_amt > 0 else Decimal("100.0")
        mrr_approx = inv_amt.quantize(Decimal("0.01"))
        arr_approx = (mrr_approx * Decimal("12")).quantize(Decimal("0.01"))

        rows.append([
            m,
            str(int(data["count"])),
            str(to_money(inv_amt)),
            str(to_money(col_amt)),
            str(to_money(out_amt)),
            f"{col_rate}%",
            str(to_money(mrr_approx)),
            str(to_money(arr_approx))
        ])

    tot_inv = sum([d["invoiced"] for d in month_buckets.values()])
    tot_col = sum([d["collected"] for d in month_buckets.values()])
    tot_out = sum([d["outstanding"] for d in month_buckets.values()])

    summary = {
        "Period": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "Total Invoiced": f"₹{tot_inv:,.2f}",
        "Total Collected": f"₹{tot_col:,.2f}",
        "Total Outstanding": f"₹{tot_out:,.2f}"
    }

    return {
        "title": "Monthly Financial Pack",
        "subtitle": f"Consolidated billing and revenue ledger from {start_date.isoformat()} to {end_date.isoformat()}",
        "headers": headers,
        "rows": rows,
        "summary": summary
    }


# -------------------------------------------------------------
# 2. Revenue Ledger Report
# -------------------------------------------------------------
def get_revenue_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.status != "CANCELLED"
    ).order_by(Invoice.invoice_date.desc()).all()

    headers = [
        "Invoice Number",
        "Invoice Date",
        "Customer ID",
        "Subtotal (₹)",
        "Tax (₹)",
        "Discount (₹)",
        "Total Amount (₹)",
        "Amount Paid (₹)",
        "Balance (₹)",
        "Status"
    ]

    rows = []
    for inv in invoices:
        rows.append([
            inv.number,
            inv.invoice_date.isoformat(),
            inv.customer_id,
            str(to_money(inv.subtotal or Decimal("0.00"))),
            str(to_money(inv.tax_total or Decimal("0.00"))),
            str(to_money(inv.discount_total or Decimal("0.00"))),
            str(to_money(inv.total)),
            str(to_money(inv.amount_paid)),
            str(to_money(inv.balance)),
            inv.status
        ])

    total_rev = sum([i.total for i in invoices])
    total_paid = sum([i.amount_paid for i in invoices])

    return {
        "title": "Revenue & Invoicing Ledger",
        "subtitle": f"Detailed breakdown of issued invoices between {start_date.isoformat()} and {end_date.isoformat()}",
        "headers": headers,
        "rows": rows,
        "summary": {
            "Total Invoiced": f"₹{total_rev:,.2f}",
            "Total Collected": f"₹{total_paid:,.2f}",
            "Invoice Count": str(len(invoices))
        }
    }


# -------------------------------------------------------------
# 3. Outstanding Invoices Report
# -------------------------------------------------------------
def get_outstanding_invoices_report(
    db: Session,
    as_of_date: Optional[date] = None
) -> Dict[str, Any]:
    today = as_of_date or date.today()

    invoices = db.query(Invoice).filter(
        Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
        Invoice.balance > Decimal("0.00")
    ).order_by(Invoice.due_date.asc()).all()

    headers = [
        "Invoice Number",
        "Customer ID",
        "Due Date",
        "Days Overdue",
        "Aging Bucket",
        "Total Invoiced (₹)",
        "Amount Paid (₹)",
        "Outstanding Balance (₹)",
        "Status"
    ]

    rows = []
    total_outstanding = Decimal("0.00")

    for inv in invoices:
        days_overdue = (today - inv.due_date).days
        if days_overdue <= 0:
            bucket = "Current"
        elif days_overdue <= 30:
            bucket = "1–30 Days"
        elif days_overdue <= 60:
            bucket = "31–60 Days"
        elif days_overdue <= 90:
            bucket = "61–90 Days"
        else:
            bucket = "90+ Days"

        rows.append([
            inv.number,
            inv.customer_id,
            inv.due_date.isoformat(),
            str(max(0, days_overdue)),
            bucket,
            str(to_money(inv.total)),
            str(to_money(inv.amount_paid)),
            str(to_money(inv.balance)),
            inv.status
        ])
        total_outstanding += inv.balance

    return {
        "title": "Outstanding Receivables & Aging Report",
        "subtitle": f"Unpaid invoice balances as of {today.isoformat()}",
        "headers": headers,
        "rows": rows,
        "summary": {
            "Total Outstanding": f"₹{total_outstanding:,.2f}",
            "Unpaid Invoice Count": str(len(invoices)),
            "As Of Date": today.isoformat()
        }
    }


# -------------------------------------------------------------
# 4. Payments Report
# -------------------------------------------------------------
def get_payments_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    payments = db.query(Payment).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == "RECORDED"
    ).order_by(Payment.payment_date.desc()).all()

    headers = [
        "Payment ID",
        "Reference",
        "Customer ID",
        "Payment Date",
        "Method",
        "Amount (₹)",
        "Allocated Total (₹)",
        "Status"
    ]

    rows = []
    total_pmt = Decimal("0.00")

    for p in payments:
        alloc_sum = sum([a.amount for a in p.allocations]) if p.allocations else Decimal("0.00")
        rows.append([
            p.id,
            p.reference or "None",
            p.customer_id,
            p.payment_date.isoformat(),
            p.method,
            str(to_money(p.amount)),
            str(to_money(alloc_sum)),
            p.status
        ])
        total_pmt += p.amount

    return {
        "title": "Payments & Cash Collections Ledger",
        "subtitle": f"Recorded cash inflows from {start_date.isoformat()} to {end_date.isoformat()}",
        "headers": headers,
        "rows": rows,
        "summary": {
            "Total Collections": f"₹{total_pmt:,.2f}",
            "Payment Transactions": str(len(payments))
        }
    }


# -------------------------------------------------------------
# 5. Subscriptions Report
# -------------------------------------------------------------
def get_subscriptions_report(
    db: Session,
    status: Optional[str] = None,
    plan_id: Optional[str] = None
) -> Dict[str, Any]:
    query = db.query(Subscription)
    if status and status.upper() != "ALL":
        query = query.filter(Subscription.status == status.upper())
    if plan_id:
        query = query.filter(Subscription.plan_id == plan_id)

    subs = query.order_by(Subscription.start_date.desc()).all()

    headers = [
        "Subscription Number",
        "Customer ID",
        "Plan ID",
        "Frequency",
        "Price (₹)",
        "Normalized MRR (₹)",
        "Status",
        "Start Date",
        "Expiry Date"
    ]

    rows = []
    total_mrr = Decimal("0.00")

    for s in subs:
        price = s.plan.price if s.plan else Decimal("0.00")
        freq = s.plan.billing_frequency if s.plan else "MONTHLY"
        mrr = normalize_mrr(price, freq)
        if s.status == "ACTIVE":
            total_mrr += mrr

        rows.append([
            s.number,
            s.customer_id,
            s.plan_id,
            freq,
            str(to_money(price)),
            str(to_money(mrr)),
            s.status,
            s.start_date.isoformat(),
            s.expiry_date.isoformat() if s.expiry_date else "Perpetual"
        ])

    return {
        "title": "Subscriptions Portfolio Report",
        "subtitle": f"Customer contract portfolio (Status: {status or 'ALL'})",
        "headers": headers,
        "rows": rows,
        "summary": {
            "Total Subscriptions": str(len(subs)),
            "Active Recurring MRR": f"₹{total_mrr:,.2f}"
        }
    }


# -------------------------------------------------------------
# 6. Discount Performance Report
# -------------------------------------------------------------
def get_discount_performance_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.discount_total > Decimal("0.00"),
        Invoice.status != "CANCELLED"
    ).order_by(Invoice.invoice_date.desc()).all()

    headers = [
        "Invoice Number",
        "Invoice Date",
        "Customer ID",
        "Subtotal (₹)",
        "Discount Granted (₹)",
        "Effective Discount (%)",
        "Net Invoiced (₹)",
        "Status"
    ]

    rows = []
    total_disc = Decimal("0.00")
    total_subtotal = Decimal("0.00")

    for inv in invoices:
        subtot = inv.subtotal or (inv.total + inv.discount_total)
        eff_pct = ((inv.discount_total / subtot) * Decimal("100.00")).quantize(Decimal("0.1")) if subtot > 0 else Decimal("0.0")
        rows.append([
            inv.number,
            inv.invoice_date.isoformat(),
            inv.customer_id,
            str(to_money(subtot)),
            str(to_money(inv.discount_total)),
            f"{eff_pct}%",
            str(to_money(inv.total)),
            inv.status
        ])
        total_disc += inv.discount_total
        total_subtotal += subtot

    return {
        "title": "Discount Performance & Concessions Report",
        "subtitle": f"Redeemed promotional discounts between {start_date.isoformat()} and {end_date.isoformat()}",
        "headers": headers,
        "rows": rows,
        "summary": {
            "Total Discount Granted": f"₹{total_disc:,.2f}",
            "Discounted Invoices": str(len(invoices)),
            "Gross Subtotal": f"₹{total_subtotal:,.2f}"
        }
    }
