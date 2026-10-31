"""
Audit Log Database Models.
Append-only log recording actor, action, entity, before/after JSON snapshots, and metadata.
Enforces immutability at the model event level.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    JSON,
    String,
    Text,
    event,
)
from sqlalchemy.orm import validates
from app.core.database import Base
from app.core.errors import SubscriptIQError

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    occurred_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    actor_id = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=False, default="system")
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)
    request_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor_time", "actor_id", "occurred_at"),
        Index("ix_audit_action_time", "action", "occurred_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "before": self.before,
            "after": self.after,
            "meta": self.meta,
            "request_id": self.request_id,
        }

# Database & ORM Immutable Enforcement (Append-Only)
@event.listens_for(AuditLog, 'before_update')
def block_audit_log_update(mapper, connection, target):
    raise SubscriptIQError(
        code="AUDIT_LOG_IMMUTABLE",
        message="Audit logs are append-only. Modifying existing audit log entries is strictly forbidden.",
        status_code=400
    )

@event.listens_for(AuditLog, 'before_delete')
def block_audit_log_delete(mapper, connection, target):
    raise SubscriptIQError(
        code="AUDIT_LOG_IMMUTABLE",
        message="Audit logs are append-only. Deleting audit log records is strictly forbidden.",
        status_code=400
    )
