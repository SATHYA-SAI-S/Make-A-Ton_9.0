from decimal import Decimal
import pytest
from app.core.money import to_decimal, format_money, round_money
from app.shared.registry import get_port, register_port
from app.shared.ports import NotificationPort
from app.main import app
from fastapi.testclient import TestClient

def test_money_helpers():
    d1 = to_decimal("120.456")
    assert d1 == Decimal("120.46")
    assert format_money(d1) == "120.46"

    d2 = to_decimal(50)
    assert d2 == Decimal("50.00")
    assert format_money(d2) == "50.00"

    with pytest.raises(ValueError):
        to_decimal("invalid-money")

def test_ports_and_registry():
    notif_port = get_port("notification")
    assert notif_port is not None
    assert isinstance(notif_port, NotificationPort)

    sent = notif_port.send(template="test", to="test@brightloop.com", context={"user": "Sam"})
    assert sent is True

def test_fastapi_health():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
