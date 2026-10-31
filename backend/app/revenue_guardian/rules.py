"""
Autonomous Risk Detection Rules Engine for Revenue Guardian.
Implements the 8 core revenue risk detectors:
1. Missed Billing (ACTIVE subscription due with no invoice)
2. Duplicate Billing (Multiple active invoices for same subscription and period)
3. Expired Discount (Discount applied after promotion/rule expiration)
4. Payment Mismatch (Allocation mismatch with payment amount or invoice balance)
5. Renewal Risk (Subscription expiring soon with no renewal confirmed)
6. Overdue Risk (Invoice past due date with aging severity escalation)
7. Pricing Anomaly (Invoice line unit price discrepancy against subscription lines)
8. Revenue Leakage (Actual recurring billings significantly lower than expected MRR)
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.money import to_money, ROUND_HALF_UP
from app.finance.models import (
    Customer,
    Plan,
    Subscription,
    SubscriptionLine,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from app.finance.overview import normalize_mrr
from app.revenue_guardian.scoring import calculate_risk_score_and_severity


@dataclass
class RiskFinding:
    rule_key: str
    category: str
    severity: str
    score: int
    customer_id: Optional[str]
    subscription_id: Optional[str]
    invoice_id: Optional[str]
    payment_id: Optional[str]
    estimated_impact: Decimal
    explanation: str
    suggested_action: str
    fingerprint: str


# ---------------------------------------------------------
# Rule 1: Missed Billing
# ---------------------------------------------------------
def detect_missed_billing(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects ACTIVE subscriptions where the billing date has arrived/passed,
    but no corresponding invoice has been generated.
    """
    today = as_of or date.today()
    findings: List[RiskFinding] = []

    # Find ACTIVE subscriptions with next_billing_date <= today or start_date <= today - 30d
    subs = db.query(Subscription).filter(
        Subscription.status == "ACTIVE",
        or_(
            and_(Subscription.next_billing_date.isnot(None), Subscription.next_billing_date <= today),
            and_(Subscription.next_billing_date.is_(None), Subscription.start_date <= today - timedelta(days=30))
        )
    ).all()

    for s in subs:
        due_date = s.next_billing_date or (s.start_date + timedelta(days=30))
        # Check if an invoice was generated around or after this due date
        inv_exists = db.query(Invoice).filter(
            Invoice.subscription_id == s.id,
            Invoice.status != "CANCELLED",
            Invoice.invoice_date >= due_date - timedelta(days=5)
        ).first()

        if not inv_exists:
            monthly_val = normalize_mrr(s.plan.price, s.plan.billing_frequency) if s.plan else Decimal("0.00")
            impact = to_money(monthly_val)
            days_past = (today - due_date).days
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="BILLING",
                days_active=days_past,
                base_boost=10
            )
            fingerprint = f"MISSED_BILLING:sub:{s.id}:{due_date.isoformat()}"

            findings.append(RiskFinding(
                rule_key="MISSED_BILLING",
                category="BILLING",
                severity=severity,
                score=score,
                customer_id=s.customer_id,
                subscription_id=s.id,
                invoice_id=None,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"ACTIVE subscription {s.number} was due for billing on {due_date.isoformat()} ({days_past} days ago), but no invoice was generated.",
                suggested_action=f"Generate billing run invoice for subscription {s.number} or update next billing date.",
                fingerprint=fingerprint
            ))

    return findings


