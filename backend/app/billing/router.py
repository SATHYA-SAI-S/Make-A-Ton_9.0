from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.security import require_roles, UserContext
from app.core.pagination import PaginatedResponse
from app.billing.models import BillingRun, BillingRunItem
from app.billing.engine import run_billing_engine, find_missed_periods

router = APIRouter(prefix="/api/v1/billing", tags=["Billing Engine"])

class RunBillingRequest(BaseModel):
    as_of: Optional[date] = None
    dry_run: bool = False

class BillingRunItemResponse(BaseModel):
    id: str
    subscription_id: str
    period_start: date
    period_end: date
    invoice_id: Optional[str]
    result: str
    error: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class BillingRunResponse(BaseModel):
    id: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    triggered_by: str
    subscriptions_checked: int
    invoices_created: int
    failures: int
    error: Optional[str]
    items: List[BillingRunItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

@router.post("/run", response_model=BillingRunResponse, status_code=status.HTTP_200_OK)
def trigger_billing_run(
    payload: RunBillingRequest,
    user: UserContext = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    run = run_billing_engine(
        as_of=payload.as_of,
        dry_run=payload.dry_run,
        triggered_by=f"ADMIN_{user.user_id}"
    )
    # Refresh to include items
    return db.query(BillingRun).filter_by(id=run.id).first()

@router.get("/runs", response_model=PaginatedResponse[BillingRunResponse])
def list_billing_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: UserContext = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    query = db.query(BillingRun)
    total = query.count()
    runs = query.order_by(desc(BillingRun.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=runs,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/runs/{run_id}", response_model=BillingRunResponse)
def get_billing_run(
    run_id: str,
    user: UserContext = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    run = db.query(BillingRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Billing run not found")
    return run

@router.get("/missed-periods")
def detect_missed_periods(
    as_of: Optional[date] = Query(None),
    user: UserContext = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    return find_missed_periods(as_of=as_of, db=db)
