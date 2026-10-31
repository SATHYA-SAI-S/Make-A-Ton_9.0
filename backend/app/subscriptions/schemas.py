import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SubscriptionLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class SubscriptionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    from_state: str
    to_state: str
    reason: str
    created_at: datetime


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_number: str
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    plan_version_id: uuid.UUID
    quotation_id: Optional[uuid.UUID] = None
    status: str
    start_date: date
    end_date: date
    payment_terms: str
    next_billing_at: Optional[date] = None
    billing_anchor_day: int
    currency: str
    total_amount: Decimal
    created_by: uuid.UUID
    lines: List[SubscriptionLineResponse] = []
    events: List[SubscriptionEventResponse] = []
    created_at: datetime
    updated_at: datetime


class SubscriptionActionRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500, description="Audit reason for state transition")


# Due Subscription Schemas (Shared Contract for Person 2 Billing Engine)

class DueSubscriptionLine(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: str
    quantity: int
    unit_price: str  # Decimal string to guarantee precision across JSON
    line_total: str


class DueSubscriptionItem(BaseModel):
    subscription_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    plan_version_id: uuid.UUID
    billing_frequency: str
    next_billing_at: date
    currency: str
    lines: List[DueSubscriptionLine]


class DueSubscriptionListResponse(BaseModel):
    items: List[DueSubscriptionItem]
    as_of: date
    total_due: int
    next_cursor: Optional[str] = None


class AdvanceBillingRequest(BaseModel):
    period_start: date
    period_end: date
