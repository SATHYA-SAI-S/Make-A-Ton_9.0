import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Numeric, Integer, Date, DateTime, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class BillingPeriod(Base):
    __tablename__ = "billing_periods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(20), default="BILLED", nullable=False)  # PENDING, BILLED, SKIPPED
    invoice_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", "period_end", name="uq_subscription_billing_period"),
    )

class BillingRun(Base):
    __tablename__ = "billing_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED
    triggered_by = Column(String(50), default="SCHEDULER", nullable=False)  # SCHEDULER, ADMIN_MANUAL, DRY_RUN
    subscriptions_checked = Column(Integer, default=0, nullable=False)
    invoices_created = Column(Integer, default=0, nullable=False)
    failures = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)

    items = relationship("BillingRunItem", back_populates="run", cascade="all, delete-orphan")

class BillingRunItem(Base):
    __tablename__ = "billing_run_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("billing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(String(36), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    invoice_id = Column(String(36), nullable=True)
    result = Column(String(20), nullable=False)  # SUCCESS, SKIPPED, FAILED
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    run = relationship("BillingRun", back_populates="items")
