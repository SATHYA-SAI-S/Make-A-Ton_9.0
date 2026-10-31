"""
Autonomous Detection Engine for Revenue Guardian.
Executes risk detection cycles across all 8 rules, enforcing strict idempotency
via deterministic fingerprints and non-destructive read-only analysis of financial ledgers.
"""
from datetime import datetime, timezone, date
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.revenue_guardian.models import RiskAlert, RiskDetectionRun
from app.revenue_guardian.rules import ALL_DETECTION_RULES, RiskFinding


def run_detection_cycle(
    db: Session,
    rule_keys: Optional[List[str]] = None,
    as_of: Optional[date] = None
) -> RiskDetectionRun:
    """
    Executes a complete risk detection run across registered anomaly detection rules.
    Guarantees:
    1. Idempotency: re-running never creates duplicate alerts for the same fingerprint.
    2. Resolution persistence: resolved or dismissed alerts maintain their status.
    3. Strict financial isolation: Never modifies customers, subscriptions, invoices, or payments.
    """
    run_record = RiskDetectionRun(
        id=str(uuid.uuid4()),
        started_at=datetime.now(timezone.utc),
        status="RUNNING",
        rules_run=0,
        alerts_created=0,
    )
    db.add(run_record)
    db.commit()

    # Filter rules to run
    rules_to_run = ALL_DETECTION_RULES
    if rule_keys:
        rule_keys_set = set(rule_keys)
        rules_to_run = [r for r in ALL_DETECTION_RULES if r[0] in rule_keys_set]

    alerts_created_count = 0
    now_utc = datetime.now(timezone.utc)

    try:
        for rule_name, rule_fn in rules_to_run:
            run_record.rules_run += 1
            findings: List[RiskFinding] = rule_fn(db=db, as_of=as_of)

            for f in findings:
                # Query existing alert by unique fingerprint
                existing_alert = db.query(RiskAlert).filter(
                    RiskAlert.fingerprint == f.fingerprint
                ).first()

                if existing_alert:
                    # Update detection timestamp and refreshed score, but preserve RESOLVED/DISMISSED status
                    existing_alert.detected_at = now_utc
                    existing_alert.score = f.score
                    existing_alert.severity = f.severity
                    existing_alert.estimated_impact = f.estimated_impact
                    existing_alert.explanation = f.explanation
                    existing_alert.suggested_action = f.suggested_action
                else:
                    # Create new alert
                    new_alert = RiskAlert(
                        id=str(uuid.uuid4()),
                        rule_key=f.rule_key,
                        category=f.category,
                        severity=f.severity,
                        score=f.score,
                        customer_id=f.customer_id,
                        subscription_id=f.subscription_id,
                        invoice_id=f.invoice_id,
                        payment_id=f.payment_id,
                        detected_at=now_utc,
                        estimated_impact=f.estimated_impact,
                        explanation=f.explanation,
                        suggested_action=f.suggested_action,
                        status="OPEN",
                        fingerprint=f.fingerprint
                    )
                    db.add(new_alert)
                    alerts_created_count += 1

        run_record.alerts_created = alerts_created_count
        run_record.finished_at = datetime.now(timezone.utc)
        run_record.status = "SUCCESS"
        db.commit()
        db.refresh(run_record)
        return run_record

    except Exception as exc:
        db.rollback()
        run_record.status = "FAILED"
        run_record.finished_at = datetime.now(timezone.utc)
        run_record.error = str(exc)
        db.add(run_record)
        db.commit()
        raise exc
