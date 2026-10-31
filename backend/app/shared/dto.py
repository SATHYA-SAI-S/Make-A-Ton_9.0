from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TaxBreakdownDTO(BaseModel):
    rule_name: str
    tax_type: str  # CGST, SGST, IGST, VAT, OTHER
    rate: Decimal
    base_amount: Decimal
    tax_amount: Decimal

class TaxLineInputDTO(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")

class CustomerDTO(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    state_code: str = "KA"
    gstin: Optional[str] = None
    status: str = "ACTIVE"
    segment: Optional[str] = None

class SubscriptionLineDTO(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    tax_amount_preview: Decimal = Decimal("0.00")
    amount: Decimal

class SubscriptionDTO(BaseModel):
    id: str
    number: str
    customer_id: str
    plan_id: str
    status: str  # DRAFT, QUOTATION, CONFIRMED, ACTIVE, PAUSED, CLOSED
    close_reason: Optional[str] = None
    billing_frequency: str = "MONTHLY"  # DAILY, WEEKLY, MONTHLY, YEARLY
    start_date: date
    expiry_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    payment_terms_days: int = 15
    currency: str = "INR"
    lines: List[SubscriptionLineDTO] = []

class InvoiceDTO(BaseModel):
    id: str
    number: str
    customer_id: str
    subscription_id: Optional[str] = None
    status: str
    invoice_date: date
    due_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance: Decimal
    is_overdue: bool = False
    snapshot: Dict[str, Any] = {}

class PaymentDTO(BaseModel):
    id: str
    customer_id: str
    method: str
    amount: Decimal
    payment_date: datetime
    reference: Optional[str] = None
    notes: Optional[str] = None
    status: str = "RECORDED"
