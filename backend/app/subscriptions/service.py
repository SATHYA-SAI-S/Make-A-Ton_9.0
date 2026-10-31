import uuid
import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_

from app.core.errors import ValidationException, NotFoundException, ForbiddenException, ConflictException
from app.subscriptions.models import Subscription, SubscriptionLine, SubscriptionEvent
from app.subscriptions.schemas import (
    SubscriptionResponse,
    SubscriptionLineResponse,
    SubscriptionEventResponse,
    DueSubscriptionItem,
    DueSubscriptionLine,
    DueSubscriptionListResponse
)
from app.quotations.models import Quotation
from app.catalogue.models import Plan, PlanVersion
from app.customers.models import Customer
from app.auth.models import User

ALLOWED_TRANSITIONS = {
    "draft": ["quotation", "confirmed"],
    "quotation": ["confirmed", "cancelled"],
    "confirmed": ["active", "closed"],
    "active": ["paused", "closed"],
    "paused": ["active", "closed"],
    "closed": []
}


def generate_subscription_number(db: Session) -> str:
    """Generate unique subscription number: SUB-YYYY-XXXXXX."""
    year = datetime.now(timezone.utc).year
    prefix = f"SUB-{year}-"
    latest = db.scalar(
        select(Subscription.subscription_number)
        .where(Subscription.subscription_number.like(f"{prefix}%"))
        .order_by(desc(Subscription.subscription_number))
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


def calculate_frequency_delta(frequency: str, start: date) -> date:
    """Calculate period end date from frequency."""
    if frequency == "daily":
        return start + timedelta(days=1)
    elif frequency == "weekly":
        return start + timedelta(days=7)
    elif frequency == "monthly":
        # 1 month advance with day clamping
        year = start.year + (start.month // 12)
        month = (start.month % 12) + 1
        max_days = calendar.monthrange(year, month)[1]
        day = min(start.day, max_days)
        return date(year, month, day)
    elif frequency == "yearly":
        year = start.year + 1
        max_days = calendar.monthrange(year, start.month)[1]
        day = min(start.day, max_days)
        return date(year, start.month, day)
    return start + timedelta(days=30)


def clamp_date_to_month(year: int, month: int, anchor_day: int) -> date:
    """Clamp an anchor day to the maximum days available in target month."""
    max_days = calendar.monthrange(year, month)[1]
    return date(year, month, min(anchor_day, max_days))


def add_subscription_event(
    db: Session,
    subscription_id: uuid.UUID,
    from_state: str,
    to_state: str,
    reason: str,
    actor_id: Optional[uuid.UUID]
) -> SubscriptionEvent:
    event = SubscriptionEvent(
        subscription_id=subscription_id,
        actor_id=actor_id,
        from_state=from_state,
        to_state=to_state,
        reason=reason
    )
    db.add(event)
    return event


def validate_transition(current_state: str, target_state: str):
    valid_targets = ALLOWED_TRANSITIONS.get(current_state, [])
    if target_state not in valid_targets:
        raise ConflictException(
            f"Invalid subscription state transition from '{current_state}' to '{target_state}'. Permitted: {valid_targets}.",
            code="INVALID_STATE_TRANSITION"
        )


# Lifecycle Operations

def confirm_quotation_to_subscription(db: Session, quotation_id: uuid.UUID, actor: User) -> Subscription:
    """
    Idempotent confirmation: Quotation -> Subscription.
    If subscription already exists for this quotation, returns it safely.
    """
    if actor.role not in ("admin", "staff"):
        raise ForbiddenException("Only staff and administrators can confirm quotations.", code="PERMISSION_DENIED")

    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise NotFoundException("Quotation not found.", code="QUOTATION_NOT_FOUND")

    # Idempotency check: if quotation already created a subscription, return it
    existing_sub = db.scalar(select(Subscription).where(Subscription.quotation_id == quotation.id))
    if existing_sub:
        return existing_sub

    # Expiry verification
    if date.today() > quotation.valid_until:
        quotation.status = "expired"
        db.commit()
        raise ValidationException(
            "This quotation has expired and cannot be confirmed. An administrator must extend its validity.",
            code="QUOTATION_EXPIRED"
        )

    plan = db.get(Plan, quotation.plan_id)
    if not plan:
        raise NotFoundException("Plan not found.", code="PLAN_NOT_FOUND")

    start_date = date.today()
    end_date = calculate_frequency_delta(plan.billing_frequency, start_date)

    subscription = Subscription(
        subscription_number=generate_subscription_number(db),
        customer_id=quotation.customer_id,
        plan_id=quotation.plan_id,
        plan_version_id=quotation.plan_version_id,
        quotation_id=quotation.id,
        status="confirmed",
        start_date=start_date,
        end_date=end_date,
        payment_terms=quotation.payment_terms,
        next_billing_at=start_date,  # First billing occurs on start date
        billing_anchor_day=start_date.day,
        currency=quotation.currency,
        total_amount=quotation.total,
        created_by=actor.id
    )
    db.add(subscription)
    db.flush()

    # Copy snapshot lines
    for q_line in quotation.lines:
        s_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=q_line.product_id,
            variant_id=q_line.variant_id,
            description=q_line.description,
            quantity=q_line.quantity,
            unit_price=q_line.unit_price,
            line_total=q_line.line_total
        )
        db.add(s_line)

    quotation.status = "confirmed"
    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state="quotation",
        to_state="confirmed",
        reason=f"Confirmed quotation {quotation.number}",
        actor_id=actor.id
    )

    db.commit()
    db.refresh(subscription)
    return subscription


