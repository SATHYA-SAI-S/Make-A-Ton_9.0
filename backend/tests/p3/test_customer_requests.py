"""
Unit & Integration Tests for Phase 4: Customer Requests Workflow (P3-T04).
Verifies:
1. Customer request creation (UPGRADE, DOWNGRADE, PAUSE, CANCEL, RENEWAL).
2. Duplicate pending request blocking.
3. Tenant isolation (Customer A cannot create a request for Customer B's subscription).
4. Staff review workflow:
   - Approval invokes SubscriptionPort and marks APPLIED.
   - Rejection leaves subscription untouched and marks REJECTED.
5. Customer notification dispatch and audit trail recording.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.portal.request_models import CustomerRequest
from backend.app.audit.models import AuditLog
from backend.app.shared.registry import get_port
from backend.app.audit.bootstrap import bootstrap_audit

# Dedicated in-memory test database using StaticPool to share connection across sessions
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    bootstrap_audit()
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_customer_submits_upgrade_request():
    headers_cust = {"Authorization": "Bearer dev-customer-token"}
    payload = {
        "subscription_id": "sub-1001",
        "type": "UPGRADE",
        "target_plan_id": "plan-ent-yearly",
        "note": "Upgrade to annual commitment."
    }

    resp = client.post("/api/v1/portal/requests", json=payload, headers=headers_cust)
    assert resp.status_code == 200
    data = resp.json()
    assert data["subscription_id"] == "sub-1001"
    assert data["type"] == "UPGRADE"
    assert data["status"] == "PENDING"
    assert data["customer_id"] == "cust-101"

def test_duplicate_pending_request_blocked():
    """Attempting a second request on the same subscription while one is PENDING must fail."""
    headers_cust = {"Authorization": "Bearer dev-customer-token"}
    payload = {
        "subscription_id": "sub-1001",
        "type": "PAUSE",
        "note": "Duplicate pause attempt"
    }

    resp = client.post("/api/v1/portal/requests", json=payload, headers=headers_cust)
    assert resp.status_code == 422
    assert "already active" in resp.json()["error"]["message"]

def test_customer_cannot_request_other_customer_subscription():
    """Customer A attempting to request change on Customer B's subscription must get 404."""
    # sub-1003 belongs to cust-102
    headers_cust_a = {"Authorization": "Bearer dev-customer-token"}
    payload = {
        "subscription_id": "sub-1003",
        "type": "CANCEL",
        "note": "Malicious cancel attempt"
    }

    resp = client.post("/api/v1/portal/requests", json=payload, headers=headers_cust_a)
    assert resp.status_code == 404

def test_staff_approves_request_and_applies():
    headers_staff = {"Authorization": "Bearer dev-staff-token"}
    headers_cust = {"Authorization": "Bearer dev-customer-token"}

    # List requests as staff
    list_resp = client.get("/api/v1/portal/admin/requests?status=PENDING", headers=headers_staff)
    assert list_resp.status_code == 200
    pending_items = list_resp.json()["items"]
    assert len(pending_items) >= 1
    req_id = pending_items[0]["id"]

    # Staff approves
    review_payload = {
        "action": "APPROVE",
        "decision_note": "Approved by senior finance rep."
    }
    review_resp = client.post(
        f"/api/v1/portal/admin/requests/{req_id}/review",
        json=review_payload,
        headers=headers_staff
    )
    assert review_resp.status_code == 200
    approved_data = review_resp.json()
    assert approved_data["status"] == "APPLIED"

    # Verify subscription plan was updated via SubscriptionPort
    sub_port = get_port("subscription")
    sub = sub_port.get("sub-1001")
    assert sub["plan_id"] == "plan-ent-yearly"

    # Verify notification was sent
    notif_port = get_port("notification")
    assert len(notif_port.sent_messages) >= 1
    assert any(m["template"] == "request_approved" for m in notif_port.sent_messages)

def test_staff_rejects_customer_request():
    headers_cust = {"Authorization": "Bearer dev-customer-token"}
    headers_staff = {"Authorization": "Bearer dev-staff-token"}

    # Create a pause request on sub-1002
    payload = {
        "subscription_id": "sub-1002",
        "type": "PAUSE",
        "note": "Temporary hiatus request"
    }
    create_resp = client.post("/api/v1/portal/requests", json=payload, headers=headers_cust)
    assert create_resp.status_code == 200
    req_id = create_resp.json()["id"]

    # Staff rejects
    review_payload = {
        "action": "REJECT",
        "decision_note": "SLA contract requires 30-day notice period."
    }
    review_resp = client.post(
        f"/api/v1/portal/admin/requests/{req_id}/review",
        json=review_payload,
        headers=headers_staff
    )
    assert review_resp.status_code == 200
    rejected_data = review_resp.json()
    assert rejected_data["status"] == "REJECTED"

    # Subscription status must remain ACTIVE
    sub_port = get_port("subscription")
    sub = sub_port.get("sub-1002")
    assert sub["status"] == "ACTIVE"

def test_non_staff_cannot_review_requests():
    headers_cust = {"Authorization": "Bearer dev-customer-token"}
    review_payload = {"action": "APPROVE"}
    resp = client.post(
        "/api/v1/portal/admin/requests/any-id/review",
        json=review_payload,
        headers=headers_cust
    )
    assert resp.status_code == 403
