"""
Customer Portal Pydantic Schemas & DTOs.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CustomerProfileDTO(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    state_code: Optional[str] = None
    gstin: Optional[str] = None
    status: str
    segment: str

class CustomerProfileUpdate(BaseModel):
    phone: Optional[str] = None
    billing_address: Optional[str] = None

class PortalDashboardSummary(BaseModel):
    customer: CustomerProfileDTO
    active_subscriptions_count: int
    outstanding_balance: Decimal
    unpaid_invoices_count: int
    next_renewal_date: Optional[date] = None
    recent_subscriptions: List[Dict[str, Any]] = []
    recent_invoices: List[Dict[str, Any]] = []

class PortalOutstandingBalanceResponse(BaseModel):
    customer_id: str
    outstanding_balance: Decimal
    currency: str = "INR"
    has_unpaid_invoices: bool
    unpaid_count: int
