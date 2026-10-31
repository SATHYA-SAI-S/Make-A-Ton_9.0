import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Boolean, Date, DateTime, Numeric, Integer, Uuid, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), default="service", nullable=False)  # service, physical, digital
    sales_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)

    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_adjustment: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    billing_frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    min_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    available_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    allow_pause: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_early_close: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_renewal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, closed
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=True)
    current_version: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)

    versions: Mapped[List["PlanVersion"]] = relationship("PlanVersion", back_populates="plan", cascade="all, delete-orphan", order_by="desc(PlanVersion.version_no)")

    __table_args__ = (
        Index("ix_plans_frequency_status", "billing_frequency", "status"),
    )


class PlanVersion(Base):
    __tablename__ = "plan_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    plan: Mapped["Plan"] = relationship("Plan", back_populates="versions")

    __table_args__ = (
        Index("ix_plan_versions_plan_ver", "plan_id", "version_no", unique=True),
    )
