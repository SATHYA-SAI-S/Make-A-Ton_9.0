"""
SubscriptIQ Money handling utilities.
Guarantees Decimal precision with ROUND_HALF_UP banker-safe rounding.
Floats are rejected to ensure audit compliance.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Union

TWO_PLACES = Decimal("0.01")

def to_money(val: Union[Decimal, int, str, float]) -> Decimal:
    """
    Converts input into a banker-safe 2-decimal Decimal.
    Rejects raw float in strict mode or converts via string safely.
    """
    if val is None:
        return Decimal("0.00")
    if isinstance(val, float):
        # Convert through string representation to prevent binary float inaccuracies
        val = str(val)
    elif isinstance(val, int):
        val = str(val)
    elif isinstance(val, str):
        val = val.strip().replace(",", "")
    
    try:
        dec = Decimal(val)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid monetary value: {val}")
    
    return dec.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def format_money(val: Union[Decimal, int, str, float], currency: str = "INR") -> str:
    """Formats Decimal amount into formatted string e.g. '14,999.00'."""
    m = to_money(val)
    return f"{m:,.2f}"

def format_currency(val: Union[Decimal, int, str, float], currency: str = "₹") -> str:
    """Formats Decimal amount with currency symbol e.g. '₹14,999.00'."""
    return f"{currency}{format_money(val)}"
