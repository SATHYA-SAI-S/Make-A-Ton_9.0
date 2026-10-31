"""
High-fidelity Fake Port Implementations.
Ensures Person 3 is completely autonomous and never blocked by pending merges.
All data strictly mirrors the contracts in Document 00 section 6.4.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.money import to_money
from backend.app.shared.ports import (
    AuditPort,
    BillingControlPort,
    CustomerPort,
    InvoicePort,
    NotificationPort,
    PaymentPort,
    SubscriptionPort,
    TaxPreviewPort,
)

class FakeNotificationPort(NotificationPort):
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None) -> bool:
        self.sent_messages.append({
            "template": template,
            "to": to,
            "context": context,
            "customer_id": customer_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return True

class FakeAuditPort(AuditPort):
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def emit(
        self,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        actor_role: str = "system",
        request_id: Optional[str] = None
    ) -> str:
        log_id = str(uuid.uuid4())
        self.logs.append({
            "id": log_id,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before": before,
            "after": after,
            "meta": meta or {},
            "request_id": request_id or str(uuid.uuid4())[:8]
        })
        return log_id

class FakeCustomerPort(CustomerPort):
    def __init__(self):
        self.customers = {
            "cust-101": {
                "id": "cust-101",
                "user_id": "usr-cust-001",
                "name": "Acme Software Corp",
                "email": "billing@acme.com",
                "phone": "+91 98765 43210",
                "billing_address": "100 MG Road, Bengaluru, Karnataka, 560001",
                "state_code": "KA",
                "gstin": "29ABCDE1234F1Z5",
                "status": "ACTIVE",
                "segment": "ENTERPRISE",
                "created_at": "2026-01-15T09:00:00Z"
            },
            "cust-102": {
                "id": "cust-102",
                "user_id": "usr-cust-002",
                "name": "TechCorp Logistics",
                "email": "ops@techcorp.com",
                "phone": "+91 91234 56789",
                "billing_address": "45 Anna Salai, Chennai, Tamil Nadu, 600002",
                "state_code": "TN",
                "gstin": "33AABCT9988G1Z2",
                "status": "ACTIVE",
                "segment": "MID_MARKET",
                "created_at": "2026-03-10T11:00:00Z"
            }
        }

    def get(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self.customers.get(customer_id)

    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        for c in self.customers.values():
            if c.get("user_id") == user_id:
                return c
        return None

class FakeSubscriptionPort(SubscriptionPort):
    def __init__(self):
        self.subscriptions = {
            "sub-1001": {
                "id": "sub-1001",
                "number": "SUB-2026-0001",
                "customer_id": "cust-101",
                "plan_id": "plan-ent-monthly",
                "plan_name": "Enterprise Cloud Suite",
                "status": "ACTIVE",
                "close_reason": None,
                "start_date": date(2026, 1, 1),
                "expiry_date": date(2027, 1, 1),
                "next_billing_date": date(2026, 11, 1),
                "payment_terms_days": 30,
                "billing_frequency": "MONTHLY",
                "currency": "INR",
                "lines": [
                    {
                        "id": "sline-1",
                        "product_id": "prod-erp",
                        "variant_id": "var-odoo",
                        "product_name": "Cloud ERP (Odoo Edition)",
                        "quantity": 10,
                        "unit_price": to_money("1560.00"),
                        "amount": to_money("15600.00")
                    }
                ]
            },
            "sub-1002": {
                "id": "sub-1002",
                "number": "SUB-2026-0002",
                "customer_id": "cust-101",
                "plan_id": "plan-support-monthly",
                "plan_name": "24/7 Dedicated Support",
                "status": "ACTIVE",
                "close_reason": None,
                "start_date": date(2026, 2, 1),
                "expiry_date": date(2027, 2, 1),
                "next_billing_date": date(2026, 11, 1),
                "payment_terms_days": 15,
                "billing_frequency": "MONTHLY",
                "currency": "INR",
                "lines": [
                    {
                        "id": "sline-2",
                        "product_id": "prod-support",
                        "product_name": "Premium SLA Support",
                        "quantity": 1,
                        "unit_price": to_money("5000.00"),
                        "amount": to_money("5000.00")
                    }
                ]
            },
            "sub-1003": {
                "id": "sub-1003",
                "number": "SUB-2026-0003",
                "customer_id": "cust-102",
                "plan_id": "plan-growth-yearly",
                "plan_name": "Growth Yearly Tier",
                "status": "ACTIVE",
                "close_reason": None,
                "start_date": date(2026, 3, 1),
                "expiry_date": date(2027, 3, 1),
                "next_billing_date": date(2027, 3, 1),
                "payment_terms_days": 30,
                "billing_frequency": "YEARLY",
                "currency": "INR",
                "lines": [
                    {
                        "id": "sline-3",
                        "product_id": "prod-suite",
                        "product_name": "Operations Suite",
                        "quantity": 5,
                        "unit_price": to_money("12000.00"),
                        "amount": to_money("60000.00")
                    }
                ]
            }
        }

    def get(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        return self.subscriptions.get(subscription_id)

    def list_billable(self, as_of: date) -> List[Dict[str, Any]]:
        return [
            s for s in self.subscriptions.values()
            if s["status"] == "ACTIVE" and s.get("next_billing_date") and s["next_billing_date"] <= as_of
        ]

    def set_next_billing_date(self, subscription_id: str, next_date: date) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["next_billing_date"] = next_date
            return True
        return False

    def apply_plan_change(self, subscription_id: str, new_plan_id: str, effective_date: date) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["plan_id"] = new_plan_id
            return True
        return False

    def request_status_change(self, subscription_id: str, action: str, reason: Optional[str] = None) -> bool:
        if subscription_id not in self.subscriptions:
            return False
        if action == "PAUSE":
            self.subscriptions[subscription_id]["status"] = "PAUSED"
        elif action == "RESUME":
            self.subscriptions[subscription_id]["status"] = "ACTIVE"
        elif action == "CLOSE":
            self.subscriptions[subscription_id]["status"] = "CLOSED"
            self.subscriptions[subscription_id]["close_reason"] = reason or "EARLY_CLOSURE"
        return True

class FakeInvoicePort(InvoicePort):
    def __init__(self):
        today = date.today()
        self.invoices = {
            "inv-2001": {
                "id": "inv-2001",
                "number": "INV-2026-0001",
                "customer_id": "cust-101",
                "subscription_id": "sub-1001",
                "status": "PAID",
                "invoice_date": today - timedelta(days=60),
                "due_date": today - timedelta(days=30),
                "subtotal": to_money("15600.00"),
                "discount_total": to_money("0.00"),
                "tax_total": to_money("2808.00"),
                "total": to_money("18408.00"),
                "amount_paid": to_money("18408.00"),
                "balance": to_money("0.00"),
                "lines": [
                    {
                        "id": "iline-1",
                        "product_id": "prod-erp",
                        "description": "Cloud ERP (Odoo Edition) - Month 8",
                        "quantity": 10,
                        "unit_price": to_money("1560.00"),
                        "discount_amount": to_money("0.00"),
                        "tax_rate": to_money("18.00"),
                        "tax_amount": to_money("2808.00"),
                        "line_total": to_money("18408.00")
                    }
                ]
            },
            "inv-2002": {
                "id": "inv-2002",
                "number": "INV-2026-0002",
                "customer_id": "cust-101",
                "subscription_id": "sub-1001",
                "status": "CONFIRMED",
                "invoice_date": today - timedelta(days=35),
                "due_date": today - timedelta(days=5),
                "subtotal": to_money("15600.00"),
                "discount_total": to_money("0.00"),
                "tax_total": to_money("2808.00"),
                "total": to_money("18408.00"),
                "amount_paid": to_money("6000.00"),
                "balance": to_money("12408.00"),
                "lines": [
                    {
                        "id": "iline-2",
                        "product_id": "prod-erp",
                        "description": "Cloud ERP (Odoo Edition) - Month 9",
                        "quantity": 10,
                        "unit_price": to_money("1560.00"),
                        "discount_amount": to_money("0.00"),
                        "tax_rate": to_money("18.00"),
                        "tax_amount": to_money("2808.00"),
                        "line_total": to_money("18408.00")
                    }
                ]
            }
        }

    def list_for_customer(self, customer_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = [inv for inv in self.invoices.values() if inv["customer_id"] == customer_id]
        today = date.today()
        for r in results:
            r["is_overdue"] = (r["status"] in ["CONFIRMED", "PARTIALLY_PAID"]) and (r["balance"] > Decimal("0.00")) and (r["due_date"] < today)
        return results

    def get(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        inv = self.invoices.get(invoice_id)
        if inv:
            today = date.today()
            inv["is_overdue"] = (inv["status"] in ["CONFIRMED", "PARTIALLY_PAID"]) and (inv["balance"] > Decimal("0.00")) and (inv["due_date"] < today)
        return inv

    def pdf(self, invoice_id: str) -> bytes:
        inv = self.get(invoice_id)
        # Return valid PDF header bytes
        content = f"%PDF-1.4\n1 0 obj<< /Title (Invoice {inv['number'] if inv else invoice_id}) >>\nendobj\ntrailer<<>>\n%%EOF"
        return content.encode("utf-8")

class FakePaymentPort(PaymentPort):
    def __init__(self):
        self.payments = [
            {
                "id": "pay-3001",
                "customer_id": "cust-101",
                "method": "UPI",
                "amount": to_money("18408.00"),
                "payment_date": date.today() - timedelta(days=28),
                "reference": "UPI/2026/89123891",
                "status": "RECORDED",
                "notes": "Monthly billing settlement"
            },
            {
                "id": "pay-3002",
                "customer_id": "cust-101",
                "method": "BANK_TRANSFER",
                "amount": to_money("6000.00"),
                "payment_date": date.today() - timedelta(days=4),
                "reference": "NEFT/8812391209",
                "status": "RECORDED",
                "notes": "Partial payment towards INV-2026-0002"
            }
        ]

    def list_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        return [p for p in self.payments if p["customer_id"] == customer_id]

    def outstanding_for_customer(self, customer_id: str) -> Decimal:
        return to_money("12408.00") if customer_id == "cust-101" else to_money("0.00")

class FakeTaxPreviewPort(TaxPreviewPort):
    def preview(self, lines: List[Dict[str, Any]], customer: Dict[str, Any], as_of: date) -> List[Dict[str, Any]]:
        return [{"line_id": l.get("id"), "tax_rate": Decimal("18.00"), "tax_amount": to_money(Decimal(str(l.get("amount", 0))) * Decimal("0.18"))} for l in lines]

class FakeBillingControlPort(BillingControlPort):
    def run_now(self, as_of: date) -> Dict[str, Any]:
        return {"status": "SUCCESS", "invoices_created": 3, "run_id": str(uuid.uuid4())}

    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [{"id": "run-1", "started_at": datetime.now(timezone.utc).isoformat(), "status": "COMPLETED", "invoices_created": 5}]

def get_fake_port(name: str) -> Any:
    fakes = {
        "notification": FakeNotificationPort(),
        "audit": FakeAuditPort(),
        "subscription": FakeSubscriptionPort(),
        "customer": FakeCustomerPort(),
        "invoice": FakeInvoicePort(),
        "payment": FakePaymentPort(),
        "tax_preview": FakeTaxPreviewPort(),
        "billing_control": FakeBillingControlPort(),
    }
    return fakes.get(name)
