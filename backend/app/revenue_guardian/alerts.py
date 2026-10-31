"""
Alert Service & Triage Engine for Revenue Guardian.
Provides dashboard metrics, paginated alert filtering, and audited resolution actions.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.core.money import to_money
from backend.app.revenue_guardian.models import RiskAlert, RiskDetectionRun
from backend.app.audit.service import emit_audit_event


def get_guardian_dashboard(db: Session) -> Dict[str, Any]:
    """
    Returns aggregated metrics, open alerts count by severity/category,
    top prioritized anomalies, and recent detection runs.
    """
    open_alerts_query = db.query(RiskAlert).filter(RiskAlert.status == "OPEN")

    # Counts by severity
    critical_count = open_alerts_query.filter(RiskAlert.severity == "CRITICAL").count()
    high_count = open_alerts_query.filter(RiskAlert.severity == "HIGH").count()
    medium_count = open_alerts_query.filter(RiskAlert.severity == "MEDIUM").count()
    low_count = open_alerts_query.filter(RiskAlert.severity == "LOW").count()
    total_open = critical_count + high_count + medium_count + low_count

    # Total estimated impact across open alerts
    total_impact = db.query(func.coalesce(func.sum(RiskAlert.estimated_impact), 0)).filter(
        RiskAlert.status == "OPEN"
    ).scalar()
    total_impact_dec = to_money(Decimal(str(total_impact)))

    # Category breakdown
    cat_counts = (
        db.query(RiskAlert.category, func.count(RiskAlert.id), func.sum(RiskAlert.estimated_impact))
        .filter(RiskAlert.status == "OPEN")
        .group_by(RiskAlert.category)
        .all()
    )
    categories_summary = [
        {"category": c[0], "count": c[1], "estimated_impact": str(to_money(Decimal(str(c[2] or 0))))}
        for c in cat_counts
    ]

    # Top 10 prioritized open alerts
    top_alerts = (
        open_alerts_query.order_by(RiskAlert.score.desc(), RiskAlert.estimated_impact.desc())
        .limit(10)
        .all()
    )

    # Recent 5 detection runs
    recent_runs = (
        db.query(RiskDetectionRun)
        .order_by(RiskDetectionRun.started_at.desc())
        .limit(5)
        .all()
    )

    return {
        "summary": {
            "total_open_alerts": total_open,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "total_estimated_impact": str(total_impact_dec),
        },
        "categories_summary": categories_summary,
        "recent_runs": [
            {
                "id": r.id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "rules_run": r.rules_run,
                "alerts_created": r.alerts_created,
                "status": r.status,
                "error": r.error,
            }
            for r in recent_runs
        ],
        "top_alerts": [
            {
                "id": a.id,
                "rule_key": a.rule_key,
                "category": a.category,
                "severity": a.severity,
                "score": a.score,
                "customer_id": a.customer_id,
                "subscription_id": a.subscription_id,
                "invoice_id": a.invoice_id,
                "payment_id": a.payment_id,
                "detected_at": a.detected_at.isoformat() if a.detected_at else None,
                "estimated_impact": str(a.estimated_impact),
                "explanation": a.explanation,
                "suggested_action": a.suggested_action,
                "status": a.status,
            }
            for a in top_alerts
        ],
    }


def list_alerts(
    db: Session,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    rule_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> Dict[str, Any]:
    """
    Paginated alert listing with dynamic filters.
    """
    query = db.query(RiskAlert)

    if status and status.upper() != "ALL":
        query = query.filter(RiskAlert.status == status.upper())
    if severity and severity.upper() != "ALL":
        query = query.filter(RiskAlert.severity == severity.upper())
    if category and category.upper() != "ALL":
        query = query.filter(RiskAlert.category == category.upper())
    if rule_key and rule_key.upper() != "ALL":
        query = query.filter(RiskAlert.rule_key == rule_key.upper())
    if customer_id:
        query = query.filter(RiskAlert.customer_id == customer_id)

    total_count = query.count()
    offset = (page - 1) * page_size
    alerts = (
        query.order_by(RiskAlert.score.desc(), RiskAlert.detected_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": a.id,
                "rule_key": a.rule_key,
                "category": a.category,
                "severity": a.severity,
                "score": a.score,
                "customer_id": a.customer_id,
                "subscription_id": a.subscription_id,
                "invoice_id": a.invoice_id,
                "payment_id": a.payment_id,
                "detected_at": a.detected_at.isoformat() if a.detected_at else None,
                "estimated_impact": str(a.estimated_impact),
                "explanation": a.explanation,
                "suggested_action": a.suggested_action,
                "status": a.status,
                "acknowledged_by": a.acknowledged_by,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved_by": a.resolved_by,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "resolution_note": a.resolution_note,
            }
            for a in alerts
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
        },
    }


def get_alert_by_id(db: Session, alert_id: str) -> Optional[RiskAlert]:
    return db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()


def perform_alert_action(
    db: Session,
    alert_id: str,
    action: str,
    note: Optional[str] = None,
    actor_id: str = "staff"
) -> RiskAlert:
    """
    Executes an audited state change on a RiskAlert.
    Supported actions: ACKNOWLEDGE, RESOLVE, DISMISS.
    """
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise ValueError(f"RiskAlert {alert_id} not found.")

    now_utc = datetime.now(timezone.utc)
    before_state = {
        "status": alert.status,
        "acknowledged_by": alert.acknowledged_by,
        "resolved_by": alert.resolved_by,
        "resolution_note": alert.resolution_note,
    }

    action_upper = action.upper()
    if action_upper == "ACKNOWLEDGE":
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by = actor_id
        alert.acknowledged_at = now_utc
    elif action_upper == "RESOLVE":
        alert.status = "RESOLVED"
        alert.resolved_by = actor_id
        alert.resolved_at = now_utc
        alert.resolution_note = note or "Resolved anomaly."
    elif action_upper == "DISMISS":
        alert.status = "DISMISSED"
        alert.resolved_by = actor_id
        alert.resolved_at = now_utc
        alert.resolution_note = note or "Dismissed by operator."
    else:
        raise ValueError(f"Unsupported alert action: {action}. Use ACKNOWLEDGE, RESOLVE, or DISMISS.")

    db.commit()
    db.refresh(alert)

    # Emit audit log
    try:
        emit_audit_event(
            db=db,
            actor_id=actor_id,
            actor_role="staff",
            action=f"GUARDIAN_ALERT_{action_upper}",
            entity_type="risk_alert",
            entity_id=alert.id,
            before=before_state,
            after={
                "status": alert.status,
                "acknowledged_by": alert.acknowledged_by,
                "resolved_by": alert.resolved_by,
                "resolution_note": alert.resolution_note,
            },
            meta={"rule_key": alert.rule_key, "estimated_impact": str(alert.estimated_impact)},
        )
    except Exception:
        pass

    return alert
