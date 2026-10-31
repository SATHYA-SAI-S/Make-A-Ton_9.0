from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.security import require_roles, UserContext
from app.core.money import to_decimal
from app.core.pagination import PaginatedResponse
from app.shared.dto import CustomerDTO, TaxBreakdownDTO, TaxLineInputDTO
from app.taxes.models import TaxRule, TaxCalculationHistory, tax_rule_products
from app.taxes.service import compute_tax

router = APIRouter(prefix="/api/v1/taxes", tags=["Taxes"])

class TaxRuleCreate(BaseModel):
    name: str
    rate: Decimal
    type: str  # GST, CGST, SGST, IGST, VAT, OTHER
    effective_from: date = date.today()
    effective_to: Optional[date] = None
    active: bool = True
    applicable_product_ids: Optional[List[str]] = None

class TaxRuleResponse(BaseModel):
    id: str
    name: str
    rate: Decimal
    type: str
    effective_from: date
    effective_to: Optional[date]
    active: bool
    applicable_product_ids: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class TaxPreviewRequest(BaseModel):
    customer: CustomerDTO
    lines: List[TaxLineInputDTO]
    as_of: date = date.today()

class TaxHistoryResponse(BaseModel):
    id: str
    rule_name: str
    rate: Decimal
    base_amount: Decimal
    amount: Decimal
    created_at: str

    model_config = ConfigDict(from_attributes=True)

@router.get("/rules", response_model=List[TaxRuleResponse])
def list_tax_rules(active_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(TaxRule)
    if active_only:
        query = query.filter(TaxRule.active == True)
    rules = query.order_by(TaxRule.name).all()
    
    result = []
    for r in rules:
        prod_ids = [row[0] for row in db.query(tax_rule_products.c.product_id).filter(tax_rule_products.c.rule_id == r.id).all()]
        result.append(TaxRuleResponse(
            id=r.id,
            name=r.name,
            rate=r.rate,
            type=r.type,
            effective_from=r.effective_from,
            effective_to=r.effective_to,
            active=r.active,
            applicable_product_ids=prod_ids
        ))
    return result

@router.post("/rules", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    payload: TaxRuleCreate,
    user: UserContext = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    rule = TaxRule(
        name=payload.name,
        rate=to_decimal(payload.rate),
        type=payload.type.upper(),
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        active=payload.active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    if payload.applicable_product_ids:
        for pid in payload.applicable_product_ids:
            db.execute(tax_rule_products.insert().values(rule_id=rule.id, product_id=pid))
        db.commit()

    return TaxRuleResponse(
        id=rule.id,
        name=rule.name,
        rate=rule.rate,
        type=rule.type,
        effective_from=rule.effective_from,
        effective_to=rule.effective_to,
        active=rule.active,
        applicable_product_ids=payload.applicable_product_ids or []
    )

@router.delete("/rules/{rule_id}")
def delete_tax_rule(
    rule_id: str,
    user: UserContext = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    rule = db.query(TaxRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Tax rule deleted"}

@router.post("/preview", response_model=List[TaxBreakdownDTO])
def preview_tax(payload: TaxPreviewRequest, db: Session = Depends(get_db)):
    return compute_tax(payload.lines, payload.customer, payload.as_of, db=db, record_history=False)
