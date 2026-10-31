import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, Boolean, Date, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

# Join table for tax rules and product restrictions
tax_rule_products = Table(
    "tax_rule_products",
    Base.metadata,
    Column("rule_id", String(36), ForeignKey("tax_rules.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", String(36), primary_key=True)
)

class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(6, 2), nullable=False)  # e.g. 18.00
    type = Column(String(20), nullable=False)  # GST, CGST, SGST, IGST, VAT, OTHER
    effective_from = Column(Date, default=date.today, nullable=False)
    effective_to = Column(Date, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

class TaxCalculationHistory(Base):
    __tablename__ = "tax_calculation_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_line_id = Column(String(36), nullable=True)
    rule_id = Column(String(36), nullable=True)
    rule_name = Column(String(100), nullable=False)
    rate = Column(Numeric(6, 2), nullable=False)
    base_amount = Column(Numeric(14, 2), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

class BillingSettings(Base):
    __tablename__ = "billing_settings"

    id = Column(String(36), primary_key=True, default="default")
    company_name = Column(String(200), default="Brightloop Software", nullable=False)
    company_state_code = Column(String(10), default="KA", nullable=False)
    company_gstin = Column(String(30), default="29AABCU9603R1Z7", nullable=False)
    default_currency = Column(String(10), default="INR", nullable=False)
    invoice_prefix = Column(String(20), default="INV", nullable=False)
    invoice_sequence = Column(Numeric(10, 0), default=1, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)
