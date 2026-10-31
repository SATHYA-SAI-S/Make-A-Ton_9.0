import io
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.money import to_decimal, round_money, format_money
from backend.app.core.errors import AppException
from backend.app.shared.dto import InvoiceDTO, CustomerDTO
from backend.app.shared.events import DomainEvent, publish
from backend.app.shared.registry import get_port
from backend.app.invoices.models import Invoice, InvoiceLine
from backend.app.taxes.models import BillingSettings

def generate_invoice_number(db: Session) -> str:
    """Generates sequential invoice number: INV-YYYY-000001."""
    current_year = date.today().year
    prefix = f"INV-{current_year}-"

    # Query latest invoice for current year
    latest = db.query(Invoice).filter(Invoice.number.like(f"{prefix}%"))\
               .order_by(Invoice.number.desc()).first()

    if latest:
        try:
            seq_part = latest.number.split("-")[-1]
            next_seq = int(seq_part) + 1
        except Exception:
            next_seq = 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:06d}"

def create_invoice_snapshot(
    customer: CustomerDTO,
    plan_name: Optional[str],
    lines_data: List[Dict[str, Any]],
    tax_rules_used: List[str]
) -> Dict[str, Any]:
    """Generates immutable JSON snapshot preserved on the invoice."""
    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "state_code": customer.state_code,
            "gstin": customer.gstin,
            "billing_address": customer.billing_address
        },
        "company": {
            "name": settings.COMPANY_NAME,
            "state_code": settings.COMPANY_STATE_CODE,
            "gstin": settings.COMPANY_GSTIN
        },
        "plan_name": plan_name or "Custom Subscription",
        "tax_rules_used": tax_rules_used,
        "snapshot_at": datetime.now(timezone.utc).isoformat()
    }

def confirm_invoice(invoice_id: str, db: Session) -> Invoice:
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise AppException("NOT_FOUND", "Invoice not found", status_code=404)
    if inv.status != "DRAFT":
        raise AppException("INVALID_STATE", f"Cannot confirm invoice in status {inv.status}")

    inv.status = "CONFIRMED"
    db.commit()
    db.refresh(inv)

    publish(DomainEvent(
        event_name="invoice.confirmed",
        payload={"invoice_id": inv.id, "number": inv.number, "total": str(inv.total)}
    ))
    return inv

def cancel_invoice(invoice_id: str, reason: str, db: Session) -> Invoice:
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise AppException("NOT_FOUND", "Invoice not found", status_code=404)
    if inv.amount_paid > Decimal("0.00"):
        raise AppException("CANNOT_CANCEL", "Cannot cancel an invoice with recorded payments")
    if inv.status not in ("DRAFT", "CONFIRMED"):
        raise AppException("INVALID_STATE", f"Cannot cancel invoice in status {inv.status}")
    if not reason or not reason.strip():
        raise AppException("REASON_REQUIRED", "Cancellation reason is required")

    inv.status = "CANCELLED"
    inv.cancellation_reason = reason.strip()
    db.commit()
    db.refresh(inv)

    publish(DomainEvent(
        event_name="invoice.cancelled",
        payload={"invoice_id": inv.id, "number": inv.number, "reason": reason}
    ))
    return inv

def generate_invoice_pdf(invoice: Invoice) -> bytes:
    """Renders a PDF for an invoice using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    elements = []

    # Title & Header
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1E3A8A'))
    elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    elements.append(Spacer(1, 10))

    # Company & Invoice Metadata
    snap = invoice.snapshot or {}
    comp = snap.get("company", {})
    cust = snap.get("customer", {})

    header_data = [
        [
            Paragraph(f"<b>Seller:</b><br/>{comp.get('name', settings.COMPANY_NAME)}<br/>GSTIN: {comp.get('gstin', settings.COMPANY_GSTIN)}<br/>State: {comp.get('state_code', settings.COMPANY_STATE_CODE)}", styles['Normal']),
            Paragraph(f"<b>Invoice #:</b> {invoice.number}<br/><b>Date:</b> {invoice.invoice_date}<br/><b>Due Date:</b> {invoice.due_date}<br/><b>Status:</b> {invoice.status}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Billed To:</b><br/>{cust.get('name', 'Valued Customer')}<br/>Email: {cust.get('email', '-')}<br/>GSTIN: {cust.get('gstin', '-')}<br/>State: {cust.get('state_code', '-')}", styles['Normal']),
            Paragraph(f"<b>Currency:</b> {invoice.currency}<br/><b>Plan:</b> {snap.get('plan_name', 'Subscription')}", styles['Normal'])
        ]
    ]
    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # Line Items Table
    table_data = [["Item Description", "Qty", "Unit Price", "Discount", "Tax", "Total"]]
    for line in invoice.lines:
        table_data.append([
            Paragraph(line.description, styles['Normal']),
            str(int(line.quantity)),
            format_money(line.unit_price),
            format_money(line.discount_amount),
            f"{format_money(line.tax_amount)} ({line.tax_rate}%)",
            format_money(line.line_total)
        ])

    lines_table = Table(table_data, colWidths=[180, 40, 75, 75, 90, 80])
    lines_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#111827')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    elements.append(lines_table)
    elements.append(Spacer(1, 15))

    # Summary Totals
    summary_data = [
        ["Subtotal:", format_money(invoice.subtotal)],
        ["Discounts:", f"- {format_money(invoice.discount_total)}"],
        ["Taxes Total:", format_money(invoice.tax_total)],
        ["Invoice Total:", f"{invoice.currency} {format_money(invoice.total)}"],
        ["Amount Paid:", f"{invoice.currency} {format_money(invoice.amount_paid)}"],
        ["Balance Due:", f"{invoice.currency} {format_money(invoice.balance)}"]
    ]
    summary_table = Table(summary_data, colWidths=[440, 100])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'),
        ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,5), (-1,5), colors.HexColor('#B91C1C') if invoice.balance > 0 else colors.HexColor('#047857')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(summary_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def to_dto(inv: Invoice) -> InvoiceDTO:
    return InvoiceDTO(
        id=inv.id,
        number=inv.number,
        customer_id=inv.customer_id,
        subscription_id=inv.subscription_id,
        status=inv.status,
        invoice_date=inv.invoice_date,
        due_date=inv.due_date,
        subtotal=inv.subtotal,
        discount_total=inv.discount_total,
        tax_total=inv.tax_total,
        total=inv.total,
        amount_paid=inv.amount_paid,
        balance=inv.balance,
        is_overdue=inv.is_overdue,
        snapshot=inv.snapshot or {}
    )
