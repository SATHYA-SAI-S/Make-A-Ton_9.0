"""
Audit Service.
Handles audit record emission, field-level diff calculation, and query filters.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.audit.models import AuditLog
from backend.app.core.database import SessionLocal

def compute_diff(before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Computes field-level difference between before and after JSON snapshots.
    Returns: { "field_name": { "before": old_val, "after": new_val, "changed": True } }
    """
    diff: Dict[str, Dict[str, Any]] = {}
    before = before or {}
    after = after or {}

    all_keys = set(before.keys()).union(set(after.keys()))
    for key in sorted(all_keys):
        old_val = before.get(key)
        new_val = after.get(key)
        if old_val != new_val:
            diff[key] = {
                "before": old_val,
                "after": new_val,
                "changed": True
            }
    return diff

def emit_audit_event(
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    actor_role: str = "system",
    request_id: Optional[str] = None,
    db: Optional[Session] = None
) -> str:
    """
    Persists an audit event to the append-only audit log.
    If db session is not passed, creates and manages its own session safely.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        log_id = str(uuid.uuid4())
        audit_entry = AuditLog(
            id=log_id,
            occurred_at=datetime.now(timezone.utc),
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            meta=meta or {},
            request_id=request_id
        )
        db.add(audit_entry)
        db.commit()
        return log_id
    finally:
        if close_db:
            db.close()

def query_audit_logs(
    db: Session,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """Queries audit logs with multi-dimensional filtering and sorting."""
    query = db.query(AuditLog)

    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if actor_role:
        query = query.filter(AuditLog.actor_role == actor_role)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if start_date:
        query = query.filter(AuditLog.occurred_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.occurred_at <= end_date)

    total = query.count()
    items = query.order_by(desc(AuditLog.occurred_at)).offset(offset).limit(limit).all()

    results = []
    for item in items:
        d = item.to_dict()
        d["diff"] = compute_diff(item.before, item.after)
        results.append(d)

    return results, total
