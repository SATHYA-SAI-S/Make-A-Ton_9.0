from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DictLikeBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def __setitem__(self, key: str, value: Any) -> None:
        self.__dict__[key] = value
        setattr(self, key, value)


    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class TaxBreakdownDTO(DictLikeBaseModel):
    rule_name: str
    tax_type: str  # CGST, SGST, IGST, VAT, OTHER
    rate: Decimal
    base_amount: Decimal
    tax_amount: Decimal


class TaxLineInputDTO(DictLikeBaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")


class CustomerDTO(DictLikeBaseModel):

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


class SubscriptionLineDTO(DictLikeBaseModel):
    id: str
    product_id: str
    variant_id: Optional[str] = None
    product_name: str = ""
    quantity: int = 1
    unit_price: Decimal
    tax_amount_preview: Decimal = Decimal("0.00")
    amount: Decimal


class SubscriptionDTO(DictLikeBaseModel):
    id: str
    number: str
    customer_id: str
    plan_id: str
    plan_name: str = "Standard Plan"
    status: str = "ACTIVE"  # DRAFT, QUOTATION, CONFIRMED, ACTIVE, PAUSED, CLOSED
    close_reason: Optional[str] = None
    billing_frequency: str = "MONTHLY"  # DAILY, WEEKLY, MONTHLY, YEARLY
    start_date: date
    expiry_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    payment_terms_days: int = 15
    currency: str = "INR"
    lines: List[SubscriptionLineDTO] = []


class InvoiceLineDTO(DictLikeBaseModel):
    id: str
    product_id: str
    description: str = ""
    quantity: int = 1
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal


class InvoiceDTO(DictLikeBaseModel):
    id: str
    number: str
    customer_id: str
    subscription_id: Optional[str] = None
    status: str = "DRAFT"  # DRAFT, CONFIRMED, PARTIALLY_PAID, PAID, CANCELLED
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
    lines: List[InvoiceLineDTO] = []


class PaymentDTO(DictLikeBaseModel):
    id: str
    customer_id: str
    method: str
    amount: Decimal
    payment_date: datetime
    reference: Optional[str] = None
    notes: Optional[str] = None
    status: str = "RECORDED"

