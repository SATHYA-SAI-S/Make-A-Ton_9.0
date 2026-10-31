"""
Audit Module Bootstrap.
Implements and registers AuditPort into the central shared registry.
Writes audit records reliably without failing calling business operations.
"""
from typing import Any, Dict, Optional
from backend.app.shared.ports import AuditPort
from backend.app.shared.registry import register_port
from backend.app.audit.service import emit_audit_event

class AuditPortImpl(AuditPort):
    def emit(
        self,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        actor_role: str = "system",
        request_id: Optional[str] = None
    ) -> str:
        try:
            return emit_audit_event(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=after,
                meta=meta,
                actor_role=actor_role,
                request_id=request_id
            )
        except Exception as e:
            # Fallback error logging to ensure business transaction does not abort
            print(f"[AUDIT PORT EMIT ERROR] Failed to record audit log: {e}")
            import uuid
            return f"err-fallback-{uuid.uuid4()}"

def bootstrap_audit():
    """Bootstraps the Audit service and registers port."""
    register_port("audit", AuditPortImpl())

# Auto-register at import time
bootstrap_audit()
