import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.core.errors import ValidationException, NotFoundException, ForbiddenException, ConflictException
from app.catalogue.models import Product, ProductVariant, Plan, PlanVersion
from app.catalogue.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanVersionResponse,
    PlanPriceChangeRequest
)
from app.auth.models import User


def effective_unit_price(product: Product, variant: Optional[ProductVariant] = None) -> Decimal:
    """
    Pure pricing calculation with strict Decimal arithmetic.
    effective unit price = product.sales_price + variant.price_adjustment
    Guarantees price never falls below zero.
    """
    base_price = Decimal(str(product.sales_price))
    adjustment = Decimal(str(variant.price_adjustment)) if variant else Decimal("0.00")
    total_price = base_price + adjustment

    if total_price < Decimal("0.00"):
        raise ValidationException(
            f"Effective unit price ({total_price}) cannot be negative after variant adjustment ({adjustment}).",
            code="NEGATIVE_PRICE"
        )

    return total_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Product Management

def create_product(db: Session, request: ProductCreate, creator: User) -> Product:
    """Admin-only product creation."""
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can create products.", code="ADMIN_REQUIRED")

    product = Product(
        name=request.name.strip(),
        type=request.type,
        sales_price=request.sales_price,
        cost_price=request.cost_price,
        notes=request.notes,
        is_active=request.is_active,
        currency=request.currency
    )
    db.add(product)
    db.flush()

    if request.variants:
        for v in request.variants:
            # Validate effective price does not fall below zero
            effective_unit_price(product, ProductVariant(price_adjustment=v.price_adjustment))
            variant = ProductVariant(
                product_id=product.id,
                name=v.name.strip(),
                price_adjustment=v.price_adjustment,
                is_active=v.is_active
            )
            db.add(variant)

    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundException("Product not found.", code="PRODUCT_NOT_FOUND")
    return product


def list_products(db: Session, is_active: Optional[bool] = None) -> List[Product]:
    query = select(Product)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    return list(db.scalars(query.order_by(Product.name.asc())).all())


