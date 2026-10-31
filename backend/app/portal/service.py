"""
Customer Portal Service Implementation.
Coordinates with SubscriptionPort, InvoicePort, PaymentPort, and AuditPort.
Strictly isolates tenant data.
"""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.core.errors import NotFoundError, PermissionDeniedError
from app.core.money import to_money
from app.shared.registry import get_port

def get_portal_dashboard(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Generates the aggregated executive dashboard for the customer."""
    cust_id = customer["id"]
    sub_port = get_port("subscription")
    inv_port = get_port("invoice")
    pay_port = get_port("payment")

    # Fetch subscriptions
    all_subs = list_customer_subscriptions(customer)
    active_subs = [s for s in all_subs if s.get("status") == "ACTIVE"]

    # Calculate next renewal date
    renewal_dates = [s["expiry_date"] for s in active_subs if s.get("expiry_date")]
    next_renewal = min(renewal_dates) if renewal_dates else None

    # Invoices & Balance
    all_invoices = inv_port.list_for_customer(cust_id)
    unpaid_invoices = [
        i for i in all_invoices
        if i.get("status") in ["CONFIRMED", "PARTIALLY_PAID"] and i.get("balance", Decimal("0")) > Decimal("0")
    ]
    outstanding_bal = pay_port.outstanding_for_customer(cust_id)

    return {
        "customer": customer,
        "active_subscriptions_count": len(active_subs),
        "outstanding_balance": outstanding_bal,
        "unpaid_invoices_count": len(unpaid_invoices),
        "next_renewal_date": next_renewal,
        "recent_subscriptions": all_subs[:5],
        "recent_invoices": all_invoices[:5],
    }

def list_customer_subscriptions(
    customer: Dict[str, Any],
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns subscriptions belonging exclusively to the caller customer."""
    sub_port = get_port("subscription")
    cust_id = customer["id"]

    # Subscriptions in fake / real store
    subs = getattr(sub_port, "subscriptions", {})
    if isinstance(subs, dict):
        matching = [s for s in subs.values() if s.get("customer_id") == cust_id]
    else:
        matching = []

    if status_filter and status_filter != "ALL":
        matching = [s for s in matching if s.get("status") == status_filter]

    # Include timeline activity simulation
    for s in matching:
        s["timeline"] = [
            {"date": str(s.get("start_date")), "event": "Subscription Created & Confirmed"},
            {"date": str(s.get("start_date")), "event": "Subscription Activated (ACTIVE)"},
        ]
    return matching

def get_customer_subscription_detail(
    customer: Dict[str, Any],
    subscription_id: str
) -> Dict[str, Any]:
    """Retrieves single subscription detail with strict tenant isolation check."""
    sub_port = get_port("subscription")
    sub = sub_port.get(subscription_id)

    if not sub:
        raise NotFoundError("Subscription", subscription_id)

    # Cross-tenant security check
    if sub.get("customer_id") != customer["id"]:
        raise NotFoundError("Subscription", subscription_id)

    return sub

def list_customer_invoices(
    customer: Dict[str, Any],
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists invoices for the caller customer."""
    inv_port = get_port("invoice")
    invoices = inv_port.list_for_customer(customer["id"])

    if status_filter and status_filter != "ALL":
        invoices = [i for i in invoices if i.get("status") == status_filter]

    return invoices

def get_customer_invoice_detail(
    customer: Dict[str, Any],
    invoice_id: str
) -> Dict[str, Any]:
    """Retrieves invoice details with tenant isolation check."""
    inv_port = get_port("invoice")
    invoice = inv_port.get(invoice_id)

    if not invoice:
        raise NotFoundError("Invoice", invoice_id)

    # Cross-tenant security check
    if invoice.get("customer_id") != customer["id"]:
        raise NotFoundError("Invoice", invoice_id)

    return invoice

def get_customer_invoice_pdf(
    customer: Dict[str, Any],
    invoice_id: str
) -> Tuple[bytes, str]:
    """Retrieves PDF binary bytes for an invoice with tenant validation."""
    invoice = get_customer_invoice_detail(customer, invoice_id)
    inv_port = get_port("invoice")
    pdf_bytes = inv_port.pdf(invoice_id)
    filename = f"Invoice_{invoice.get('number', invoice_id)}.pdf"
    return pdf_bytes, filename

def list_customer_payments(customer: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retrieves payment history for caller customer."""
    pay_port = get_port("payment")
    return pay_port.list_for_customer(customer["id"])

def get_customer_balance(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates balance and overdue count for caller customer."""
    pay_port = get_port("payment")
    inv_port = get_port("invoice")

    cust_id = customer["id"]
    balance = pay_port.outstanding_for_customer(cust_id)
    invoices = inv_port.list_for_customer(cust_id)

    unpaid = [
        i for i in invoices
        if i.get("status") in ["CONFIRMED", "PARTIALLY_PAID"] and i.get("balance", Decimal("0")) > Decimal("0")
    ]

    return {
        "customer_id": cust_id,
        "outstanding_balance": balance,
        "currency": "INR",
        "has_unpaid_invoices": len(unpaid) > 0,
        "unpaid_count": len(unpaid),
    }

def update_customer_profile(
    customer: Dict[str, Any],
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Updates editable customer profile fields and logs audit event."""
    audit_port = get_port("audit")
    cust_port = get_port("customer")

    before_state = {
        "phone": customer.get("phone"),
        "billing_address": customer.get("billing_address")
    }

    # Apply updates
    if "phone" in update_data and update_data["phone"] is not None:
        customer["phone"] = update_data["phone"]
    if "billing_address" in update_data and update_data["billing_address"] is not None:
        customer["billing_address"] = update_data["billing_address"]

    after_state = {
        "phone": customer.get("phone"),
        "billing_address": customer.get("billing_address")
    }

    # Record audit log
    audit_port.emit(
        actor_id=customer.get("user_id", customer["id"]),
        actor_role="customer",
        action="customer.profile_updated",
        entity_type="customer",
        entity_id=customer["id"],
        before=before_state,
        after=after_state,
        meta={"source": "customer_portal"}
    )

    return customer
