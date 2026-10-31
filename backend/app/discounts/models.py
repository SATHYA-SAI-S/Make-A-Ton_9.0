import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, Integer, Boolean, Date, DateTime, Text, ForeignKey
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class DiscountRule(Base):
    __tablename__ = "discount_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # FIXED, PERCENT
    value = Column(Numeric(14, 2), nullable=False)  # e.g. 500.00 or 15.00
    min_purchase = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    min_quantity = Column(Integer, default=0, nullable=False)
    start_date = Column(Date, default=date.today, nullable=False)
    end_date = Column(Date, nullable=True)
    max_usage = Column(Integer, nullable=True)  # Null = unlimited
    used_count = Column(Integer, default=0, nullable=False)
    scope = Column(String(20), default="SUBSCRIPTION", nullable=False)  # PRODUCT, SUBSCRIPTION
    product_id = Column(String(36), nullable=True)
    priority = Column(Integer, default=1, nullable=False)  # 1 = highest priority
    stackable = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRED, DISABLED
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

class DiscountRedemption(Base):
    __tablename__ = "discount_redemptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("discount_rules.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(String(36), nullable=True)
    customer_id = Column(String(36), nullable=True)
    subscription_id = Column(String(36), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