def update_product(db: Session, product_id: uuid.UUID, request: ProductUpdate, creator: User) -> Product:
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can update products.", code="ADMIN_REQUIRED")

    product = get_product(db, product_id)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def add_product_variant(db: Session, product_id: uuid.UUID, request: ProductVariantCreate, creator: User) -> ProductVariant:
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can add product variants.", code="ADMIN_REQUIRED")

    product = get_product(db, product_id)
    # Validate non-negative effective price
    effective_unit_price(product, ProductVariant(price_adjustment=request.price_adjustment))

    variant = ProductVariant(
        product_id=product.id,
        name=request.name.strip(),
        price_adjustment=request.price_adjustment,
        is_active=request.is_active
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def update_product_variant(db: Session, variant_id: uuid.UUID, request: ProductVariantUpdate, creator: User) -> ProductVariant:
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can modify product variants.", code="ADMIN_REQUIRED")

    variant = db.get(ProductVariant, variant_id)
    if not variant:
        raise NotFoundException("Product variant not found.", code="VARIANT_NOT_FOUND")

    product = db.get(Product, variant.product_id)
    update_data = request.model_dump(exclude_unset=True)

    if "price_adjustment" in update_data and update_data["price_adjustment"] is not None:
        effective_unit_price(product, ProductVariant(price_adjustment=update_data["price_adjustment"]))

    for field, value in update_data.items():
        setattr(variant, field, value)

    db.commit()
    db.refresh(variant)
    return variant


# Plan Management & Versioning

def create_plan(db: Session, request: PlanCreate, creator: User) -> PlanResponse:
    """Admin-only plan creation with initial version."""
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can create subscription plans.", code="ADMIN_REQUIRED")

    if request.available_to < request.available_from:
        raise ValidationException("available_to date must be greater than or equal to available_from date.", code="INVALID_DATE_RANGE")

    plan = Plan(
        name=request.name.strip(),
        billing_frequency=request.billing_frequency,
        min_quantity=request.min_quantity,
        available_from=request.available_from,
        available_to=request.available_to,
        allow_pause=request.allow_pause,
        allow_early_close=request.allow_early_close,
        allow_renewal=request.allow_renewal,
        status=request.status
    )
    db.add(plan)
    db.flush()

    # Initial Version 1
    version = PlanVersion(
        plan_id=plan.id,
        version_no=1,
        price=request.price,
        effective_from=datetime.now(timezone.utc)
    )
    db.add(version)
    db.commit()
    db.refresh(plan)

    return PlanResponse(
        id=plan.id,
        name=plan.name,
        billing_frequency=plan.billing_frequency,
        current_price=request.price,
        current_version_no=1,
        min_quantity=plan.min_quantity,
        available_from=plan.available_from,
        available_to=plan.available_to,
        allow_pause=plan.allow_pause,
        allow_early_close=plan.allow_early_close,
        allow_renewal=plan.allow_renewal,
        status=plan.status,
        versions=[PlanVersionResponse.model_validate(version)],
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


def get_plan(db: Session, plan_id: uuid.UUID) -> Plan:
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundException("Subscription plan not found.", code="PLAN_NOT_FOUND")

    # Check auto-closure if today > available_to
    if plan.status == "active" and date.today() > plan.available_to:
        plan.status = "closed"
        db.commit()
        db.refresh(plan)

    return plan


def get_plan_response(db: Session, plan: Plan) -> PlanResponse:
    latest_version = db.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id)
        .order_by(desc(PlanVersion.version_no))
    )
    price = latest_version.price if latest_version else Decimal("0.00")
    version_no = latest_version.version_no if latest_version else 1
    versions = list(db.scalars(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id)
        .order_by(desc(PlanVersion.version_no))
    ).all())

    return PlanResponse(
        id=plan.id,
        name=plan.name,
        billing_frequency=plan.billing_frequency,
        current_price=price,
        current_version_no=version_no,
        min_quantity=plan.min_quantity,
        available_from=plan.available_from,
        available_to=plan.available_to,
        allow_pause=plan.allow_pause,
        allow_early_close=plan.allow_early_close,
        allow_renewal=plan.allow_renewal,
        status=plan.status,
        versions=[PlanVersionResponse.model_validate(v) for v in versions],
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


def list_plans(db: Session, status: Optional[str] = None) -> List[PlanResponse]:
    # Auto-close any expired plans first
    close_expired_plans(db)

    query = select(Plan)
    if status:
        query = query.where(Plan.status == status)

    plans = list(db.scalars(query.order_by(Plan.name.asc())).all())
    return [get_plan_response(db, p) for p in plans]


def update_plan(db: Session, plan_id: uuid.UUID, request: PlanUpdate, creator: User) -> PlanResponse:
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can modify subscription plans.", code="ADMIN_REQUIRED")

    plan = get_plan(db, plan_id)
    update_data = request.model_dump(exclude_unset=True)

    avail_from = update_data.get("available_from", plan.available_from)
    avail_to = update_data.get("available_to", plan.available_to)
    if avail_to < avail_from:
        raise ValidationException("available_to date must be >= available_from date.", code="INVALID_DATE_RANGE")

    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return get_plan_response(db, plan)


def change_plan_price(db: Session, plan_id: uuid.UUID, request: PlanPriceChangeRequest, creator: User) -> PlanVersionResponse:
    """Creates a new immutable plan version. Existing subscriptions keep their agreed price."""
    if creator.role != "admin":
        raise ForbiddenException("Only administrators can update plan prices.", code="ADMIN_REQUIRED")

    plan = get_plan(db, plan_id)

    latest_ver = db.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id)
        .order_by(desc(PlanVersion.version_no))
    )
    new_version_no = (latest_ver.version_no + 1) if latest_ver else 1

    new_version = PlanVersion(
        plan_id=plan.id,
        version_no=new_version_no,
        price=request.new_price,
        effective_from=request.effective_from or datetime.now(timezone.utc)
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return PlanVersionResponse.model_validate(new_version)


def is_plan_available(plan: Plan, on_date: date) -> bool:
    """Verifies whether a plan is currently available for quotation or subscription."""
    if plan.status != "active":
        return False
    return plan.available_from <= on_date <= plan.available_to


def close_expired_plans(db: Session) -> int:
    """Service function to close plans whose available_to date has passed."""
    today = date.today()
    expired_plans = list(db.scalars(
        select(Plan).where(Plan.status == "active", Plan.available_to < today)
    ).all())

    count = len(expired_plans)
    for p in expired_plans:
        p.status = "closed"

    if count > 0:
        db.commit()

    return count
