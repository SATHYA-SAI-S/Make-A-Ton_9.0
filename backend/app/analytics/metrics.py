"""
Financial Metric Calculations & Normalization Utilities.
Strictly implements docs/p3/metrics.md formulas.
Guarantees Decimal precision and bankers' ROUND_HALF_UP rounding.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union
from app.core.money import to_money

TWO_PLACES = Decimal("0.01")
DAYS_IN_YEAR = Decimal("365")
MONTHS_IN_YEAR = Decimal("12")
WEEKS_IN_YEAR = Decimal("52")

def normalize_mrr(price: Union[Decimal, str, int, float], frequency: str) -> Decimal:
    """
    Normalizes a subscription line price into an exact Monthly Recurring Revenue (MRR).
    Formulas:
    - MONTHLY: price
    - YEARLY: price / 12
    - WEEKLY: price * 52 / 12
    - DAILY: price * 365 / 12
    """
    p = to_money(price)
    freq = (frequency or "MONTHLY").upper().strip()

    if freq == "MONTHLY":
        return p
    elif freq == "YEARLY":
        return (p / MONTHS_IN_YEAR).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    elif freq == "WEEKLY":
        return ((p * WEEKS_IN_YEAR) / MONTHS_IN_YEAR).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    elif freq == "DAILY":
        return ((p * DAYS_IN_YEAR) / MONTHS_IN_YEAR).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    else:
        return p

def calculate_arr(mrr: Union[Decimal, str, int, float]) -> Decimal:
    """Calculates ARR = MRR * 12."""
    return (to_money(mrr) * MONTHS_IN_YEAR).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def calculate_arpc(mrr: Union[Decimal, str, int, float], active_customers: int) -> Decimal:
    """Calculates Average Revenue Per Customer (ARPC) = MRR / Active Customers."""
    if active_customers <= 0:
        return Decimal("0.00")
    return (to_money(mrr) / Decimal(str(active_customers))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def calculate_churn_rate(lost_customers: int, starting_customers: int) -> Decimal:
    """Calculates Customer Churn Rate % = (Lost / Starting) * 100."""
    if starting_customers <= 0:
        return Decimal("0.00")
    rate = (Decimal(str(lost_customers)) / Decimal(str(starting_customers))) * Decimal("100")
    return rate.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def calculate_collection_rate(collected_amount: Union[Decimal, str, int], due_amount: Union[Decimal, str, int]) -> Decimal:
    """Calculates Collection Rate % = (Collected / Due) * 100."""
    c = to_money(collected_amount)
    d = to_money(due_amount)
    if d <= Decimal("0.00"):
        return Decimal("100.00") if c > Decimal("0.00") else Decimal("0.00")
    rate = (c / d) * Decimal("100")
    return rate.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def calculate_pct_change(current: Union[Decimal, int, float], previous: Union[Decimal, int, float]) -> Decimal:
    """Computes percentage change between two reporting periods."""
    curr = to_money(current)
    prev = to_money(previous)
    if prev == Decimal("0.00"):
        return Decimal("100.00") if curr > Decimal("0.00") else Decimal("0.00")
    diff = ((curr - prev) / prev) * Decimal("100")
    return diff.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
