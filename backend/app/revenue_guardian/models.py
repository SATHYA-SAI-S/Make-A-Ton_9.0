"""
SQLAlchemy models for Revenue Guardian risk alerts and detection runs.
Tables:
- risk_alerts: autonomous detection findings with severity scoring and resolution lifecycle.
- risk_detection_runs: audit log of detection cycles executed.
"""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    DateTime,
    Text,
    Index,
)
from backend.app.core.database import Base


class RiskAlert(Base):
    __tablename__ = "risk_alerts"
    __table_args__ = (
        Index("ix_risk_alerts_status_severity", "status", "severity"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_key = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # BILLING, PAYMENT, SUBSCRIPTION, REVENUE
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    score = Column(Integer, nullable=False, default=50)  # 1-100
    customer_id = Column(String(36), nullable=True, index=True)
    subscription_id = Column(String(36), nullable=True, index=True)
    invoice_id = Column(String(36), nullable=True, index=True)  # Soft UUID reference without hard FK
    payment_id = Column(String(36), nullable=True, index=True)  # Soft UUID reference without hard FK
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    estimated_impact = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    explanation = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    fingerprint = Column(String(255), nullable=False, unique=True, index=True)


class RiskDetectionRun(Base):
    __tablename__ = "risk_detection_runs"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    rules_run = Column(Integer, nullable=False, default=0)
    alerts_created = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="RUNNING", index=True)  # RUNNING, SUCCESS, FAILED
    error = Column(Text, nullable=True)
