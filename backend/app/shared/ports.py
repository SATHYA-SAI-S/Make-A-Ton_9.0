from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from backend.app.shared.dto import (
    CustomerDTO,
    InvoiceDTO,
    PaymentDTO,
    SubscriptionDTO,
    TaxBreakdownDTO,
    TaxLineInputDTO,
)

class NotificationPort(ABC):
    @abstractmethod
    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None) -> bool:
        """Sends transactional notification using Jinja2 template."""
        pass

class AuditPort(ABC):
    @abstractmethod
    def emit(
        self,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Asynchronously emits an immutable audit log entry."""
        pass

class SubscriptionPort(ABC):
    @abstractmethod
    def get(self, subscription_id: str) -> Optional[SubscriptionDTO]:
        pass

    @abstractmethod
    def list_billable(self, as_of: date) -> List[SubscriptionDTO]:
        """Lists active subscriptions due for billing (status=ACTIVE and next_billing_date <= as_of)."""
        pass

    @abstractmethod
    def set_next_billing_date(self, subscription_id: str, next_date: date) -> None:
        """The only method Person 2 uses to update Person 1's subscription."""
        pass

    @abstractmethod
    def apply_plan_change(self, subscription_id: str, new_plan_id: str, effective_date: date) -> None:
        pass

    @abstractmethod
    def request_status_change(self, subscription_id: str, action: str) -> None:
        pass

class CustomerPort(ABC):
    @abstractmethod
    def get(self, customer_id: str) -> Optional[CustomerDTO]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> Optional[CustomerDTO]:
        pass

class TaxPreviewPort(ABC):
    @abstractmethod
    def preview(self, lines: List[TaxLineInputDTO], customer: CustomerDTO, as_of: date) -> List[TaxBreakdownDTO]:
        """Returns tax breakdown for quote preview without writing to database."""
        pass

class InvoicePort(ABC):
    @abstractmethod
    def list_for_customer(self, customer_id: str, filters: Optional[Dict[str, Any]] = None) -> List[InvoiceDTO]:
        pass

    @abstractmethod
    def get(self, invoice_id: str) -> Optional[InvoiceDTO]:
        pass

    @abstractmethod
    def pdf(self, invoice_id: str) -> bytes:
        pass

class PaymentPort(ABC):
    @abstractmethod
    def list_for_customer(self, customer_id: str) -> List[PaymentDTO]:
        pass

    @abstractmethod
    def outstanding_for_customer(self, customer_id: str) -> Decimal:
        pass

class BillingControlPort(ABC):
    @abstractmethod
    def run_now(self, as_of: Optional[date] = None, dry_run: bool = False) -> Dict[str, Any]:
        pass

    @abstractmethod
    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass
