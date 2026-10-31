from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.overdue.models import PaymentFollowup
from app.overdue.service import (
    get_overdue_invoices,
    get_overdue_summary,
    evaluate_and_send_reminders,
    record_manual_followup
)

router = APIRouter(prefix="/api/v1/overdue", tags=["overdue"])

class TriggerRemindersRequest(BaseModel):
    as_of: Optional[date] = None

class CreateFollowupRequest(BaseModel):
    invoice_id: str
    notes: str
    promised_payment_date: Optional[date] = None
    channel: Optional[str] = "PHONE"
    status: Optional[str] = "PROMISED"

@router.get("/invoices")
def api_get_overdue_invoices(
    as_of: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return get_overdue_invoices(as_of=as_of, db=db)

@router.get("/summary")
def api_get_overdue_summary(
    as_of: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return get_overdue_summary(as_of=as_of, db=db)

@router.post("/trigger-reminders")
def api_trigger_reminders(
    payload: TriggerRemindersRequest = None,
    db: Session = Depends(get_db)
):
    as_of_date = payload.as_of if payload else None
    result = evaluate_and_send_reminders(as_of=as_of_date, db=db)
    db.commit()
    return result

@router.post("/followups", status_code=201)
def api_create_followup(
    payload: CreateFollowupRequest,
    db: Session = Depends(get_db)
):
    followup = record_manual_followup(
        invoice_id=payload.invoice_id,
        notes=payload.notes,
        promised_payment_date=payload.promised_payment_date,
        channel=payload.channel or "PHONE",
        status=payload.status or "PROMISED",
        db=db
    )
    db.commit()
    db.refresh(followup)
    return {
        "id": followup.id,
        "invoice_id": followup.invoice_id,
        "customer_id": followup.customer_id,
        "channel": followup.channel,
        "notes": followup.notes,
        "promised_payment_date": followup.promised_payment_date.isoformat() if followup.promised_payment_date else None,
        "status": followup.status,
        "created_at": followup.created_at.isoformat()
    }

@router.get("/followups/{invoice_id}")
def api_get_invoice_followups(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    followups = db.query(PaymentFollowup).filter(
        PaymentFollowup.invoice_id == invoice_id
    ).order_by(PaymentFollowup.created_at.desc()).all()

    return [
        {
            "id": f.id,
            "invoice_id": f.invoice_id,
            "customer_id": f.customer_id,
            "tier": f.tier,
            "channel": f.channel,
            "notes": f.notes,
            "promised_payment_date": f.promised_payment_date.isoformat() if f.promised_payment_date else None,
            "status": f.status,
            "created_at": f.created_at.isoformat()
        }
        for f in followups
    ]
