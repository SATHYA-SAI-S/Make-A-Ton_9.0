from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from app.core.money import to_decimal
from app.shared.ports import (
    AuditPort,
    BillingControlPort,
    CustomerPort,
    InvoicePort,
    NotificationPort,
    PaymentPort,
    SubscriptionPort,
    TaxPreviewPort,
)
from app.shared.dto import (
    CustomerDTO,
    InvoiceDTO,
    InvoiceLineDTO,
    PaymentDTO,
    SubscriptionDTO,
    SubscriptionLineDTO,
    TaxBreakdownDTO,
    TaxLineInputDTO,
)


class FakeNotificationPort(NotificationPort):
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None, **kwargs) -> bool:
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
        self.customers: Dict[str, CustomerDTO] = {
            "cust-001": CustomerDTO(
                id="cust-001",
                user_id="usr-001",
                name="Acme Corp",
                email="billing@acme.com",
                phone="+91 98765 43210",
                state_code="KA",
                gstin="29ABCDE1234F1Z5",
                status="ACTIVE",
                segment="ENTERPRISE"
            ),
            "cust-002": CustomerDTO(
                id="cust-002",
                user_id="usr-002",
                name="Globex Inc",
                email="finance@globex.com",
                phone="+91 91234 56789",
                state_code="MH",
                gstin="27XYZAB5678C1Z2",
                status="ACTIVE",
                segment="MID_MARKET"
            ),
            "cust-101": CustomerDTO(
                id="cust-101",
                user_id="usr-cust-001",
                name="Acme Software Corp",
                email="billing@acme.com",
                phone="+91 98765 43210",
                billing_address="100 MG Road, Bengaluru, Karnataka, 560001",
                state_code="KA",
                gstin="29ABCDE1234F1Z5",
                status="ACTIVE",
                segment="ENTERPRISE"
            ),
            "cust-102": CustomerDTO(
                id="cust-102",
                user_id="usr-cust-002",
                name="TechCorp Logistics",
                email="ops@techcorp.com",
                phone="+91 91234 56789",
                billing_address="45 Anna Salai, Chennai, Tamil Nadu, 600002",
                state_code="TN",
                gstin="33AABCT9988G1Z2",
                status="ACTIVE",
                segment="MID_MARKET"
            ),
        }

    def get(self, customer_id: str) -> Optional[CustomerDTO]:
        return self.customers.get(customer_id)

    def get_by_user(self, user_id: str) -> Optional[CustomerDTO]:
        for c in self.customers.values():
            if c.user_id == user_id:
                return c
        return list(self.customers.values())[0] if self.customers else None