# ---------------------------------------------------------
# Rule 2: Duplicate Billing
# ---------------------------------------------------------
def detect_duplicate_billing(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects multiple non-cancelled invoices generated for the same subscription
    in the same billing period or invoice date.
    """
    findings: List[RiskFinding] = []

    # Query invoices grouped by subscription_id and billing_period_id/invoice_date
    invoices = db.query(Invoice).filter(
        Invoice.subscription_id.isnot(None),
        Invoice.status != "CANCELLED"
    ).all()

    # Bucket by (subscription_id, billing_period_id or invoice_date)
    grouped: Dict[str, List[Invoice]] = {}
    for inv in invoices:
        period_key = inv.billing_period_id or inv.invoice_date.strftime("%Y-%m")
        key = f"{inv.subscription_id}::{period_key}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(inv)

    for key, inv_list in grouped.items():
        if len(inv_list) > 1:
            sub_id, period_key = key.split("::")
            # Calculate impact as sum of all duplicate invoices after the first
            sorted_invs = sorted(inv_list, key=lambda x: x.created_at)
            duplicate_invs = sorted_invs[1:]
            impact = sum([d.total for d in duplicate_invs])
            impact = to_money(impact)

            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="BILLING",
                base_boost=15
            )
            inv_nums = ", ".join([i.number for i in inv_list])
            fingerprint = f"DUPLICATE_BILLING:sub:{sub_id}:{period_key}"

            findings.append(RiskFinding(
                rule_key="DUPLICATE_BILLING",
                category="BILLING",
                severity=severity,
                score=score,
                customer_id=inv_list[0].customer_id,
                subscription_id=sub_id,
                invoice_id=duplicate_invs[0].id,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"Found {len(inv_list)} non-cancelled invoices ({inv_nums}) for subscription {sub_id} in period {period_key}.",
                suggested_action=f"Review and cancel duplicate invoice(s) ({', '.join([d.number for d in duplicate_invs])}) before payment collection.",
                fingerprint=fingerprint
            ))

    return findings


# ---------------------------------------------------------
# Rule 3: Expired Discount
# ---------------------------------------------------------
def detect_expired_discounts(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects invoices with active discounts applied where the promotion
    or plan availability window expired before the invoice date.
    """
    findings: List[RiskFinding] = []

    # Find invoices with discounts
    discounted_invoices = db.query(Invoice).filter(
        Invoice.discount_total > Decimal("0.00"),
        Invoice.status != "CANCELLED"
    ).all()

    for inv in discounted_invoices:
        # Check associated subscription's plan
        is_expired = False
        if inv.subscription_id:
            sub = db.query(Subscription).filter(Subscription.id == inv.subscription_id).first()
            if sub and sub.plan and sub.plan.available_to:
                if inv.invoice_date > sub.plan.available_to:
                    is_expired = True

        if is_expired:
            impact = to_money(inv.discount_total)
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="REVENUE",
                base_boost=5
            )
            fingerprint = f"EXPIRED_DISCOUNT:inv:{inv.id}"

            findings.append(RiskFinding(
                rule_key="EXPIRED_DISCOUNT",
                category="REVENUE",
                severity=severity,
                score=score,
                customer_id=inv.customer_id,
                subscription_id=inv.subscription_id,
                invoice_id=inv.id,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"Invoice {inv.number} contains discount ₹{inv.discount_total} applied after promotional rule expiry date.",
                suggested_action=f"Verify discount eligibility for invoice {inv.number} and issue debit adjustment note if inappropriate.",
                fingerprint=fingerprint
            ))

    return findings


# ---------------------------------------------------------
# Rule 4: Payment Mismatch
# ---------------------------------------------------------
def detect_payment_mismatches(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects:
    a) Payments whose amount does not equal the sum of their recorded allocations.
    b) Invoices whose amount_paid does not equal the sum of allocations pointing to them.
    """
    findings: List[RiskFinding] = []

    # 1. Payment allocation sums
    payments = db.query(Payment).filter(Payment.status == "RECORDED").all()
    for p in payments:
        alloc_sum = db.query(func.coalesce(func.sum(PaymentAllocation.amount), 0)).filter(
            PaymentAllocation.payment_id == p.id
        ).scalar()
        alloc_dec = Decimal(str(alloc_sum))

        diff = abs(p.amount - alloc_dec)
        if diff > Decimal("0.01") and len(p.allocations) > 0:
            impact = to_money(diff)
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="PAYMENT",
                base_boost=10
            )
            fingerprint = f"PAYMENT_MISMATCH:pmt:{p.id}"

            findings.append(RiskFinding(
                rule_key="PAYMENT_MISMATCH",
                category="PAYMENT",
                severity=severity,
                score=score,
                customer_id=p.customer_id,
                subscription_id=None,
                invoice_id=None,
                payment_id=p.id,
                estimated_impact=impact,
                explanation=f"Payment {p.reference or p.id} recorded amount ₹{p.amount} differs from total allocated amount ₹{alloc_dec} (Discrepancy: ₹{impact}).",
                suggested_action=f"Reconcile payment allocations for payment reference {p.reference or p.id}.",
                fingerprint=fingerprint
            ))

    # 2. Invoice amount_paid vs allocation sums
    invoices = db.query(Invoice).filter(
        Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID", "PAID"]),
        Invoice.amount_paid > Decimal("0.00")
    ).all()
    for inv in invoices:
        alloc_sum = db.query(func.coalesce(func.sum(PaymentAllocation.amount), 0)).filter(
            PaymentAllocation.invoice_id == inv.id
        ).scalar()
        alloc_dec = Decimal(str(alloc_sum))

        diff = abs(inv.amount_paid - alloc_dec)
        if diff > Decimal("0.01"):
            impact = to_money(diff)
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="PAYMENT",
                base_boost=10
            )
            fingerprint = f"PAYMENT_MISMATCH:inv:{inv.id}"

            findings.append(RiskFinding(
                rule_key="PAYMENT_MISMATCH",
                category="PAYMENT",
                severity=severity,
                score=score,
                customer_id=inv.customer_id,
                subscription_id=inv.subscription_id,
                invoice_id=inv.id,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"Invoice {inv.number} amount_paid ₹{inv.amount_paid} differs from total payment allocations ₹{alloc_dec} (Discrepancy: ₹{impact}).",
                suggested_action=f"Verify payments and recalculate balance for invoice {inv.number}.",
                fingerprint=fingerprint
            ))

    return findings


# ---------------------------------------------------------
# Rule 5: Renewal Risk
# ---------------------------------------------------------
def detect_renewal_risk(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects subscriptions approaching expiry within 30 days without auto-renewal
    or confirmed renewal successor.
    """
    today = as_of or date.today()
    findings: List[RiskFinding] = []
    window_end = today + timedelta(days=30)

    expiring_subs = db.query(Subscription).filter(
        Subscription.status == "ACTIVE",
        Subscription.expiry_date.isnot(None),
        Subscription.expiry_date >= today,
        Subscription.expiry_date <= window_end
    ).all()

    for s in expiring_subs:
        days_left = (s.expiry_date - today).days
        # Check if plan does not allow renewal or no renewal subscription
        has_renewal_risk = False
        if s.plan and not s.plan.allow_renewal:
            has_renewal_risk = True
        else:
            # Check if another subscription exists starting at expiry_date
            successor = db.query(Subscription).filter(
                Subscription.customer_id == s.customer_id,
                Subscription.id != s.id,
                Subscription.start_date >= s.expiry_date
            ).first()
            if not successor:
                has_renewal_risk = True

        if has_renewal_risk:
            # Impact is the normalized annual contract value at risk
            annual_val = normalize_mrr(s.plan.price, s.plan.billing_frequency) * Decimal("12.00") if s.plan else Decimal("0.00")
            impact = to_money(annual_val)
            urgency_boost = 15 if days_left <= 7 else (5 if days_left <= 15 else 0)
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="SUBSCRIPTION",
                base_boost=urgency_boost
            )
            fingerprint = f"RENEWAL_RISK:sub:{s.id}:{s.expiry_date.isoformat()}"

            findings.append(RiskFinding(
                rule_key="RENEWAL_RISK",
                category="SUBSCRIPTION",
                severity=severity,
                score=score,
                customer_id=s.customer_id,
                subscription_id=s.id,
                invoice_id=None,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"Subscription {s.number} expires on {s.expiry_date.isoformat()} ({days_left} days remaining) with no confirmed renewal contract.",
                suggested_action=f"Initiate renewal outreach for account {s.customer.name if s.customer else s.customer_id} to prevent contract churn.",
                fingerprint=fingerprint
            ))

    return findings


