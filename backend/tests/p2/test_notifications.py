import pytest
from fastapi.testclient import TestClient
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.notifications.models import Notification
from backend.app.notifications.service import NotificationService
from backend.app.main import app

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_template_rendering():
    service = NotificationService(mock_send=True)
    html = service.render("password_reset", {"name": "Alice", "reset_link": "https://brightloop.com/reset?token=abc"})
    assert "Alice" in html
    assert "https://brightloop.com/reset?token=abc" in html

    inv_html = service.render("invoice_generated", {
        "customer_name": "Bob",
        "invoice_number": "INV-2026-0001",
        "period_start": "2026-10-01",
        "period_end": "2026-10-31",
        "currency": "INR",
        "total": "4500.00",
        "due_date": "2026-11-15"
    })
    assert "INV-2026-0001" in inv_html
    assert "4500.00" in inv_html

def test_notification_mock_send_and_db_record():
    service = NotificationService(mock_send=True)
    success = service.send(
        template="invoice_confirmed",
        to="alice@brightloop.com",
        context={"customer_name": "Alice", "invoice_number": "INV-2026-0002", "currency": "INR", "total": "1200.00", "payment_terms_days": 15},
        customer_id="cust-123"
    )
    assert success is True

    db = SessionLocal()
    notif = db.query(Notification).filter_by(recipient="alice@brightloop.com").first()
    assert notif is not None
    assert notif.status == "SENT"
    assert notif.attempts == 1
    assert notif.customer_id == "cust-123"
    db.close()

def test_notification_failed_send_records_error():
    service = NotificationService(smtp_host="127.0.0.1", smtp_port=9999)
    service.force_real_smtp = True
    success = service.send(
        template="payment_failed",
        to="charlie@brightloop.com",
        context={"customer_name": "Charlie", "amount": "999.00", "currency": "INR", "invoice_number": "INV-001", "error_message": "Card declined"}
    )
    assert success is False

    db = SessionLocal()
    notif = db.query(Notification).filter_by(recipient="charlie@brightloop.com").first()
    assert notif is not None
    assert notif.status == "FAILED"
    assert notif.attempts == 3
    assert notif.error is not None
    db.close()

def test_notifications_api():
    service = NotificationService(mock_send=True)
    service.send("due_reminder", "dan@brightloop.com", {"customer_name": "Dan", "invoice_number": "INV-100", "currency": "INR", "balance": "500.00", "due_date": "2026-11-01"})

    client = TestClient(app)
    response = client.get("/api/v1/notifications", headers={"x-user-role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["recipient"] == "dan@brightloop.com" for item in data["items"])