class FakeSubscriptionPort(SubscriptionPort):
    def __init__(self):
        self.subscriptions: Dict[str, SubscriptionDTO] = {
            "sub-1001": SubscriptionDTO(
                id="sub-1001",
                number="SUB-2026-0001",
                customer_id="cust-101",
                plan_id="plan-ent-monthly",
                plan_name="Enterprise Cloud Suite",
                status="ACTIVE",
                close_reason=None,
                start_date=date(2026, 1, 1),
                expiry_date=date(2027, 1, 1),
                next_billing_date=date(2026, 11, 1),
                payment_terms_days=30,
                billing_frequency="MONTHLY",
                currency="INR",
                lines=[
                    SubscriptionLineDTO(
                        id="sline-1",
                        product_id="prod-erp",
                        variant_id="var-odoo",
                        product_name="Cloud ERP (Odoo Edition)",
                        quantity=10,
                        unit_price=to_decimal("1560.00"),
                        amount=to_decimal("15600.00")
                    )
                ]
            ),
            "sub-1002": SubscriptionDTO(
                id="sub-1002",
                number="SUB-2026-0002",
                customer_id="cust-101",
                plan_id="plan-support-monthly",
                plan_name="24/7 Dedicated Support",
                status="ACTIVE",
                close_reason=None,
                start_date=date(2026, 2, 1),
                expiry_date=date(2027, 2, 1),
                next_billing_date=date(2026, 11, 1),
                payment_terms_days=15,
                billing_frequency="MONTHLY",
                currency="INR",
                lines=[
                    SubscriptionLineDTO(
                        id="sline-2",
                        product_id="prod-support",
                        product_name="Premium SLA Support",
                        quantity=1,
                        unit_price=to_decimal("5000.00"),
                        amount=to_decimal("5000.00")
                    )
                ]
            ),
            "sub-1003": SubscriptionDTO(
                id="sub-1003",
                number="SUB-2026-0003",
                customer_id="cust-102",
                plan_id="plan-growth-yearly",
                plan_name="Growth Yearly Tier",
                status="ACTIVE",
                close_reason=None,
                start_date=date(2026, 3, 1),
                expiry_date=date(2027, 3, 1),
                next_billing_date=date(2027, 3, 1),
                payment_terms_days=30,
                billing_frequency="YEARLY",
                currency="INR",
                lines=[
                    SubscriptionLineDTO(
                        id="sline-3",
                        product_id="prod-suite",
                        product_name="Operations Suite",
                        quantity=5,
                        unit_price=to_decimal("12000.00"),
                        amount=to_decimal("60000.00")
                    )
                ]
            )
        }

    def seed_subscription(self, sub: SubscriptionDTO):
        self.subscriptions[sub.id] = sub

    def get(self, subscription_id: str) -> Optional[SubscriptionDTO]:
        return self.subscriptions.get(subscription_id)

    def list_billable(self, as_of: date) -> List[SubscriptionDTO]:
        return [
            s for s in self.subscriptions.values()
            if s.status == "ACTIVE" and s.next_billing_date and s.next_billing_date <= as_of
        ]

    def set_next_billing_date(self, subscription_id: str, next_date: date) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].next_billing_date = next_date
            return True
        return False

    def apply_plan_change(self, subscription_id: str, new_plan_id: str, effective_date: date) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].plan_id = new_plan_id
            return True
        return False

    def request_status_change(self, subscription_id: str, action: str, reason: Optional[str] = None) -> bool:
        if subscription_id not in self.subscriptions:
            return False
        if action == "PAUSE":
            self.subscriptions[subscription_id].status = "PAUSED"
        elif action == "RESUME":
            self.subscriptions[subscription_id].status = "ACTIVE"
        elif action == "CLOSE":
            self.subscriptions[subscription_id].status = "CLOSED"
            self.subscriptions[subscription_id].close_reason = reason or "EARLY_CLOSURE"
        return True


