import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Quotation Template Schemas

class QuotationTemplateLineCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int = Field(1, ge=1)


class QuotationTemplateLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int


class QuotationTemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    default_plan_id: uuid.UUID
    validity_days: int = Field(30, ge=1, le=365)
    payment_terms: str = Field("Due Upon Receipt", max_length=255)
    is_active: bool = True
    lines: Optional[List[QuotationTemplateLineCreate]] = None


class QuotationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    default_plan_id: Optional[uuid.UUID] = None
    validity_days: Optional[int] = Field(None, ge=1, le=365)
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None


class QuotationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    default_plan_id: uuid.UUID
    validity_days: int
    payment_terms: str
    is_active: bool
    lines: List[QuotationTemplateLineResponse] = []
    created_at: datetime
    updated_at: datetime


# Quotation Schemas

class QuotationLineCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    quantity: int = Field(1, ge=1)


class QuotationLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class QuotationCreate(BaseModel):
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    validity_days: Optional[int] = Field(None, ge=1, le=365)
    payment_terms: Optional[str] = "Due Upon Receipt"
    currency: str = "INR"
    lines: List[QuotationLineCreate] = Field(..., min_length=1)


class QuotationUpdate(BaseModel):
    payment_terms: Optional[str] = None
    validity_days: Optional[int] = Field(None, ge=1, le=365)
    lines: Optional[List[QuotationLineCreate]] = None


class QuotationExtendValidityRequest(BaseModel):
    additional_days: int = Field(..., ge=1, le=365)
    reason: str = Field(..., min_length=3, max_length=500)


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    plan_version_id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    status: str
    valid_until: date
    payment_terms: str
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str
    created_by: uuid.UUID
    lines: List[QuotationLineResponse] = []
    created_at: datetime
    updated_at: datetime
