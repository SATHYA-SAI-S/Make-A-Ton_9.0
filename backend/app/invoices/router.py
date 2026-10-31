from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.security import current_user, UserContext
from app.core.pagination import PaginatedResponse
from app.shared.registry import get_port
from app.invoices.models import Invoice, InvoiceLine
from app.invoices.service import (
    confirm_invoice,
    cancel_invoice,
    generate_invoice_pdf,
    to_dto
)

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

class InvoiceLineItem(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)

class InvoiceDetailResponse(BaseModel):
    id: str
    number: str
    customer_id: str
    subscription_id: Optional[str]
    status: str
    invoice_date: date
    due_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance: Decimal
    currency: str
    is_overdue: bool
    cancellation_reason: Optional[str]
    snapshot: Dict[str, Any]
    lines: List[InvoiceLineItem] = []

    model_config = ConfigDict(from_attributes=True)

class CancelRequest(BaseModel):
    reason: str

@router.get("", response_model=PaginatedResponse[InvoiceDetailResponse])
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice)

    # Customer scope isolation
    if user.role == "customer":
        query = query.filter(Invoice.customer_id == user.customer_id)
    elif customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if status:
        query = query.filter(Invoice.status == status.upper())

    total = query.count()
    invoices = query.order_by(desc(Invoice.invoice_date), desc(Invoice.created_at))\
                    .offset((page - 1) * page_size).limit(page_size).all()

    # Filter is_overdue in memory if requested
    items = []
    for inv in invoices:
        if is_overdue is not None and inv.is_overdue != is_overdue:
            continue
        items.append(InvoiceDetailResponse(
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
            currency=inv.currency,
            is_overdue=inv.is_overdue,
            cancellation_reason=inv.cancellation_reason,
            snapshot=inv.snapshot or {},
            lines=inv.lines
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(
    invoice_id: str,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role == "customer" and inv.customer_id != user.customer_id:
        raise HTTPException(status_code=403, detail="Cannot access another customer's invoice")

    return InvoiceDetailResponse(
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
        currency=inv.currency,
        is_overdue=inv.is_overdue,
        cancellation_reason=inv.cancellation_reason,
        snapshot=inv.snapshot or {},
        lines=inv.lines
    )

@router.post("/{invoice_id}/confirm")
def confirm_invoice_endpoint(
    invoice_id: str,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    if user.role == "customer":
        raise HTTPException(status_code=403, detail="Customers cannot confirm invoices")
    inv = confirm_invoice(invoice_id, db)
    return {"message": "Invoice confirmed", "id": inv.id, "status": inv.status}

@router.post("/{invoice_id}/cancel")
def cancel_invoice_endpoint(
    invoice_id: str,
    payload: CancelRequest,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    if user.role == "customer":
        raise HTTPException(status_code=403, detail="Customers cannot cancel invoices")
    inv = cancel_invoice(invoice_id, payload.reason, db)
    return {"message": "Invoice cancelled", "id": inv.id, "status": inv.status}

@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: str,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if user.role == "customer" and inv.customer_id != user.customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    pdf_bytes = generate_invoice_pdf(inv)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={inv.number}.pdf"}
    )

@router.get("/{invoice_id}/print")
def print_invoice_html(
    invoice_id: str,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if user.role == "customer" and inv.customer_id != user.customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    snap = inv.snapshot or {}
    cust = snap.get("customer", {})
    comp = snap.get("company", {})

    lines_html = "".join([
        f"<tr><td>{l.description}</td><td>{int(l.quantity)}</td><td>{format_money(l.unit_price)}</td><td>{format_money(l.discount_amount)}</td><td>{format_money(l.tax_amount)} ({l.tax_rate}%)</td><td>{format_money(l.line_total)}</td></tr>"
        for l in inv.lines
    ])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{inv.number} - Tax Invoice</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px; color: #111; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #1E3A8A; padding-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
            th, td {{ border: 1px solid #E5E7EB; padding: 10px; text-align: left; }}
            th {{ background: #F3F4F6; }}
            .total-box {{ float: right; width: 300px; margin-top: 20px; }}
            .total-row {{ display: flex; justify-content: space-between; padding: 4px 0; }}
            .grand-total {{ font-size: 1.2em; font-weight: bold; border-top: 1px solid #111; padding-top: 8px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="header">
            <div>
                <h2>{comp.get('name', 'Brightloop Software')}</h2>
                <p>GSTIN: {comp.get('gstin', '-')}<br>State: {comp.get('state_code', '-')}</p>
            </div>
            <div>
                <h1>TAX INVOICE</h1>
                <p><b>Invoice:</b> {inv.number}<br><b>Date:</b> {inv.invoice_date}<br><b>Due:</b> {inv.due_date}<br><b>Status:</b> {inv.status}</p>
            </div>
        </div>
        <p><b>Billed To:</b> {cust.get('name', 'Customer')} ({cust.get('email', '-')})<br>GSTIN: {cust.get('gstin', '-')}</p>
        <table>
            <thead><tr><th>Item</th><th>Qty</th><th>Unit Price</th><th>Discount</th><th>Tax</th><th>Total</th></tr></thead>
            <tbody>{lines_html}</tbody>
        </table>
        <div class="total-box">
            <div class="total-row"><span>Subtotal:</span><span>{format_money(inv.subtotal)}</span></div>
            <div class="total-row"><span>Discount:</span><span>-{format_money(inv.discount_total)}</span></div>
            <div class="total-row"><span>Tax:</span><span>{format_money(inv.tax_total)}</span></div>
            <div class="total-row grand-total"><span>Total:</span><span>{inv.currency} {format_money(inv.total)}</span></div>
            <div class="total-row"><span>Balance Due:</span><span>{inv.currency} {format_money(inv.balance)}</span></div>
        </div>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

@router.post("/{invoice_id}/send")
def send_invoice_email(
    invoice_id: str,
    user: UserContext = Depends(current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter_by(id=invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    snap = inv.snapshot or {}
    cust = snap.get("customer", {})
    recipient = cust.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="Invoice has no customer email")

    notif_port = get_port("notification")
    sent = notif_port.send(
        template="invoice_confirmed" if inv.status == "CONFIRMED" else "invoice_generated",
        to=recipient,
        context={
            "customer_name": cust.get("name", "Customer"),
            "invoice_number": inv.number,
            "period_start": str(inv.invoice_date),
            "period_end": str(inv.due_date),
            "currency": inv.currency,
            "total": format_money(inv.total),
            "due_date": str(inv.due_date),
            "payment_terms_days": 15
        },
        customer_id=inv.customer_id
    )
    return {"message": "Invoice email dispatched", "sent": sent}
