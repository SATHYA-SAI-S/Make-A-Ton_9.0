"""
Shared Ports (Contract Interfaces) across SubscriptIQ modules.
Defines pure abstract interfaces to eliminate direct coupling.
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

class NotificationPort(ABC):
    @abstractmethod
    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None) -> bool:
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
        actor_role: str = "system",
        request_id: Optional[str] = None
    ) -> str:
        """Emits an audit entry. Returns generated audit ID."""
        pass

class SubscriptionPort(ABC):
    @abstractmethod
    def get(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_billable(self, as_of: date) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def set_next_billing_date(self, subscription_id: str, next_date: date) -> bool:
        pass

    @abstractmethod
    def apply_plan_change(self, subscription_id: str, new_plan_id: str, effective_date: date) -> bool:
        pass

    @abstractmethod
    def request_status_change(self, subscription_id: str, action: str, reason: Optional[str] = None) -> bool:
        pass

class CustomerPort(ABC):
    @abstractmethod
    def get(self, customer_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

class TaxPreviewPort(ABC):
    @abstractmethod
    def preview(self, lines: List[Dict[str, Any]], customer: Dict[str, Any], as_of: date) -> List[Dict[str, Any]]:
        pass

class InvoicePort(ABC):
    @abstractmethod
    def list_for_customer(self, customer_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def pdf(self, invoice_id: str) -> bytes:
        pass

class PaymentPort(ABC):
    @abstractmethod
    def list_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def outstanding_for_customer(self, customer_id: str) -> Decimal:
        pass

class BillingControlPort(ABC):
    @abstractmethod
    def run_now(self, as_of: date) -> Dict[str, Any]:
        pass

    @abstractmethod
    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass
