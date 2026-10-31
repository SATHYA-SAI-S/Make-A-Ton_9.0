import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Numeric, Date, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    subscription_id = Column(String(36), nullable=True, index=True)
    billing_period_id = Column(String(36), index=True, nullable=True)
    status = Column(String(20), default="DRAFT", nullable=False)  # DRAFT, CONFIRMED, PARTIALLY_PAID, PAID, CANCELLED
    invoice_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    subtotal = Column(Numeric(14, 2), nullable=False)
    discount_total = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    total = Column(Numeric(14, 2), nullable=False)
    amount_paid = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    balance = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), default="INR", server_default="INR", nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    snapshot = Column(JSON, default=dict, server_default="{}", nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)

    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_invoices_customer_status", "customer_id", "status"),
        Index("idx_invoices_due_date", "due_date"),
        Index("idx_invoices_subscription_id", "subscription_id"),
    )

    @property
    def is_overdue(self) -> bool:
        if self.status in ("CONFIRMED", "PARTIALLY_PAID") and self.balance > Decimal("0.00"):
            return self.due_date < date.today()
        return False

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), nullable=False)
    variant_id = Column(String(36), nullable=True)
    description = Column(Text, default="", server_default="", nullable=True)
    quantity = Column(Numeric(10, 0), default=1, nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    discount_amount = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    tax_rate = Column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(14, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="lines")
