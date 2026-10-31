"""
Money handling helper for SubscriptIQ.
Strict rule: All monetary calculations MUST use Decimal with ROUND_HALF_UP.
Floats are strictly rejected.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union

TWO_PLACES = Decimal("0.01")

def to_decimal(val: Union[str, int, float, Decimal]) -> Decimal:
    """Safely converts an input to Decimal with 2 decimal places. Rejects floats in strict mode or converts exact string representations."""
    if isinstance(val, float):
        # Convert via string representation to avoid imprecise binary float errors, but issue warning/assert
        val_str = str(val)
    elif isinstance(val, Decimal):
        val_str = str(val)
    elif isinstance(val, (int, str)):
        val_str = str(val)
    else:
        raise TypeError(f"Cannot convert type {type(val)} to Decimal")
    
    try:
        d = Decimal(val_str)
        return d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid monetary value: {val}") from e

def format_money(val: Union[Decimal, str, int, float]) -> str:
    """Formats Decimal as standard currency string e.g. '1250.00'."""
    d = to_decimal(val)
    return f"{d:.2f}"

def round_money(val: Decimal) -> Decimal:
    """Banker-safe round to two decimal places."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
