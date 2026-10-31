from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.money import to_decimal, round_money
from app.shared.dto import CustomerDTO, TaxBreakdownDTO, TaxLineInputDTO
from app.shared.ports import TaxPreviewPort
from app.taxes.models import TaxRule, TaxCalculationHistory, BillingSettings, tax_rule_products

def get_company_state_code(db: Optional[Session] = None) -> str:
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True
    try:
        cfg = db.query(BillingSettings).filter_by(id="default").first()
        return cfg.company_state_code if cfg else settings.COMPANY_STATE_CODE
    finally:
        if owns_session:
            db.close()

def compute_tax(
    lines: List[TaxLineInputDTO],
    customer: CustomerDTO,
    as_of: date,
    db: Optional[Session] = None,
    record_history: bool = False
) -> List[TaxBreakdownDTO]:
    """
    Computes tax using Place-of-Supply rules and active tax rules in effect for `as_of`.
    Intra-state (customer state == company state): GST splits into CGST (half) + SGST (half).
    Inter-state (customer state != company state): IGST (full rate).
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        company_state = get_company_state_code(db)
        customer_state = customer.state_code.upper() if customer.state_code else company_state

        # Query active rules effective as of as_of
        rules = db.query(TaxRule).filter(
            TaxRule.active == True,
            TaxRule.effective_from <= as_of,
            (TaxRule.effective_to == None) | (TaxRule.effective_to >= as_of)
        ).all()

        breakdowns: List[TaxBreakdownDTO] = []

        for line in lines:
            line_subtotal = to_decimal(line.unit_price) * Decimal(line.quantity)
            discounted_base = max(Decimal("0.00"), line_subtotal - to_decimal(line.discount_amount))
            discounted_base = round_money(discounted_base)

            if discounted_base <= Decimal("0.00"):
                continue

            for rule in rules:
                # Check product applicability: if products are specified in tax_rule_products, rule must match
                product_rows = db.execute(
                    select(tax_rule_products.c.product_id).where(tax_rule_products.c.rule_id == rule.id)
                ).scalars().all()
                if product_rows and line.product_id not in product_rows:
                    continue

                rate = to_decimal(rule.rate)

                # Place of Supply classification
                if rule.type == "GST":
                    if customer_state == company_state:
                        # Intra-state: Split 50% CGST, 50% SGST
                        half_rate = round_money(rate / Decimal("2.0"))
                        cgst_amt = round_money(discounted_base * (half_rate / Decimal("100.0")))
                        sgst_amt = round_money(discounted_base * (half_rate / Decimal("100.0")))

                        cgst = TaxBreakdownDTO(
                            rule_name=f"{rule.name} (CGST)",
                            tax_type="CGST",
                            rate=half_rate,
                            base_amount=discounted_base,
                            tax_amount=cgst_amt
                        )
                        sgst = TaxBreakdownDTO(
                            rule_name=f"{rule.name} (SGST)",
                            tax_type="SGST",
                            rate=half_rate,
                            base_amount=discounted_base,
                            tax_amount=sgst_amt
                        )
                        breakdowns.extend([cgst, sgst])

                        if record_history:
                            db.add(TaxCalculationHistory(
                                rule_id=rule.id, rule_name=cgst.rule_name, rate=half_rate,
                                base_amount=discounted_base, amount=cgst_amt
                            ))
                            db.add(TaxCalculationHistory(
                                rule_id=rule.id, rule_name=sgst.rule_name, rate=half_rate,
                                base_amount=discounted_base, amount=sgst_amt
                            ))
                    else:
                        # Inter-state: IGST
                        igst_amt = round_money(discounted_base * (rate / Decimal("100.0")))
                        igst = TaxBreakdownDTO(
                            rule_name=f"{rule.name} (IGST)",
                            tax_type="IGST",
                            rate=rate,
                            base_amount=discounted_base,
                            tax_amount=igst_amt
                        )
                        breakdowns.append(igst)

                        if record_history:
                            db.add(TaxCalculationHistory(
                                rule_id=rule.id, rule_name=igst.rule_name, rate=rate,
                                base_amount=discounted_base, amount=igst_amt
                            ))
                else:
                    # Direct tax (VAT, OTHER, explicit CGST/SGST/IGST)
                    amt = round_money(discounted_base * (rate / Decimal("100.0")))
                    item = TaxBreakdownDTO(
                        rule_name=rule.name,
                        tax_type=rule.type,
                        rate=rate,
                        base_amount=discounted_base,
                        tax_amount=amt
                    )
                    breakdowns.append(item)

                    if record_history:
                        db.add(TaxCalculationHistory(
                            rule_id=rule.id, rule_name=rule.name, rate=rate,
                            base_amount=discounted_base, amount=amt
                        ))

        if record_history:
            db.commit()

        return breakdowns
    finally:
        if owns_session:
            db.close()

class TaxPreviewService(TaxPreviewPort):
    def preview(self, lines: List[TaxLineInputDTO], customer: CustomerDTO, as_of: date) -> List[TaxBreakdownDTO]:
        return compute_tax(lines, customer, as_of, record_history=False)
