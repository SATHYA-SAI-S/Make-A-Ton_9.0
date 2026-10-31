"""
Revenue Guardian REST Router.
Provides dashboard, alert triage, detection triggers, and resolution action endpoints
under /api/v1/guardian.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import UserClaims, require_roles
from app.revenue_guardian.alerts import (
    get_guardian_dashboard,
    list_alerts,
    get_alert_by_id,
    perform_alert_action,
)
from app.revenue_guardian.detection import run_detection_cycle
from app.revenue_guardian.models import RiskDetectionRun

router = APIRouter(tags=["Revenue Guardian"])


class AlertActionRequest(BaseModel):
    action: str = Field(..., description="Action to take: ACKNOWLEDGE, RESOLVE, or DISMISS")
    note: Optional[str] = Field(None, description="Resolution or dismissal notes")


class RunDetectionRequest(BaseModel):
    rules: Optional[List[str]] = Field(None, description="Optional subset of rule keys to execute")


@router.get("/dashboard", summary="Revenue Guardian Overview Dashboard")
def get_dashboard(
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Returns summary statistics, open anomaly counts by severity,
    top prioritized anomalies, and recent detection runs.
    """
    return get_guardian_dashboard(db=db)


@router.get("/alerts", summary="List Filtered Risk Alerts")
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED, ALL)"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, ALL)"),
    category: Optional[str] = Query(None, description="Filter by category (BILLING, PAYMENT, SUBSCRIPTION, REVENUE, ALL)"),
    rule_key: Optional[str] = Query(None, description="Filter by rule key"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Returns paginated risk alerts with multi-dimensional filtering.
    """
    return list_alerts(
        db=db,
        status=status,
        severity=severity,
        category=category,
        rule_key=rule_key,
        customer_id=customer_id,
        page=page,
        page_size=page_size,
    )


@router.get("/alerts/{alert_id}", summary="Get Alert Detail")
def get_alert_detail(
    alert_id: str,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    alert = get_alert_by_id(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {
        "id": alert.id,
        "rule_key": alert.rule_key,
        "category": alert.category,
        "severity": alert.severity,
        "score": alert.score,
        "customer_id": alert.customer_id,
        "subscription_id": alert.subscription_id,
        "invoice_id": alert.invoice_id,
        "payment_id": alert.payment_id,
        "detected_at": alert.detected_at.isoformat() if alert.detected_at else None,
        "estimated_impact": str(alert.estimated_impact),
        "explanation": alert.explanation,
        "suggested_action": alert.suggested_action,
        "status": alert.status,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_by": alert.resolved_by,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolution_note": alert.resolution_note,
    }


@router.post("/alerts/{alert_id}/action", summary="Execute Alert Triage / Resolution Action")
def execute_alert_action(
    alert_id: str,
    req: AlertActionRequest,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Executes ACKNOWLEDGE, RESOLVE, or DISMISS action on a detected anomaly.
    Every action is recorded in the immutable audit ledger.
    """
    try:
        actor = getattr(current_user, "id", getattr(current_user, "sub", "staff"))
        alert = perform_alert_action(
            db=db,
            alert_id=alert_id,
            action=req.action,
            note=req.note,
            actor_id=actor,
        )
        return {
            "message": f"Alert {alert.id} status updated to {alert.status}",
            "id": alert.id,
            "status": alert.status,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolution_note": alert.resolution_note,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run", summary="Trigger Immediate Risk Detection Cycle")
def trigger_detection_run(
    req: Optional[RunDetectionRequest] = None,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Executes autonomous risk detection cycle across all 8 rules.
    Detects missed billings, duplicate invoices, expired discounts, payment mismatches,
    renewal risks, overdue receivables, pricing anomalies, and revenue leakage.
    """
    rule_keys = req.rules if req else None
    run_record = run_detection_cycle(db=db, rule_keys=rule_keys)
    return {
        "id": run_record.id,
        "status": run_record.status,
        "rules_run": run_record.rules_run,
        "alerts_created": run_record.alerts_created,
        "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
        "finished_at": run_record.finished_at.isoformat() if run_record.finished_at else None,
    }


@router.get("/runs", summary="List Detection Run History")
def get_detection_runs(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(RiskDetectionRun)
        .order_by(RiskDetectionRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "rules_run": r.rules_run,
            "alerts_created": r.alerts_created,
            "status": r.status,
            "error": r.error,
        }
        for r in runs
    ]
