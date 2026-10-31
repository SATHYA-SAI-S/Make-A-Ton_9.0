"""
Shared Data Transfer Objects (DTOs).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class SubscriptionLineDTO(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str] = None
    product_name: str
    quantity: int
    unit_price: Decimal
    tax_amount_preview: Decimal = Decimal("0.00")
    amount: Decimal

class SubscriptionDTO(BaseModel):
    id: str
    number: str
    customer_id: str
    plan_id: str
    plan_name: str
    billing_frequency: str  # DAILY, WEEKLY, MONTHLY, YEARLY
    status: str             # DRAFT, QUOTATION, CONFIRMED, ACTIVE, PAUSED, CLOSED
    close_reason: Optional[str] = None
    start_date: date
    expiry_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    payment_terms_days: int = 30
    currency: str = "INR"
    lines: List[SubscriptionLineDTO] = []

class InvoiceLineDTO(BaseModel):
    id: str
    product_id: str
    description: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal

class InvoiceDTO(BaseModel):
    id: str
    number: str
    customer_id: str
    subscription_id: str
    status: str  # DRAFT, CONFIRMED, PARTIALLY_PAID, PAID, CANCELLED
    invoice_date: date
    due_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance: Decimal
    is_overdue: bool = False
    lines: List[InvoiceLineDTO] = []
