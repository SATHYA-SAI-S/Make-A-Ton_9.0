import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.core.errors import ValidationException, NotFoundException, ForbiddenException, ConflictException
from app.quotations.models import QuotationTemplate, QuotationTemplateLine, Quotation, QuotationLine
from app.quotations.schemas import (
    QuotationTemplateCreate,
    QuotationTemplateUpdate,
    QuotationCreate,
    QuotationUpdate,
    QuotationExtendValidityRequest
)
from app.customers.models import Customer
from app.catalogue.models import Product, ProductVariant, Plan, PlanVersion
from app.catalogue.service import effective_unit_price, is_plan_available
from app.auth.models import User


def generate_quotation_number(db: Session) -> str:
    """Generate sequential, unique quotation identifier: QTN-YYYY-XXXXXX."""
    year = datetime.now(timezone.utc).year
    prefix = f"QTN-{year}-"
    latest = db.scalar(
        select(Quotation.number)
        .where(Quotation.number.like(f"{prefix}%"))
        .order_by(desc(Quotation.number))
        .limit(1)
    )
    if latest:
        try:
            seq = int(latest.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


# Quotation Templates

def create_template(db: Session, request: QuotationTemplateCreate, creator: User) -> QuotationTemplate:
    if creator.role not in ("admin", "staff"):
        raise ForbiddenException("Only staff and administrators can create quotation templates.", code="PERMISSION_DENIED")

    plan = db.get(Plan, request.default_plan_id)
    if not plan:
        raise NotFoundException("Default plan not found.", code="PLAN_NOT_FOUND")

    template = QuotationTemplate(
        name=request.name.strip(),
        default_plan_id=request.default_plan_id,
        validity_days=request.validity_days,
        payment_terms=request.payment_terms,
        is_active=request.is_active
    )
    db.add(template)
    db.flush()

    if request.lines:
        for line_req in request.lines:
            product = db.get(Product, line_req.product_id)
            if not product:
                raise NotFoundException(f"Product {line_req.product_id} not found.", code="PRODUCT_NOT_FOUND")
            t_line = QuotationTemplateLine(
                template_id=template.id,
                product_id=line_req.product_id,
                variant_id=line_req.variant_id,
                quantity=line_req.quantity
            )
            db.add(t_line)

    db.commit()
    db.refresh(template)
    return template


def list_templates(db: Session, is_active: Optional[bool] = None) -> List[QuotationTemplate]:
    query = select(QuotationTemplate)
    if is_active is not None:
        query = query.where(QuotationTemplate.is_active == is_active)
    return list(db.scalars(query.order_by(QuotationTemplate.name.asc())).all())


def get_template(db: Session, template_id: uuid.UUID) -> QuotationTemplate:
    template = db.get(QuotationTemplate, template_id)
    if not template:
        raise NotFoundException("Quotation template not found.", code="TEMPLATE_NOT_FOUND")
    return template


# Quotations

def create_quotation(db: Session, request: QuotationCreate, creator: User) -> Quotation:
    """Create quotation with deterministic totals and unit price snapshots."""
    if creator.role not in ("admin", "staff"):
        raise ForbiddenException("Only staff and administrators can create quotations.", code="PERMISSION_DENIED")

    # 1. Verify customer
    customer = db.get(Customer, request.customer_id)
    if not customer:
        raise NotFoundException("Customer not found.", code="CUSTOMER_NOT_FOUND")
    if customer.status != "active":
        raise ValidationException("Cannot quote an inactive/suspended customer.", code="CUSTOMER_INACTIVE")

    # 2. Verify plan & availability
    plan = db.get(Plan, request.plan_id)
    if not plan:
        raise NotFoundException("Subscription plan not found.", code="PLAN_NOT_FOUND")

    today = date.today()
    if not is_plan_available(plan, today):
        raise ValidationException(
            f"Plan '{plan.name}' is not currently available for quotations (valid {plan.available_from} to {plan.available_to}).",
            code="PLAN_UNAVAILABLE"
        )

    # Latest plan version
    latest_ver = db.scalar(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan.id)
        .order_by(desc(PlanVersion.version_no))
    )
    if not latest_ver:
        raise ValidationException("Plan has no price version configured.", code="PLAN_VERSION_MISSING")

    # 3. Check minimum quantity
    total_quantity = sum(line.quantity for line in request.lines)
    if total_quantity < plan.min_quantity:
        raise ValidationException(
            f"Total quantity ({total_quantity}) does not satisfy plan minimum quantity requirement of {plan.min_quantity}.",
            code="MIN_QUANTITY_NOT_MET"
        )

    # 4. Validity date
    validity_days = request.validity_days or 30
    valid_until = today + timedelta(days=validity_days)

    # 5. Build lines with unit price snapshot
    subtotal = Decimal("0.00")
    quotation_lines = []

    for line_req in request.lines:
        product = db.get(Product, line_req.product_id)
        if not product:
            raise NotFoundException(f"Product {line_req.product_id} not found.", code="PRODUCT_NOT_FOUND")

        variant = None
        if line_req.variant_id:
            variant = db.get(ProductVariant, line_req.variant_id)
            if not variant or variant.product_id != product.id:
                raise NotFoundException(f"Invalid variant for product {product.name}.", code="VARIANT_INVALID")

        unit_price = effective_unit_price(product, variant)
        line_total = (Decimal(line_req.quantity) * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total

        description = product.name
        if variant:
            description += f" - {variant.name}"

        quotation_lines.append(
            QuotationLine(
                product_id=product.id,
                variant_id=line_req.variant_id,
                description=line_req.description or description,
                quantity=line_req.quantity,
                unit_price=unit_price,
                line_total=line_total
            )
        )

    tax_amount = Decimal("0.00")  # Placeholder for Person 2 Tax Engine
    total = (subtotal + tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    quotation = Quotation(
        number=generate_quotation_number(db),
        customer_id=customer.id,
        plan_id=plan.id,
        plan_version_id=latest_ver.id,
        template_id=request.template_id,
        status="draft",
        valid_until=valid_until,
        payment_terms=request.payment_terms or "Due Upon Receipt",
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        currency=request.currency,
        created_by=creator.id,
        lines=quotation_lines
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


def get_quotation(db: Session, quotation_id: uuid.UUID, requesting_user: User) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise NotFoundException("Quotation not found.", code="QUOTATION_NOT_FOUND")

    if requesting_user.role == "customer":
        customer = db.scalar(select(Customer).where(Customer.user_id == requesting_user.id))
        if not customer or customer.id != quotation.customer_id:
            raise ForbiddenException("You cannot access another customer's quotation.", code="IDOR_VIOLATION")

    # Check expiration on read
    if quotation.status in ("draft", "sent") and date.today() > quotation.valid_until:
        quotation.status = "expired"
        db.commit()
        db.refresh(quotation)

    return quotation


def list_quotations(
    db: Session,
    requesting_user: User,
    customer_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None
) -> List[Quotation]:
    query = select(Quotation)
    if requesting_user.role == "customer":
        customer = db.scalar(select(Customer).where(Customer.user_id == requesting_user.id))
        if not customer:
            return []
        query = query.where(Quotation.customer_id == customer.id)
    elif customer_id:
        query = query.where(Quotation.customer_id == customer_id)

    if status:
        query = query.where(Quotation.status == status)

    quotes = list(db.scalars(query.order_by(Quotation.created_at.desc())).all())
    # Evaluate expiration
    today = date.today()
    for q in quotes:
        if q.status in ("draft", "sent") and today > q.valid_until:
            q.status = "expired"
    db.commit()

    return quotes


def send_quotation(db: Session, quotation_id: uuid.UUID, user: User) -> Quotation:
    """Transition quotation: draft -> sent."""
    quotation = get_quotation(db, quotation_id, user)
    if quotation.status != "draft":
        raise ConflictException(f"Only draft quotations can be marked as sent (current status: {quotation.status}).", code="INVALID_STATUS")

    quotation.status = "sent"
    db.commit()
    db.refresh(quotation)
    return quotation


def extend_quotation_validity(
    db: Session,
    quotation_id: uuid.UUID,
    request: QuotationExtendValidityRequest,
    admin_user: User
) -> Quotation:
    """Admin-only action to extend validity of an expired or pending quotation."""
    if admin_user.role != "admin":
        raise ForbiddenException("Only administrators can extend quotation validity.", code="ADMIN_REQUIRED")

    quotation = get_quotation(db, quotation_id, admin_user)
    if quotation.status in ("confirmed", "cancelled"):
        raise ConflictException(f"Cannot extend validity of a {quotation.status} quotation.", code="INVALID_STATUS")

    base_date = max(quotation.valid_until, date.today())
    quotation.valid_until = base_date + timedelta(days=request.additional_days)
    if quotation.status == "expired":
        quotation.status = "sent"

    db.commit()
    db.refresh(quotation)
    return quotation


def cancel_quotation(db: Session, quotation_id: uuid.UUID, reason: str, user: User) -> Quotation:
    quotation = get_quotation(db, quotation_id, user)
    if quotation.status == "confirmed":
        raise ConflictException("Cannot cancel an already confirmed quotation.", code="CANNOT_CANCEL_CONFIRMED")

    quotation.status = "cancelled"
    db.commit()
    db.refresh(quotation)
    return quotation
