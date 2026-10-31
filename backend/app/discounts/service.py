from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.core.money import to_decimal, round_money
from backend.app.shared.dto import TaxLineInputDTO
from backend.app.discounts.models import DiscountRule, DiscountRedemption

class DiscountApplication:
    def __init__(self, rule: DiscountRule, amount: Decimal, target_line_idx: Optional[int] = None):
        self.rule_id = rule.id
        self.rule_name = rule.name
        self.scope = rule.scope
        self.amount = round_money(amount)
        self.target_line_idx = target_line_idx

def eligible_discounts(
    lines: List[TaxLineInputDTO],
    as_of: date,
    db: Session,
    lock_rules: bool = False
) -> List[DiscountApplication]:
    """
    Evaluates discount eligibility across lines and whole subscription.
    Checks date window, min purchase, min quantity, max usage.
    Orders by priority.
    """
    query = db.query(DiscountRule).filter(
        DiscountRule.status == "ACTIVE",
        DiscountRule.start_date <= as_of,
        (DiscountRule.end_date == None) | (DiscountRule.end_date >= as_of)
    )

    if lock_rules:
        # SELECT ... FOR UPDATE where supported (PostgreSQL); SQLite ignores cleanly
        try:
            query = query.with_for_update()
        except Exception:
            pass

    rules = query.order_by(DiscountRule.priority.asc(), DiscountRule.value.desc()).all()

    total_subtotal = Decimal("0.00")
    total_quantity = 0
    product_totals: Dict[str, Tuple[Decimal, int]] = {}

    for idx, l in enumerate(lines):
        line_amt = to_decimal(l.unit_price) * Decimal(l.quantity)
        total_subtotal += line_amt
        total_quantity += l.quantity

        p_amt, p_qty = product_totals.get(l.product_id, (Decimal("0.00"), 0))
        product_totals[l.product_id] = (p_amt + line_amt, p_qty + l.quantity)

    applied: List[DiscountApplication] = []
    has_non_stackable = False

    for r in rules:
        # Check max usage
        if r.max_usage is not None and r.used_count >= r.max_usage:
            continue

        if r.scope == "PRODUCT":
            # Match product
            if not r.product_id or r.product_id not in product_totals:
                continue
            base_amt, qty = product_totals[r.product_id]
            if base_amt < to_decimal(r.min_purchase) or qty < r.min_quantity:
                continue

            # Calculate product discount amount
            if r.type == "PERCENT":
                disc_amt = round_money(base_amt * (to_decimal(r.value) / Decimal("100.00")))
            else:
                disc_amt = min(base_amt, to_decimal(r.value))

            if disc_amt > Decimal("0.00"):
                applied.append(DiscountApplication(rule=r, amount=disc_amt))
                if not r.stackable:
                    has_non_stackable = True
                    break

        elif r.scope == "SUBSCRIPTION":
            if total_subtotal < to_decimal(r.min_purchase) or total_quantity < r.min_quantity:
                continue

            if r.type == "PERCENT":
                disc_amt = round_money(total_subtotal * (to_decimal(r.value) / Decimal("100.00")))
            else:
                disc_amt = min(total_subtotal, to_decimal(r.value))

            if disc_amt > Decimal("0.00"):
                applied.append(DiscountApplication(rule=r, amount=disc_amt))
                if not r.stackable:
                    has_non_stackable = True
                    break

    return applied

def record_redemption(
    rule_id: str,
    amount: Decimal,
    db: Session,
    invoice_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> DiscountRedemption:
    rule = db.query(DiscountRule).filter_by(id=rule_id).first()
    if rule:
        rule.used_count += 1
        if rule.max_usage is not None and rule.used_count >= rule.max_usage:
            # Reached limit
            pass
    
    redemption = DiscountRedemption(
        rule_id=rule_id,
        invoice_id=invoice_id,
        customer_id=customer_id,
        subscription_id=subscription_id,
        amount=round_money(amount)
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption

def mark_expired_rules(db: Session, as_of: Optional[date] = None) -> int:
    today = as_of or date.today()
    expired = db.query(DiscountRule).filter(
        DiscountRule.status == "ACTIVE",
        DiscountRule.end_date != None,
        DiscountRule.end_date < today
    ).all()
    for r in expired:
        r.status = "EXPIRED"
    db.commit()
    return len(expired)
