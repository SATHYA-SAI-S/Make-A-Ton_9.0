"""
Customer Requests Workflow Service.
Orchestrates request creation, validation, duplicate prevention, and Staff review.
Upon approval, executes subscription state transitions via SubscriptionPort,
dispatches notifications, records audit entries, and publishes events.
"""
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.errors import NotFoundError, ValidationError, PermissionDeniedError
from backend.app.portal.request_models import CustomerRequest
from backend.app.shared.registry import get_port
from backend.app.shared.events import publish

ALLOWED_TYPES = {"UPGRADE", "DOWNGRADE", "PAUSE", "CANCEL", "RENEWAL"}

def create_customer_request(
    db: Session,
    customer: Dict[str, Any],
    subscription_id: str,
    req_type: str,
    target_plan_id: Optional[str] = None,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new customer request with duplicate pending check."""
    req_type = req_type.upper().strip()
    if req_type not in ALLOWED_TYPES:
        raise ValidationError(f"Invalid request type '{req_type}'. Allowed: {', '.join(sorted(ALLOWED_TYPES))}")

    if req_type in {"UPGRADE", "DOWNGRADE"} and not target_plan_id:
        raise ValidationError(f"target_plan_id is required for request type '{req_type}'.")

    # Verify subscription belongs to customer
    sub_port = get_port("subscription")
    sub = sub_port.get(subscription_id)
    if not sub or sub.get("customer_id") != customer["id"]:
        raise NotFoundError("Subscription", subscription_id)

    # Prevent duplicate PENDING request for same subscription
    existing_pending = db.query(CustomerRequest).filter(
        CustomerRequest.subscription_id == subscription_id,
        CustomerRequest.status == "PENDING"
    ).first()

    if existing_pending:
        raise ValidationError(
            f"A pending request (#{existing_pending.id[:8]} - {existing_pending.type}) is already active for this subscription."
        )

    req_id = str(uuid.uuid4())
    req = CustomerRequest(
        id=req_id,
        customer_id=customer["id"],
        subscription_id=subscription_id,
        type=req_type,
        target_plan_id=target_plan_id,
        note=note,
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    db.add(req)
    db.commit()

    # Emit event
    publish("customer_request.created", {
        "request_id": req_id,
        "customer_id": customer["id"],
        "subscription_id": subscription_id,
        "type": req_type,
        "target_plan_id": target_plan_id
    }, actor_id=customer.get("user_id", customer["id"]))

    # Audit
    audit_port = get_port("audit")
    audit_port.emit(
        actor_id=customer.get("user_id", customer["id"]),
        actor_role="customer",
        action="customer_request.created",
        entity_type="customer_request",
        entity_id=req_id,
        after=req.to_dict(),
        meta={"subscription_id": subscription_id, "type": req_type}
    )

    return req.to_dict()

def list_customer_requests(
    db: Session,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    query = db.query(CustomerRequest)
    if customer_id:
        query = query.filter(CustomerRequest.customer_id == customer_id)
    if status and status != "ALL":
        query = query.filter(CustomerRequest.status == status)

    total = query.count()
    items = query.order_by(desc(CustomerRequest.created_at)).offset(offset).limit(limit).all()
    return [i.to_dict() for i in items], total

def get_customer_request_by_id(db: Session, request_id: str) -> CustomerRequest:
    req = db.query(CustomerRequest).filter(CustomerRequest.id == request_id).first()
    if not req:
        raise NotFoundError("CustomerRequest", request_id)
    return req

def review_customer_request(
    db: Session,
    request_id: str,
    action: str,
    decision_note: Optional[str],
    staff_user_id: str
) -> Dict[str, Any]:
    """Staff review: APPROVE or REJECT customer request."""
    req = get_customer_request_by_id(db, request_id)
    if req.status != "PENDING":
        raise ValidationError(f"Request cannot be reviewed. Current status: '{req.status}'")

    action = action.upper().strip()
    if action not in {"APPROVE", "REJECT"}:
        raise ValidationError("Action must be 'APPROVE' or 'REJECT'.")

    before_state = req.to_dict()
    sub_port = get_port("subscription")
    notif_port = get_port("notification")
    audit_port = get_port("audit")
    now = datetime.now(timezone.utc)

    if action == "REJECT":
        req.status = "REJECTED"
        req.decided_by = staff_user_id
        req.decided_at = now
        req.decision_note = decision_note
        db.commit()

        # Event & Notification & Audit
        publish("customer_request.rejected", {"request_id": req.id, "reason": decision_note}, actor_id=staff_user_id)
        notif_port.send(
            template="request_rejected",
            to="billing@customer.com",
            context={"request_type": req.type, "reason": decision_note},
            customer_id=req.customer_id
        )
        audit_port.emit(
            actor_id=staff_user_id,
            actor_role="staff",
            action="customer_request.rejected",
            entity_type="customer_request",
            entity_id=req.id,
            before=before_state,
            after=req.to_dict()
        )
        return req.to_dict()

    # Case: APPROVE -> Apply change to subscription
    req.status = "APPROVED"
    req.decided_by = staff_user_id
    req.decided_at = now
    req.decision_note = decision_note

    applied_ok = False
    error_msg = None

    try:
        if req.type in {"UPGRADE", "DOWNGRADE"}:
            applied_ok = sub_port.apply_plan_change(
                subscription_id=req.subscription_id,
                new_plan_id=req.target_plan_id,
                effective_date=date.today()
            )
        elif req.type == "PAUSE":
            applied_ok = sub_port.request_status_change(req.subscription_id, "PAUSE")
        elif req.type == "CANCEL":
            applied_ok = sub_port.request_status_change(
                req.subscription_id, "CLOSE", reason="CUSTOMER_CANCELLED"
            )
        elif req.type == "RENEWAL":
            applied_ok = sub_port.request_status_change(req.subscription_id, "RENEW")
    except Exception as e:
        error_msg = str(e)
        applied_ok = False

    if applied_ok:
        req.status = "APPLIED"
        publish("customer_request.applied", {
            "request_id": req.id,
            "subscription_id": req.subscription_id,
            "type": req.type
        }, actor_id=staff_user_id)
        notif_port.send(
            template="request_approved",
            to="billing@customer.com",
            context={"request_type": req.type, "status": "APPLIED"},
            customer_id=req.customer_id
        )
    else:
        req.status = "FAILED"
        req.decision_note = f"{decision_note or ''} [Failed: {error_msg or 'Subscription port rejected transition'}]"

    db.commit()

    audit_port.emit(
        actor_id=staff_user_id,
        actor_role="staff",
        action=f"customer_request.{req.status.lower()}",
        entity_type="customer_request",
        entity_id=req.id,
        before=before_state,
        after=req.to_dict()
    )

    return req.to_dict()
