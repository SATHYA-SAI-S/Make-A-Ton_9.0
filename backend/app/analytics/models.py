"""
SQLAlchemy models for Analytics and Financial Snapshots.
Supports pre-aggregated performance caching and historical metrics.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    DateTime,
    Text,
    Index,
    UniqueConstraint
)
from backend.app.core.database import Base


class RevenueSnapshot(Base):
    __tablename__ = "revenue_snapshots"
    __table_args__ = (
        UniqueConstraint("period", name="uq_revenue_snapshots_period"),
        {"extend_existing": True}
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period = Column(String(20), nullable=False, index=True)  # e.g., '2026-10'
    mrr = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    arr = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    invoiced = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    collected = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    outstanding = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    active_subscriptions = Column(Integer, nullable=False, default=0)
    customers = Column(Integer, nullable=False, default=0)
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        Index("ix_analytics_snapshots_lookup", "metric_key", "dimension", "period"),
        {"extend_existing": True}
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_key = Column(String(100), nullable=False, index=True)  # e.g., 'mrr_trend', 'churn_rate'
    dimension = Column(String(100), nullable=True, index=True)   # e.g., 'MONTHLY', 'ENTERPRISE'
    period = Column(String(50), nullable=True, index=True)       # e.g., '2026-10'
    value = Column(Text, nullable=False)                        # Decimal string or JSON blob
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
