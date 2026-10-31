import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, String, Numeric, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), nullable=False, index=True)
    method = Column(String(30), nullable=False)  # UPI, CARD, BANK_TRANSFER, CASH, OTHER
    amount = Column(Numeric(14, 2), nullable=False)
    unallocated_amount = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    payment_date = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="RECORDED", nullable=False)  # RECORDED, FAILED, REFUNDED
    gateway_event_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")

class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    payment = relationship("Payment", back_populates="allocations")