class FakeInvoicePort(InvoicePort):
    def __init__(self):
        today = date.today()
        self.invoices: Dict[str, InvoiceDTO] = {
            "inv-2001": InvoiceDTO(
                id="inv-2001",
                number="INV-2026-0001",
                customer_id="cust-101",
                subscription_id="sub-1001",
                status="PAID",
                invoice_date=today - timedelta(days=60),
                due_date=today - timedelta(days=30),
                subtotal=to_decimal("15600.00"),
                discount_total=to_decimal("0.00"),
                tax_total=to_decimal("2808.00"),
                total=to_decimal("18408.00"),
                amount_paid=to_decimal("18408.00"),
                balance=to_decimal("0.00"),
                lines=[
                    InvoiceLineDTO(
                        id="iline-1",
                        product_id="prod-erp",
                        description="Cloud ERP (Odoo Edition) - Month 8",
                        quantity=10,
                        unit_price=to_decimal("1560.00"),
                        discount_amount=to_decimal("0.00"),
                        tax_rate=to_decimal("18.00"),
                        tax_amount=to_decimal("2808.00"),
                        line_total=to_decimal("18408.00")
                    )
                ]
            ),
            "inv-2002": InvoiceDTO(
                id="inv-2002",
                number="INV-2026-0002",
                customer_id="cust-101",
                subscription_id="sub-1001",
                status="CONFIRMED",
                invoice_date=today - timedelta(days=35),
                due_date=today - timedelta(days=5),
                subtotal=to_decimal("15600.00"),
                discount_total=to_decimal("0.00"),
                tax_total=to_decimal("2808.00"),
                total=to_decimal("18408.00"),
                amount_paid=to_decimal("6000.00"),
                balance=to_decimal("12408.00"),
                lines=[
                    InvoiceLineDTO(
                        id="iline-2",
                        product_id="prod-erp",
                        description="Cloud ERP (Odoo Edition) - Month 9",
                        quantity=10,
                        unit_price=to_decimal("1560.00"),
                        discount_amount=to_decimal("0.00"),
                        tax_rate=to_decimal("18.00"),
                        tax_amount=to_decimal("2808.00"),
                        line_total=to_decimal("18408.00")
                    )
                ]
            )
        }

    def list_for_customer(self, customer_id: str, filters: Optional[Dict[str, Any]] = None) -> List[InvoiceDTO]:
        results = [inv for inv in self.invoices.values() if inv.customer_id == customer_id]
        today = date.today()
        for r in results:
            r.is_overdue = (r.status in ["CONFIRMED", "PARTIALLY_PAID"]) and (r.balance > Decimal("0.00")) and (r.due_date < today)
        return results

    def get(self, invoice_id: str) -> Optional[InvoiceDTO]:
        inv = self.invoices.get(invoice_id)
        if inv:
            today = date.today()
            inv.is_overdue = (inv.status in ["CONFIRMED", "PARTIALLY_PAID"]) and (inv.balance > Decimal("0.00")) and (inv.due_date < today)
        return inv

    def pdf(self, invoice_id: str) -> bytes:
        inv = self.get(invoice_id)
        content = f"%PDF-1.4\n1 0 obj<< /Title (Invoice {inv.number if inv else invoice_id}) >>\nendobj\ntrailer<<>>\n%%EOF"
        return content.encode("utf-8")


class FakePaymentPort(PaymentPort):
    def __init__(self):
        self.payments: List[PaymentDTO] = [
            PaymentDTO(
                id="pay-3001",
                customer_id="cust-101",
                method="UPI",
                amount=to_decimal("18408.00"),
                payment_date=datetime.now(timezone.utc) - timedelta(days=28),
                reference="UPI/2026/89123891",
                status="RECORDED",
                notes="Monthly billing settlement"
            ),
            PaymentDTO(
                id="pay-3002",
                customer_id="cust-101",
                method="BANK_TRANSFER",
                amount=to_decimal("6000.00"),
                payment_date=datetime.now(timezone.utc) - timedelta(days=4),
                reference="NEFT/8812391209",
                status="RECORDED",
                notes="Partial payment towards INV-2026-0002"
            )
        ]

    def list_for_customer(self, customer_id: str) -> List[PaymentDTO]:
        return [p for p in self.payments if p.customer_id == customer_id]

    def outstanding_for_customer(self, customer_id: str) -> Decimal:
        return to_decimal("12408.00") if customer_id == "cust-101" else to_decimal("0.00")


class FakeTaxPreviewPort(TaxPreviewPort):
    def preview(self, lines: Any, customer: Any, as_of: date) -> List[TaxBreakdownDTO]:
        state_code = customer.get("state_code", "KA") if hasattr(customer, "get") else getattr(customer, "state_code", "KA")
        return [
            TaxBreakdownDTO(
                rule_name="GST 18%",
                tax_type="IGST" if state_code != "KA" else "GST",
                rate=Decimal("18.00"),
                base_amount=Decimal("1000.00"),
                tax_amount=Decimal("180.00")
            )
        ]


class FakeBillingControlPort(BillingControlPort):
    def run_now(self, as_of: Optional[date] = None, dry_run: bool = False) -> Dict[str, Any]:
        return {"status": "SUCCESS", "invoices_created": 3, "run_id": str(uuid.uuid4())}

    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [{"id": "run-1", "started_at": datetime.now(timezone.utc).isoformat(), "status": "COMPLETED", "invoices_created": 5}]


_fake_instances: Dict[str, Any] = {}


def get_fake_port(name: str) -> Any:
    if name not in _fake_instances:
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
        _fake_instances.update(fakes)
    return _fake_instances.get(name)

