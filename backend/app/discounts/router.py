from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, ConfigDict

from backend.app.core.database import get_db
from backend.app.core.security import require_roles, UserContext
from backend.app.core.money import to_decimal
from backend.app.discounts.models import DiscountRule, DiscountRedemption

router = APIRouter(prefix="/api/v1/discounts", tags=["Discounts"])

class DiscountRuleCreate(BaseModel):
    name: str
    type: str  # FIXED, PERCENT
    value: Decimal
    min_purchase: Decimal = Decimal("0.00")
    min_quantity: int = 0
    start_date: date = date.today()
    end_date: Optional[date] = None
    max_usage: Optional[int] = None
    scope: str = "SUBSCRIPTION"  # PRODUCT, SUBSCRIPTION
    product_id: Optional[str] = None
    priority: int = 1
    stackable: bool = False
    status: str = "ACTIVE"

class DiscountRuleResponse(BaseModel):
    id: str
    name: str
    type: str
    value: Decimal
    min_purchase: Decimal
    min_quantity: int
    start_date: date
    end_date: Optional[date]
    max_usage: Optional[int]
    used_count: int
    scope: str
    product_id: Optional[str]
    priority: int
    stackable: bool
    status: str

    model_config = ConfigDict(from_attributes=True)

class DiscountPerformanceItem(BaseModel):
    rule_id: str
    rule_name: str
    redemptions_count: int
    total_discount_amount: Decimal

@router.get("/rules", response_model=List[DiscountRuleResponse])
def list_discount_rules(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(DiscountRule)
    if status_filter:
        query = query.filter(DiscountRule.status == status_filter.upper())
    return query.order_by(DiscountRule.priority.asc(), DiscountRule.name.asc()).all()

@router.post("/rules", response_model=DiscountRuleResponse, status_code=status.HTTP_201_CREATED)
def create_discount_rule(
    payload: DiscountRuleCreate,
    user: UserContext = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    rule = DiscountRule(
        name=payload.name,
        type=payload.type.upper(),
        value=to_decimal(payload.value),
        min_purchase=to_decimal(payload.min_purchase),
        min_quantity=payload.min_quantity,
        start_date=payload.start_date,
        end_date=payload.end_date,
        max_usage=payload.max_usage,
        scope=payload.scope.upper(),
        product_id=payload.product_id,
        priority=payload.priority,
        stackable=payload.stackable,
        status=payload.status.upper()
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/performance", response_model=List[DiscountPerformanceItem])
def get_discount_performance(
    user: UserContext = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    results = db.query(
        DiscountRule.id,
        DiscountRule.name,
        func.count(DiscountRedemption.id).label("redemptions_count"),
        func.coalesce(func.sum(DiscountRedemption.amount), Decimal("0.00")).label("total_discount_amount")
    ).outerjoin(DiscountRedemption, DiscountRule.id == DiscountRedemption.rule_id)\
     .group_by(DiscountRule.id, DiscountRule.name)\
     .all()

    return [
        DiscountPerformanceItem(
            rule_id=r[0],
            rule_name=r[1],
            redemptions_count=r[2],
            total_discount_amount=to_decimal(r[3])
        )
        for r in results
    ]
