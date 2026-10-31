from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.reconciliation.service import (
    generate_reconciliation_report,
    auto_allocate_unallocated_credits
)

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])

class AutoAllocateRequest(BaseModel):
    customer_id: Optional[str] = None

@router.get("/report")
def api_get_reconciliation_report(db: Session = Depends(get_db)):
    return generate_reconciliation_report(db=db)

@router.post("/allocate-unallocated")
def api_auto_allocate(
    payload: AutoAllocateRequest = None,
    db: Session = Depends(get_db)
):
    cust_id = payload.customer_id if payload else None
    result = auto_allocate_unallocated_credits(customer_id=cust_id, db=db)
    db.commit()
    return result
