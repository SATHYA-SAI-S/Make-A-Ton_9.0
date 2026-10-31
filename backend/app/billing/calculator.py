"""
Pricing calculator for SubscriptIQ billing engine.
Pure logic component - NO database access.
Strictly relies on Decimal with ROUND_HALF_UP.
"""
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.app.core.money import to_decimal, round_money
from backend.app.shared.dto import TaxBreakdownDTO

class CalculatedLineItem(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    description: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    discounted_base: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal

class PricingCalculationResult(BaseModel):
    lines: List[CalculatedLineItem]
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    tax_breakdowns: List[TaxBreakdownDTO] = []

def calculate_pricing(
    lines_input: List[Dict[str, Any]],
    product_discounts: Optional[Dict[str, Decimal]] = None,
    subscription_discount: Decimal = Decimal("0.00"),
    tax_rate: Decimal = Decimal("0.00"),
    tax_breakdowns: Optional[List[TaxBreakdownDTO]] = None
) -> PricingCalculationResult:
    """
    Computes pricing strictly according to the specified formula:
    1. Line Amount = quantity * unit_price
    2. Apply Product Discounts
    3. Apply Subscription-wide Discounts proportionally across lines
    4. Compute Tax on discounted amount
    5. Line Total = Discounted Base + Tax Amount
    6. Overall Total = Subtotal - Total Discounts + Total Tax
    """
    product_discounts = product_discounts or {}
    subscription_discount = round_money(to_decimal(subscription_discount))
    tax_rate = to_decimal(tax_rate)

    raw_lines = []
    initial_subtotal = Decimal("0.00")

    # Step 1: Calculate raw line amounts
    for line in lines_input:
        qty = int(line.get("quantity", 1))
        unit_price = round_money(to_decimal(line["unit_price"]))
        line_sub = round_money(unit_price * Decimal(qty))
        initial_subtotal += line_sub
        raw_lines.append({
            "product_id": str(line.get("product_id", "")),
            "variant_id": line.get("variant_id"),
            "description": line.get("description", "Subscription line item"),
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": line_sub,
            "product_discount": Decimal("0.00"),
            "subscription_discount": Decimal("0.00"),
            "total_discount": Decimal("0.00"),
            "discounted_base": line_sub
        })

    # Step 2: Apply product discounts
    subtotal_after_prod_discounts = Decimal("0.00")
    for r in raw_lines:
        p_id = r["product_id"]
        if p_id in product_discounts:
            p_disc = min(r["subtotal"], round_money(to_decimal(product_discounts[p_id])))
            r["product_discount"] = p_disc
            r["discounted_base"] = round_money(r["subtotal"] - p_disc)
        subtotal_after_prod_discounts += r["discounted_base"]

    # Step 3: Apply subscription discount proportionally across lines based on remaining base
    if subscription_discount > Decimal("0.00") and subtotal_after_prod_discounts > Decimal("0.00"):
        actual_sub_disc_to_distribute = min(subtotal_after_prod_discounts, subscription_discount)
        distributed_so_far = Decimal("0.00")
        
        for idx, r in enumerate(raw_lines):
            if idx == len(raw_lines) - 1:
                # Assign remainder to last line to prevent penny drift
                line_sub_disc = round_money(actual_sub_disc_to_distribute - distributed_so_far)
            else:
                ratio = r["discounted_base"] / subtotal_after_prod_discounts
                line_sub_disc = round_money(actual_sub_disc_to_distribute * ratio)
                distributed_so_far += line_sub_disc
            
            line_sub_disc = min(r["discounted_base"], line_sub_disc)
            r["subscription_discount"] = line_sub_disc
            r["discounted_base"] = round_money(r["discounted_base"] - line_sub_disc)

    # Step 4 & 5: Calculate taxes and line totals
    total_subtotal = Decimal("0.00")
    total_discounts = Decimal("0.00")
    total_tax = Decimal("0.00")
    calculated_lines: List[CalculatedLineItem] = []

    for r in raw_lines:
        tot_line_disc = round_money(r["product_discount"] + r["subscription_discount"])
        disc_base = round_money(max(Decimal("0.00"), r["subtotal"] - tot_line_disc))
        
        # Calculate line tax
        line_tax = round_money(disc_base * (tax_rate / Decimal("100.00")))
        line_final = round_money(disc_base + line_tax)

        total_subtotal += r["subtotal"]
        total_discounts += tot_line_disc
        total_tax += line_tax

        calculated_lines.append(CalculatedLineItem(
            product_id=r["product_id"],
            variant_id=r["variant_id"],
            description=r["description"],
            quantity=r["quantity"],
            unit_price=r["unit_price"],
            subtotal=r["subtotal"],
            discount_amount=tot_line_disc,
            discounted_base=disc_base,
            tax_rate=tax_rate,
            tax_amount=line_tax,
            line_total=line_final
        ))

    overall_total = round_money(total_subtotal - total_discounts + total_tax)

    return PricingCalculationResult(
        lines=calculated_lines,
        subtotal=total_subtotal,
        discount_total=total_discounts,
        tax_total=total_tax,
        total=overall_total,
        tax_breakdowns=tax_breakdowns or []
    )
