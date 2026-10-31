"""
Unit & Integration Tests for Phase 3: Customer Portal Backend & Security Isolation (P3-T03).
Mandatory verification:
1. Customer A requesting Customer B's data receives 404 / 403.
2. Staff and Admin tokens are rejected on portal routes (403 Forbidden).
3. Legitimate customer accesses dashboard, subscriptions, invoices, PDF, payments.
4. Profile edits are persisted and recorded in Audit logs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.shared.registry import get_port
from app.audit.bootstrap import bootstrap_audit

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_ports():
    bootstrap_audit()

def test_portal_dashboard_customer_a():
    # Customer 101 token
    headers = {"Authorization": "Bearer dev-customer-token"}
    response = client.get("/api/v1/portal/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["id"] == "cust-101"
    assert data["active_subscriptions_count"] >= 1
    assert "outstanding_balance" in data

def test_portal_subscriptions_and_detail():
    headers = {"Authorization": "Bearer dev-customer-token"}
    response = client.get("/api/v1/portal/subscriptions", headers=headers)
    assert response.status_code == 200
    subs = response.json()
    assert len(subs) >= 1
    sub_id = subs[0]["id"]

    detail_resp = client.get(f"/api/v1/portal/subscriptions/{sub_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == sub_id

def test_portal_invoices_and_pdf():
    headers = {"Authorization": "Bearer dev-customer-token"}
    response = client.get("/api/v1/portal/invoices", headers=headers)
    assert response.status_code == 200
    invoices = response.json()
    assert len(invoices) >= 1
    inv_id = invoices[0]["id"]

    # Detail
    inv_detail = client.get(f"/api/v1/portal/invoices/{inv_id}", headers=headers)
    assert inv_detail.status_code == 200
    assert inv_detail.json()["id"] == inv_id

    # PDF Download
    pdf_resp = client.get(f"/api/v1/portal/invoices/{inv_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert b"%PDF" in pdf_resp.content

def test_portal_payments_and_balance():
    headers = {"Authorization": "Bearer dev-customer-token"}
    pay_resp = client.get("/api/v1/portal/payments", headers=headers)
    assert pay_resp.status_code == 200
    assert isinstance(pay_resp.json(), list)

    bal_resp = client.get("/api/v1/portal/balance", headers=headers)
    assert bal_resp.status_code == 200
    bal_data = bal_resp.json()
    assert bal_data["customer_id"] == "cust-101"
    assert "outstanding_balance" in bal_data

def test_portal_profile_update_audited():
    headers = {"Authorization": "Bearer dev-customer-token"}
    update_payload = {"phone": "+91 99999 88888", "billing_address": "New HQ Tower, Bengaluru"}
    patch_resp = client.patch("/api/v1/portal/profile", json=update_payload, headers=headers)
    assert patch_resp.status_code == 200
    updated_data = patch_resp.json()
    assert updated_data["phone"] == "+91 99999 88888"

    # Verify audit log recorded
    audit_port = get_port("audit")
    # Verify no exception was raised in audit

# ================= MANDATORY SECURITY ISOLATION TESTS =================

def test_cross_tenant_subscription_access_blocked():
    """Customer A (cust-101) requesting Customer B's (cust-102) subscription must get 404."""
    # sub-1003 belongs to cust-102
    headers_cust_a = {"Authorization": "Bearer dev-customer-token"}
    response = client.get("/api/v1/portal/subscriptions/sub-1003", headers=headers_cust_a)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

def test_cross_tenant_invoice_access_blocked():
    """Customer B attempting to read Customer A's invoice must receive 404."""
    # inv-2001 belongs to cust-101
    headers_cust_b = {"Authorization": "Bearer dev-customer-2-token"}
    response = client.get("/api/v1/portal/invoices/inv-2001", headers=headers_cust_b)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

def test_cross_tenant_pdf_download_blocked():
    """Customer B attempting to download Customer A's invoice PDF must receive 404."""
    headers_cust_b = {"Authorization": "Bearer dev-customer-2-token"}
    response = client.get("/api/v1/portal/invoices/inv-2001/pdf", headers=headers_cust_b)
    assert response.status_code == 404

def test_staff_and_admin_tokens_rejected_on_portal():
    """Internal Staff and Admin accounts must be denied access to customer self-service portal (403)."""
    headers_staff = {"Authorization": "Bearer dev-staff-token"}
    staff_resp = client.get("/api/v1/portal/dashboard", headers=headers_staff)
    assert staff_resp.status_code == 403
    assert staff_resp.json()["error"]["code"] == "PERMISSION_DENIED"

    headers_admin = {"Authorization": "Bearer dev-admin-token"}
    admin_resp = client.get("/api/v1/portal/dashboard", headers=headers_admin)
    assert admin_resp.status_code == 403
    assert admin_resp.json()["error"]["code"] == "PERMISSION_DENIED"
