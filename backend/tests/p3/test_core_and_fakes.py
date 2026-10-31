"""
Unit tests for Person 3 Foundation:
- Money precision & ROUND_HALF_UP banker rounding
- Error responses
- Pagination DTOs
- Fake Ports contracts & data retrieval
- Registry fallback mechanism
"""
from decimal import Decimal
import pytest
from app.core.money import to_money, format_money, format_currency
from app.core.errors import SubscriptIQError, NotFoundError, PermissionDeniedError
from app.core.pagination import PageParams, PageResponse
from app.shared.registry import get_port, register_port, clear_registry
from app.shared.events import publish, subscribe

def test_money_rounding_half_up():
    assert to_money("10.005") == Decimal("10.01")
    assert to_money("10.004") == Decimal("10.00")
    assert to_money(100) == Decimal("100.00")
    assert format_money("14999.50") == "14,999.50"
    assert format_currency("14999.50") == "₹14,999.50"

def test_money_invalid_rejects():
    with pytest.raises(ValueError):
        to_money("not-a-number")

def test_error_standardized_shape():
    err = NotFoundError("Subscription", "sub-123")
    data = err.to_dict()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "sub-123" in data["error"]["message"]
    assert data["error"]["details"]["id"] == "sub-123"

def test_pagination_helper():
    params = PageParams(page=2, page_size=10)
    assert params.offset == 10
    assert params.limit == 10
    
    resp = PageResponse.create(items=["a", "b"], total=25, params=params)
    assert resp.page == 2
    assert resp.page_size == 10
    assert resp.total == 25
    assert resp.items == ["a", "b"]

def test_shared_ports_fakes():
    clear_registry()
    sub_port = get_port("subscription")
    assert sub_port is not None
    
    sub = sub_port.get("sub-1001")
    assert sub is not None
    assert sub["customer_id"] == "cust-101"
    assert sub["status"] == "ACTIVE"

    cust_port = get_port("customer")
    cust = cust_port.get("cust-101")
    assert cust is not None
    assert cust["email"] == "billing@acme.com"

    inv_port = get_port("invoice")
    invoices = inv_port.list_for_customer("cust-101")
    assert len(invoices) >= 1

    pay_port = get_port("payment")
    outstanding = pay_port.outstanding_for_customer("cust-101")
    assert outstanding > Decimal("0.00")

def test_events_publishing():
    received = []
    def handler(evt):
        received.append(evt)

    subscribe("test.event", handler)
    publish("test.event", {"hello": "world"})
    assert len(received) == 1
    assert received[0].payload == {"hello": "world"}
