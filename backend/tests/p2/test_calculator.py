from decimal import Decimal
import pytest
from backend.app.billing.calculator import calculate_pricing

def test_single_line_no_discount_no_tax():
    lines = [{"product_id": "p1", "quantity": 3, "unit_price": "150.00"}]
    res = calculate_pricing(lines)
    assert res.subtotal == Decimal("450.00")
    assert res.discount_total == Decimal("0.00")
    assert res.tax_total == Decimal("0.00")
    assert res.total == Decimal("450.00")
    assert len(res.lines) == 1
    assert res.lines[0].line_total == Decimal("450.00")

def test_product_discount_and_tax():
    # 2 units of 1000.00 = 2000.00
    # Product discount = 200.00 -> Base = 1800.00
    # Tax 18% on 1800.00 = 324.00
    # Total = 1800.00 + 324.00 = 2124.00
    lines = [{"product_id": "p1", "quantity": 2, "unit_price": "1000.00"}]
    res = calculate_pricing(
        lines,
        product_discounts={"p1": Decimal("200.00")},
        tax_rate=Decimal("18.00")
    )
    assert res.subtotal == Decimal("2000.00")
    assert res.discount_total == Decimal("200.00")
    assert res.tax_total == Decimal("324.00")
    assert res.total == Decimal("2124.00")

def test_subscription_discount_distributed_across_lines():
    # Line 1: 1000.00 (50%)
    # Line 2: 1000.00 (50%)
    # Total subtotal: 2000.00
    # Subscription discount: 500.00 (split 250.00 each)
    # Tax: 10%
    lines = [
        {"product_id": "p1", "quantity": 1, "unit_price": "1000.00"},
        {"product_id": "p2", "quantity": 1, "unit_price": "1000.00"}
    ]
    res = calculate_pricing(
        lines,
        subscription_discount=Decimal("500.00"),
        tax_rate=Decimal("10.00")
    )
    assert res.subtotal == Decimal("2000.00")
    assert res.discount_total == Decimal("500.00")
    # Base after discount = 1500.00 (750.00 each)
    # Tax = 10% of 1500.00 = 150.00 (75.00 each)
    assert res.tax_total == Decimal("150.00")
    assert res.total == Decimal("1650.00")
    assert res.lines[0].discount_amount == Decimal("250.00")
    assert res.lines[1].discount_amount == Decimal("250.00")

def test_one_hundred_percent_discount():
    lines = [{"product_id": "p1", "quantity": 1, "unit_price": "100.00"}]
    res = calculate_pricing(
        lines,
        product_discounts={"p1": Decimal("100.00")},
        tax_rate=Decimal("18.00")
    )
    assert res.subtotal == Decimal("100.00")
    assert res.discount_total == Decimal("100.00")
    assert res.tax_total == Decimal("0.00")
    assert res.total == Decimal("0.00")

def test_rounding_edge_case_penny_remainder():
    # Line 1: 33.33
    # Line 2: 33.33
    # Line 3: 33.34
    # Subtotal: 100.00
    # Subscription discount: 10.00 (split 3.33, 3.33, 3.34)
    lines = [
        {"product_id": "p1", "quantity": 1, "unit_price": "33.33"},
        {"product_id": "p2", "quantity": 1, "unit_price": "33.33"},
        {"product_id": "p3", "quantity": 1, "unit_price": "33.34"}
    ]
    res = calculate_pricing(lines, subscription_discount=Decimal("10.00"))
    assert res.discount_total == Decimal("10.00")
    assert sum(l.discount_amount for l in res.lines) == Decimal("10.00")
    assert res.total == Decimal("90.00")
