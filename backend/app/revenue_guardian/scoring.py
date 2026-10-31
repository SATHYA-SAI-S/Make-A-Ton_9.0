"""
Revenue Guardian Risk Scoring Engine.
Computes multi-factor risk scores (1-100) and severity ratings
based on estimated financial impact, days active, and category exposure.
"""
from decimal import Decimal
from typing import Tuple


def calculate_risk_score_and_severity(
    estimated_impact: Decimal,
    category: str,
    days_active: int = 0,
    base_boost: int = 0
) -> Tuple[int, str]:
    """
    Computes (score: int, severity: str) where:
    - score is bounded [1, 100]
    - severity is one of ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
    """
    impact_float = float(estimated_impact) if estimated_impact else 0.0

    # 1. Base score from financial exposure
    if impact_float >= 100000.0:
        base = 85
    elif impact_float >= 50000.0:
        base = 75
    elif impact_float >= 20000.0:
        base = 65
    elif impact_float >= 5000.0:
        base = 50
    elif impact_float >= 1000.0:
        base = 35
    elif impact_float > 0.0:
        base = 25
    else:
        base = 20

    # 2. Category sensitivity boost
    cat_boost = 0
    cat_upper = (category or "").upper()
    if cat_upper == "BILLING":
        cat_boost = 5
    elif cat_upper == "PAYMENT":
        cat_boost = 5
    elif cat_upper == "REVENUE":
        cat_boost = 8

    # 3. Aging severity escalation (+1 per 3 days up to max +15)
    age_boost = min(days_active // 3, 15)

    total_score = base + cat_boost + age_boost + base_boost
    total_score = max(1, min(100, total_score))

    # 4. Map to standardized severity
    if total_score >= 80 or impact_float >= 50000.0:
        severity = "CRITICAL"
    elif total_score >= 60 or impact_float >= 15000.0:
        severity = "HIGH"
    elif total_score >= 35 or impact_float >= 5000.0:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return total_score, severity
