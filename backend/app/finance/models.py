"""
SQLAlchemy models for Finance and Billing entities.
Contracts aligned with Person 1 (customers, plans, subscriptions)
and Person 2 (invoices, payments, refunds).
"""
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    Index,
    JSON
)
from sqlalchemy.orm import relationship, declarative_base
from app.core.database import Base

FinanceBase = declarative_base()


class Customer(FinanceBase):
    __tablename__ = "customers"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    billing_address = Column(Text, nullable=True)
    state_code = Column(String(10), nullable=True)
    gstin = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE")
    segment = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")


class Plan(FinanceBase):
    __tablename__ = "plans"
    __table_args__ = {"extend_existing": True}

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    billing_frequency = Column(String(20), nullable=False, default="MONTHLY")  # DAILY, WEEKLY, MONTHLY, YEARLY
    min_quantity = Column(Integer, default=1)
    available_from = Column(Date, nullable=True)
    available_to = Column(Date, nullable=True)
    allow_pause = Column(Boolean, default=True)
    allow_early_close = Column(Boolean, default=True)
    allow_renewal = Column(Boolean, default=True)
    current_version = Column(Integer, default=1)
    status = Column(String(50), default="ACTIVE")

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(FinanceBase):
    __tablename__ = "subscriptions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(String(50), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    plan_id = Column(String(100), ForeignKey("plans.id"), nullable=False)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, PAUSED, CLOSED, DRAFT, CONFIRMED
    close_reason = Column(String(50), nullable=True)  # EXPIRED, EARLY_CLOSURE, CANCELLED
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    next_billing_date = Column(Date, nullable=True)
    payment_terms_days = Column(Integer, default=30)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    lines = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionLine(FinanceBase):
    __tablename__ = "subscription_lines"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    product_id = Column(String(100), nullable=False)
    variant_id = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    tax_amount_preview = Column(Numeric(14, 2), default=Decimal("0.00"))
    amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    subscription = relationship("Subscription", back_populates="lines")


class Invoice(FinanceBase):
    __tablename__ = "invoices"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(String(50), nullable=False)
    customer_id = Column(String(36), nullable=False)
    subscription_id = Column(String(36), nullable=True)
    billing_period_id = Column(String(36), nullable=True)
    status = Column(String(50), default="CONFIRMED")  # DRAFT, CONFIRMED, PARTIALLY_PAID, PAID, CANCELLED
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(14, 2), default=Decimal("0.00"))
    discount_total = Column(Numeric(14, 2), default=Decimal("0.00"))
    tax_total = Column(Numeric(14, 2), default=Decimal("0.00"))
    total = Column(Numeric(14, 2), default=Decimal("0.00"))
    amount_paid = Column(Numeric(14, 2), default=Decimal("0.00"))
    balance = Column(Numeric(14, 2), default=Decimal("0.00"))
    snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(FinanceBase):
    __tablename__ = "invoice_lines"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    product_id = Column(String(100), nullable=False)
    variant_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = Column(Numeric(14, 2), default=Decimal("0.00"))
    tax_rate = Column(Numeric(6, 4), default=Decimal("0.0000"))
    tax_amount = Column(Numeric(14, 2), default=Decimal("0.00"))
    line_total = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    invoice = relationship("Invoice", back_populates="lines")


class Payment(FinanceBase):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), nullable=False)
    method = Column(String(50), nullable=False)  # UPI, CARD, NETBANKING, BANK_TRANSFER, CASH
    amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    payment_date = Column(Date, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="RECORDED")  # RECORDED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(FinanceBase):
    __tablename__ = "payment_allocations"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    invoice_id = Column(String(36), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    payment = relationship("Payment", back_populates="allocations")


class Refund(FinanceBase):
    __tablename__ = "refunds"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    customer_id = Column(String(36), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    refund_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="PROCESSED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    payment = relationship("Payment", back_populates="refunds")


class ForecastScenario(Base):
    __tablename__ = "forecast_scenarios"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    horizon_months = Column(Integer, nullable=False, default=12)
    assumptions = Column(JSON, nullable=False)
    projection = Column(JSON, nullable=False)
    summary = Column(JSON, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