# ---------------------------------------------------------
# Rule 6: Overdue Risk
# ---------------------------------------------------------
def detect_overdue_risk(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects invoices past due date with remaining balance.
    Escalates severity and priority score with age and outstanding amount.
    """
    today = as_of or date.today()
    findings: List[RiskFinding] = []

    overdue_invoices = db.query(Invoice).filter(
        Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
        Invoice.balance > Decimal("0.00"),
        Invoice.due_date < today
    ).all()

    for inv in overdue_invoices:
        days_overdue = (today - inv.due_date).days
        impact = to_money(inv.balance)

        # Base escalation based on age brackets
        if days_overdue > 90:
            bracket_boost = 25
        elif days_overdue > 60:
            bracket_boost = 18
        elif days_overdue > 30:
            bracket_boost = 10
        else:
            bracket_boost = 0

        score, severity = calculate_risk_score_and_severity(
            estimated_impact=impact,
            category="BILLING",
            days_active=days_overdue,
            base_boost=bracket_boost
        )
        fingerprint = f"OVERDUE_RISK:inv:{inv.id}:{inv.due_date.isoformat()}"

        findings.append(RiskFinding(
            rule_key="OVERDUE_RISK",
            category="BILLING",
            severity=severity,
            score=score,
            customer_id=inv.customer_id,
            subscription_id=inv.subscription_id,
            invoice_id=inv.id,
            payment_id=None,
            estimated_impact=impact,
            explanation=f"Invoice {inv.number} has an unpaid balance of ₹{inv.balance} and is {days_overdue} days overdue (Due date: {inv.due_date.isoformat()}).",
            suggested_action=f"Issue dunning reminder notice or follow up with customer {inv.customer_id} for overdue payment.",
            fingerprint=fingerprint
        ))

    return findings


# ---------------------------------------------------------
# Rule 7: Pricing Anomaly
# ---------------------------------------------------------
def detect_pricing_anomalies(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects invoice lines where unit price differs unexpectedly from
    the subscription line snapshot or catalog price.
    """
    findings: List[RiskFinding] = []

    # Find invoice lines linked to subscriptions
    invoice_lines = db.query(InvoiceLine).join(Invoice).filter(
        Invoice.subscription_id.isnot(None),
        Invoice.status != "CANCELLED"
    ).all()

    for il in invoice_lines:
        inv = il.invoice
        # Compare with subscription line or plan price
        sub = db.query(Subscription).filter(Subscription.id == inv.subscription_id).first()
        if not sub:
            continue

        expected_unit_price = None
        # Check subscription lines first
        sub_line = db.query(SubscriptionLine).filter(
            SubscriptionLine.subscription_id == sub.id,
            SubscriptionLine.product_id == il.product_id
        ).first()
        if sub_line:
            expected_unit_price = sub_line.unit_price
        elif sub.plan:
            expected_unit_price = sub.plan.price

        if expected_unit_price is not None:
            diff = abs(il.unit_price - expected_unit_price)
            if diff > Decimal("0.01"):
                line_impact = to_money(diff * Decimal(str(il.quantity)))
                score, severity = calculate_risk_score_and_severity(
                    estimated_impact=line_impact,
                    category="REVENUE",
                    base_boost=12
                )
                fingerprint = f"PRICING_ANOMALY:inv_line:{il.id}"

                findings.append(RiskFinding(
                    rule_key="PRICING_ANOMALY",
                    category="REVENUE",
                    severity=severity,
                    score=score,
                    customer_id=inv.customer_id,
                    subscription_id=sub.id,
                    invoice_id=inv.id,
                    payment_id=None,
                    estimated_impact=line_impact,
                    explanation=f"Invoice {inv.number} line for {il.product_id} billed at ₹{il.unit_price}, differing from expected price ₹{expected_unit_price} (Discrepancy: ₹{line_impact}).",
                    suggested_action=f"Verify pricing configuration for invoice {inv.number} and align with subscription terms.",
                    fingerprint=fingerprint
                ))

    return findings


# ---------------------------------------------------------
# Rule 8: Revenue Leakage
# ---------------------------------------------------------
def detect_revenue_leakage(db: Session, as_of: Optional[date] = None) -> List[RiskFinding]:
    """
    Detects active customers where actual billed revenue over the last 30 days
    is significantly lower than expected monthly MRR (> 15% discrepancy).
    """
    today = as_of or date.today()
    findings: List[RiskFinding] = []
    thirty_days_ago = today - timedelta(days=30)

    # Group active subscriptions by customer
    customers = db.query(Customer).filter(Customer.status == "ACTIVE").all()

    for c in customers:
        active_subs = [s for s in c.subscriptions if s.status == "ACTIVE" and s.start_date <= thirty_days_ago]
        if not active_subs:
            continue

        expected_mrr = sum([
            normalize_mrr(s.plan.price, s.plan.billing_frequency)
            for s in active_subs if s.plan
        ])

        if expected_mrr < Decimal("500.00"):
            continue

        # Invoices billed in the last 30 days
        actual_invoiced = db.query(func.coalesce(func.sum(Invoice.total), 0)).filter(
            Invoice.customer_id == c.id,
            Invoice.status != "CANCELLED",
            Invoice.invoice_date >= thirty_days_ago
        ).scalar()
        actual_dec = Decimal(str(actual_invoiced))

        # Discrepancy > 15%
        discrepancy = expected_mrr - actual_dec
        if discrepancy > (expected_mrr * Decimal("0.15")):
            impact = to_money(discrepancy)
            score, severity = calculate_risk_score_and_severity(
                estimated_impact=impact,
                category="REVENUE",
                base_boost=20
            )
            period_str = today.strftime("%Y-%m")
            fingerprint = f"REVENUE_LEAKAGE:cust:{c.id}:{period_str}"

            findings.append(RiskFinding(
                rule_key="REVENUE_LEAKAGE",
                category="REVENUE",
                severity=severity,
                score=score,
                customer_id=c.id,
                subscription_id=active_subs[0].id if active_subs else None,
                invoice_id=None,
                payment_id=None,
                estimated_impact=impact,
                explanation=f"Customer {c.name} expected recurring charges of ₹{to_money(expected_mrr)}/month, but only ₹{to_money(actual_dec)} was billed in the last 30 days (Unbilled Leakage: ₹{impact}).",
                suggested_action=f"Audit subscription line items for customer {c.name} and issue supplemental recurring invoice.",
                fingerprint=fingerprint
            ))

    return findings


# Registry of all 8 rules
ALL_DETECTION_RULES = [
    ("MISSED_BILLING", detect_missed_billing),
    ("DUPLICATE_BILLING", detect_duplicate_billing),
    ("EXPIRED_DISCOUNT", detect_expired_discounts),
    ("PAYMENT_MISMATCH", detect_payment_mismatches),
    ("RENEWAL_RISK", detect_renewal_risk),
    ("OVERDUE_RISK", detect_overdue_risk),
    ("PRICING_ANOMALY", detect_pricing_anomalies),
    ("REVENUE_LEAKAGE", detect_revenue_leakage),
]