def activate_subscription(db: Session, subscription_id: uuid.UUID, actor: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    validate_transition(subscription.status, "active")

    old_status = subscription.status
    subscription.status = "active"
    subscription.next_billing_at = subscription.start_date
    subscription.billing_anchor_day = subscription.start_date.day

    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state=old_status,
        to_state="active",
        reason="Subscription activated",
        actor_id=actor.id
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def pause_subscription(db: Session, subscription_id: uuid.UUID, reason: str, actor: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    plan = db.get(Plan, subscription.plan_id)
    if not plan.allow_pause:
        raise ForbiddenException("The assigned plan does not permit pausing.", code="PAUSE_NOT_ALLOWED")

    validate_transition(subscription.status, "paused")

    old_status = subscription.status
    subscription.status = "paused"
    # Paused subscriptions are excluded from due billing
    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state=old_status,
        to_state="paused",
        reason=reason,
        actor_id=actor.id
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def resume_subscription(db: Session, subscription_id: uuid.UUID, reason: str, actor: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    validate_transition(subscription.status, "active")

    old_status = subscription.status
    subscription.status = "active"

    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state=old_status,
        to_state="active",
        reason=reason,
        actor_id=actor.id
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def renew_subscription(db: Session, subscription_id: uuid.UUID, reason: str, actor: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    plan = db.get(Plan, subscription.plan_id)
    if not plan.allow_renewal:
        raise ForbiddenException("The assigned plan does not permit renewals.", code="RENEWAL_NOT_ALLOWED")
    if plan.status != "active":
        raise ValidationException("Cannot renew onto a closed/expired plan.", code="PLAN_CLOSED")

    new_end_date = calculate_frequency_delta(plan.billing_frequency, subscription.end_date)
    subscription.end_date = new_end_date

    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state=subscription.status,
        to_state=subscription.status,
        reason=f"Renewed term until {new_end_date}. Reason: {reason}",
        actor_id=actor.id
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def close_subscription(db: Session, subscription_id: uuid.UUID, reason: str, actor: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    today = date.today()
    if today < subscription.end_date:
        plan = db.get(Plan, subscription.plan_id)
        if not plan.allow_early_close:
            raise ForbiddenException("The assigned plan does not permit early closure.", code="EARLY_CLOSE_NOT_ALLOWED")

    validate_transition(subscription.status, "closed")

    old_status = subscription.status
    subscription.status = "closed"
    subscription.next_billing_at = None

    add_subscription_event(
        db=db,
        subscription_id=subscription.id,
        from_state=old_status,
        to_state="closed",
        reason=reason,
        actor_id=actor.id
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def get_subscription(db: Session, subscription_id: uuid.UUID, user: User) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    if user.role == "customer":
        customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
        if not customer or customer.id != subscription.customer_id:
            raise ForbiddenException("You cannot view another customer's subscription.", code="IDOR_VIOLATION")

    return subscription


def list_subscriptions(
    db: Session,
    user: User,
    customer_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None
) -> List[Subscription]:
    query = select(Subscription)

    if user.role == "customer":
        customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
        if not customer:
            return []
        query = query.where(Subscription.customer_id == customer.id)
    elif customer_id:
        query = query.where(Subscription.customer_id == customer_id)

    if status:
        query = query.where(Subscription.status == status)

    return list(db.scalars(query.order_by(Subscription.created_at.desc())).all())


# Person 2 Shared Billing Contract Functions

def get_due_subscriptions(
    db: Session,
    as_of: date,
    cursor: Optional[str] = None,
    limit: int = 50
) -> DueSubscriptionListResponse:
    """
    Contract for Person 2 Recurring Billing Engine.
    Returns ACTIVE subscriptions with next_billing_at <= as_of.
    Excludes paused, closed, and non-activated subscriptions.
    """
    query = (
        select(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.next_billing_at != None,
            Subscription.next_billing_at <= as_of
        )
        .order_by(Subscription.next_billing_at.asc(), Subscription.id.asc())
    )

    all_due = list(db.scalars(query.limit(limit)).all())

    items = []
    for sub in all_due:
        plan = db.get(Plan, sub.plan_id)
        freq = plan.billing_frequency if plan else "monthly"

        lines = [
            DueSubscriptionLine(
                product_id=line.product_id,
                variant_id=line.variant_id,
                description=line.description,
                quantity=line.quantity,
                unit_price=str(line.unit_price),
                line_total=str(line.line_total)
            )
            for line in sub.lines
        ]

        items.append(
            DueSubscriptionItem(
                subscription_id=sub.id,
                customer_id=sub.customer_id,
                plan_id=sub.plan_id,
                plan_version_id=sub.plan_version_id,
                billing_frequency=freq,
                next_billing_at=sub.next_billing_at,
                currency=sub.currency,
                lines=lines
            )
        )

    return DueSubscriptionListResponse(
        items=items,
        as_of=as_of,
        total_due=len(items),
        next_cursor=None
    )


def advance_next_billing(
    db: Session,
    subscription_id: uuid.UUID,
    period_start: date,
    period_end: date
) -> Subscription:
    """
    Advances next_billing_at forward by plan frequency with month-end anchor day clamping.
    Called by Person 2 Billing Worker after successful invoice generation.
    """
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found.", code="SUBSCRIPTION_NOT_FOUND")

    plan = db.get(Plan, subscription.plan_id)
    freq = plan.billing_frequency if plan else "monthly"
    current_due = subscription.next_billing_at or period_start
    anchor = subscription.billing_anchor_day

    if freq == "daily":
        next_date = current_due + timedelta(days=1)
    elif freq == "weekly":
        next_date = current_due + timedelta(days=7)
    elif freq == "monthly":
        year = current_due.year + (current_due.month // 12)
        month = (current_due.month % 12) + 1
        next_date = clamp_date_to_month(year, month, anchor)
    elif freq == "yearly":
        year = current_due.year + 1
        next_date = clamp_date_to_month(year, current_due.month, anchor)
    else:
        next_date = current_due + timedelta(days=30)

    # Check if subscription reaches end date
    if next_date > subscription.end_date:
        subscription.next_billing_at = None
        subscription.status = "closed"
        add_subscription_event(
            db=db,
            subscription_id=subscription.id,
            from_state="active",
            to_state="closed",
            reason=f"Reached agreed end date ({subscription.end_date}). Automatically closed.",
            actor_id=None
        )
    else:
        subscription.next_billing_at = next_date

    db.commit()
    db.refresh(subscription)
    return subscription
