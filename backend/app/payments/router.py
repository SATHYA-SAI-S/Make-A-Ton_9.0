from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.money import to_decimal
from backend.app.core.errors import NotFoundException
from backend.app.payments.models import Payment, PaymentAllocation, PaymentRefund
from backend.app.payments.service import (
    record_payment,
    allocate_payment,
    record_refund,
    record_failed_payment
)
from backend.app.payments.gateway import (
    create_gateway_order,
    process_gateway_webhook
)
from backend.app.payments.bootstrap import ProductionPaymentPort

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

class AllocationInput(BaseModel):
    invoice_id: str
    amount: Decimal

class RecordPaymentRequest(BaseModel):
    customer_id: str
    method: str
    amount: Decimal
    reference: Optional[str] = None
    notes: Optional[str] = None
    allocations: Optional[List[AllocationInput]] = None

class AllocatePaymentRequest(BaseModel):
    allocations: List[AllocationInput]

class RefundRequest(BaseModel):
    amount: Decimal
    reason: Optional[str] = None

class CreateOrderRequest(BaseModel):
    amount: Decimal
    currency: Optional[str] = "INR"
    invoice_id: Optional[str] = None
    customer_id: Optional[str] = None

@router.post("", status_code=201)
def api_record_payment(payload: RecordPaymentRequest, db: Session = Depends(get_db)):
    alloc_list = [a.model_dump() for a in payload.allocations] if payload.allocations else None
    payment = record_payment(
        customer_id=payload.customer_id,
        method=payload.method,
        amount=payload.amount,
        reference=payload.reference,
        notes=payload.notes,
        allocations=alloc_list,
        db=db
    )
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "customer_id": payment.customer_id,
        "method": payment.method,
        "amount": str(payment.amount),
        "unallocated_amount": str(payment.unallocated_amount),
        "status": payment.status,
        "payment_date": payment.payment_date.isoformat(),
        "reference": payment.reference
    }

@router.get("")
def api_list_payments(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Payment)
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if status:
        query = query.filter(Payment.status == status)

    total = query.count()
    payments = query.order_by(Payment.payment_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": p.id,
                "customer_id": p.customer_id,
                "method": p.method,
                "amount": str(p.amount),
                "unallocated_amount": str(p.unallocated_amount),
                "status": p.status,
                "payment_date": p.payment_date.isoformat(),
                "reference": p.reference
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{payment_id}")
def api_get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundException(f"Payment {payment_id} not found")

    return {
        "id": payment.id,
        "customer_id": payment.customer_id,
        "method": payment.method,
        "amount": str(payment.amount),
        "unallocated_amount": str(payment.unallocated_amount),
        "status": payment.status,
        "payment_date": payment.payment_date.isoformat(),
        "reference": payment.reference,
        "notes": payment.notes,
        "allocations": [
            {
                "id": a.id,
                "invoice_id": a.invoice_id,
                "amount": str(a.amount),
                "created_at": a.created_at.isoformat()
            }
            for a in payment.allocations
        ],
        "refunds": [
            {
                "id": r.id,
                "amount": str(r.amount),
                "reason": r.reason,
                "created_at": r.created_at.isoformat()
            }
            for r in payment.refunds
        ]
    }

@router.post("/{payment_id}/allocate")
def api_allocate_payment(
    payment_id: str,
    payload: AllocatePaymentRequest,
    db: Session = Depends(get_db)
):
    alloc_list = [a.model_dump() for a in payload.allocations]
    payment = allocate_payment(payment_id, alloc_list, db=db)
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "unallocated_amount": str(payment.unallocated_amount),
        "status": payment.status
    }

@router.post("/{payment_id}/refund")
def api_refund_payment(
    payment_id: str,
    payload: RefundRequest,
    db: Session = Depends(get_db)
):
    refund = record_refund(payment_id, payload.amount, reason=payload.reason, db=db)
    db.commit()
    db.refresh(refund)
    return {
        "refund_id": refund.id,
        "payment_id": refund.payment_id,
        "amount": str(refund.amount),
        "reason": refund.reason,
        "created_at": refund.created_at.isoformat()
    }

@router.post("/create-order")
def api_create_order(payload: CreateOrderRequest):
    return create_gateway_order(
        amount=payload.amount,
        currency=payload.currency or "INR",
        invoice_id=payload.invoice_id,
        customer_id=payload.customer_id
    )

@router.post("/webhook")
async def api_gateway_webhook(
    request: Request,
    x_gateway_signature: Optional[str] = Header(None, alias="x-gateway-signature"),
    x_razorpay_signature: Optional[str] = Header(None, alias="x-razorpay-signature"),
    db: Session = Depends(get_db)
):
    raw_body = await request.body()
    data = await request.json()
    sig = x_gateway_signature or x_razorpay_signature

    result = process_gateway_webhook(
        event_data=data,
        raw_body=raw_body,
        signature=sig,
        db=db
    )
    return result

@router.get("/customer/{customer_id}/outstanding")
def api_customer_outstanding(customer_id: str):
    port = ProductionPaymentPort()
    outstanding = port.outstanding_for_customer(customer_id)
    return {
        "customer_id": customer_id,
        "outstanding_balance": str(outstanding)
    }
