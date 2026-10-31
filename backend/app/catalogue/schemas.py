import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Product Variant Schemas

class ProductVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price_adjustment: Decimal = Field(default=Decimal("0.00"), description="Positive or negative price delta relative to base product")
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price_adjustment: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Product Schemas

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    type: str = Field("service", pattern="^(service|physical|digital)$")
    sales_price: Decimal = Field(..., ge=0, description="Base sales price")
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None
    is_active: bool = True
    currency: str = Field("INR", max_length=10)


class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    type: Optional[str] = Field(None, pattern="^(service|physical|digital)$")
    sales_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    currency: Optional[str] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variants: List[ProductVariantResponse] = []
    created_at: datetime
    updated_at: datetime


# Plan Schemas

class PlanVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    version_no: int
    price: Decimal
    effective_from: datetime
    created_at: datetime


class PlanBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    billing_frequency: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    min_quantity: int = Field(1, ge=1)
    available_from: date
    available_to: date
    allow_pause: bool = True
    allow_early_close: bool = True
    allow_renewal: bool = True
    status: str = Field("active", pattern="^(active|closed)$")


class PlanCreate(PlanBase):
    price: Decimal = Field(..., ge=0, description="Initial version price")


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    min_quantity: Optional[int] = Field(None, ge=1)
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    allow_pause: Optional[bool] = None
    allow_early_close: Optional[bool] = None
    allow_renewal: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(active|closed)$")


class PlanPriceChangeRequest(BaseModel):
    new_price: Decimal = Field(..., ge=0)
    effective_from: Optional[datetime] = None


class PlanResponse(PlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_price: Decimal
    current_version_no: int
    versions: List[PlanVersionResponse] = []
    created_at: datetime
    updated_at: datetime
