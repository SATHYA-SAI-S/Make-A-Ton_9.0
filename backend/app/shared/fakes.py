from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from app.shared.ports import (
    NotificationPort,
    AuditPort,
    SubscriptionPort,
    CustomerPort,
    TaxPreviewPort,
    InvoicePort,
    PaymentPort,
    BillingControlPort,
)
from app.shared.dto import (
    CustomerDTO,
    InvoiceDTO,
    PaymentDTO,
    SubscriptionDTO,
    SubscriptionLineDTO,
    TaxBreakdownDTO,
    TaxLineInputDTO,
)

class FakeNotificationPort(NotificationPort):
    def __init__(self):
        self.sent_messages = []

    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None, **kwargs) -> bool:
        self.sent_messages.append({"template": template, "to": to, "context": context, "customer_id": customer_id})
        return True

class FakeAuditPort(AuditPort):
    def __init__(self):
        self.logs = []

    def emit(self, actor_id: str, action: str, entity_type: str, entity_id: str, before=None, after=None, meta=None):
        self.logs.append({
            "actor_id": actor_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before": before,
            "after": after,
            "meta": meta
        })

class FakeSubscriptionPort(SubscriptionPort):
    def __init__(self):
        self.subscriptions: Dict[str, SubscriptionDTO] = {}

    def seed_subscription(self, sub: SubscriptionDTO):
        self.subscriptions[sub.id] = sub

    def get(self, subscription_id: str) -> Optional[SubscriptionDTO]:
        return self.subscriptions.get(subscription_id)

    def list_billable(self, as_of: date) -> List[SubscriptionDTO]:
        return [
            s for s in self.subscriptions.values()
            if s.status == "ACTIVE" and s.next_billing_date and s.next_billing_date <= as_of
        ]

    def set_next_billing_date(self, subscription_id: str, next_date: date) -> None:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].next_billing_date = next_date

    def apply_plan_change(self, subscription_id: str, new_plan_id: str, effective_date: date) -> None:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].plan_id = new_plan_id

    def request_status_change(self, subscription_id: str, action: str) -> None:
        if subscription_id in self.subscriptions:
            if action == "PAUSE":
                self.subscriptions[subscription_id].status = "PAUSED"
            elif action == "RESUME":
                self.subscriptions[subscription_id].status = "ACTIVE"
            elif action == "CLOSE":
                self.subscriptions[subscription_id].status = "CLOSED"

class FakeCustomerPort(CustomerPort):
    def __init__(self):
        self.customers: Dict[str, CustomerDTO] = {
            "cust-001": CustomerDTO(
                id="cust-001",
                name="Acme Corp",
                email="billing@acme.com",
                state_code="KA",
                gstin="29ABCDE1234F1Z5"
            ),
            "cust-002": CustomerDTO(
                id="cust-002",
                name="Globex Inc",
                email="finance@globex.com",
                state_code="MH",
                gstin="27XYZAB5678C1Z2"
            )
        }

    def get(self, customer_id: str) -> Optional[CustomerDTO]:
        return self.customers.get(customer_id)

    def get_by_user(self, user_id: str) -> Optional[CustomerDTO]:
        for c in self.customers.values():
            if c.user_id == user_id:
                return c
        return list(self.customers.values())[0] if self.customers else None

class FakeTaxPreviewPort(TaxPreviewPort):
    def preview(self, lines: List[TaxLineInputDTO], customer: CustomerDTO, as_of: date) -> List[TaxBreakdownDTO]:
        return [
            TaxBreakdownDTO(
                rule_name="GST 18%",
                tax_type="IGST" if customer.state_code != "KA" else "GST",
                rate=Decimal("18.00"),
                base_amount=Decimal("1000.00"),
                tax_amount=Decimal("180.00")
            )
        ]

_fake_instances = {
    "notification": FakeNotificationPort(),
    "audit": FakeAuditPort(),
    "subscription": FakeSubscriptionPort(),
    "customer": FakeCustomerPort(),
    "tax_preview": FakeTaxPreviewPort()
}

def get_fake_port(name: str):
    return _fake_instances.get(name)
