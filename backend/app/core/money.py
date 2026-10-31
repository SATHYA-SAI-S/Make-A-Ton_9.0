"""
Money handling helper for SubscriptIQ.
Strict rule: All monetary calculations MUST use Decimal with ROUND_HALF_UP.
Floats are strictly rejected.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Union

TWO_PLACES = Decimal("0.01")


def to_decimal(val: Union[str, int, float, Decimal, None]) -> Decimal:
    """Safely converts an input to Decimal with 2 decimal places using ROUND_HALF_UP."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, float):
        val_str = str(val)
    elif isinstance(val, Decimal):
        val_str = str(val)
    elif isinstance(val, int):
        val_str = str(val)
    elif isinstance(val, str):
        val_str = val.strip().replace(",", "")
    else:
        raise TypeError(f"Cannot convert type {type(val)} to Decimal")

    try:
        d = Decimal(val_str)
        return d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid monetary value: {val}") from e


to_money = to_decimal


def round_money(val: Decimal) -> Decimal:
    """Banker-safe round to two decimal places."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def format_money(val: Union[Decimal, str, int, float, None], currency: str = "") -> str:
    """Formats Decimal as standard currency string e.g. '1250.00'."""
    d = to_decimal(val)
    return f"{d:,.2f}"


def format_currency(val: Union[Decimal, int, str, float, None], currency: str = "₹") -> str:
    """Formats Decimal amount with currency symbol e.g. '₹14,999.00'."""
    d = to_decimal(val)
    return f"{currency}{d:,.2f}"

