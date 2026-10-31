import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, DateTime, Numeric, Integer, Uuid, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)  # SUB-YYYY-XXXXXX
    number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    plan_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("plan_versions.id", ondelete="RESTRICT"), nullable=True)
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("quotations.id", ondelete="RESTRICT"), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)  # draft, quotation, confirmed, active, paused, closed
    close_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(255), default="Due Upon Receipt", server_default="Due Upon Receipt", nullable=False)
    payment_terms_days: Mapped[Optional[int]] = mapped_column(Integer, default=30, server_default="30", nullable=True)
    next_billing_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    next_billing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    billing_anchor_day: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", server_default="INR", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="subscriptions")
    quotation: Mapped[Optional["Quotation"]] = relationship("Quotation", back_populates="subscription")
    lines: Mapped[List["SubscriptionLine"]] = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")
    events: Mapped[List["SubscriptionEvent"]] = relationship("SubscriptionEvent", back_populates="subscription", cascade="all, delete-orphan", order_by="desc(SubscriptionEvent.created_at)")

    __table_args__ = (
        Index("ix_subscriptions_status_next_billing", "status", "next_billing_at"),
    )


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), default="", nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount_preview: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=True)
    line_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=True)

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="lines")


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    from_state: Mapped[str] = mapped_column(String(50), nullable=False)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="events")
