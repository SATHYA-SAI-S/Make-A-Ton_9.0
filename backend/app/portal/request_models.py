"""
Customer Requests Database Models.
Tracks customer lifecycle change requests (Upgrade, Downgrade, Pause, Cancel, Renewal)
and Staff review actions.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    String,
    Text,
)
from backend.app.core.database import Base

class CustomerRequest(Base):
    __tablename__ = "customer_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(100), nullable=False)
    subscription_id = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # UPGRADE, DOWNGRADE, PAUSE, CANCEL, RENEWAL
    target_plan_id = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED, APPLIED, FAILED
    decided_by = Column(String(100), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        Index("ix_custreq_customer_status", "customer_id", "status"),
        Index("ix_custreq_subscription", "subscription_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "type": self.type,
            "target_plan_id": self.target_plan_id,
            "note": self.note,
            "status": self.status,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decision_note": self.decision_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
