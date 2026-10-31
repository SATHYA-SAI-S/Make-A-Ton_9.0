import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.subscriptions.service import clamp_date_to_month


def test_month_end_anchor_day_clamping():
    """Verify month-end date clamping across leap and non-leap years."""
    # Jan 31 -> Feb non-leap year (2025)
    clamped_feb_non_leap = clamp_date_to_month(2025, 2, 31)
    assert clamped_feb_non_leap == date(2025, 2, 28)

    # Jan 31 -> Feb leap year (2024 or 2028)
    clamped_feb_leap = clamp_date_to_month(2028, 2, 31)
    assert clamped_feb_leap == date(2028, 2, 29)

    # Jan 31 -> April (30 days)
    clamped_apr = clamp_date_to_month(2026, 4, 31)
    assert clamped_apr == date(2026, 4, 30)

    # Jan 31 -> March (31 days, returns to full anchor day)
    clamped_mar = clamp_date_to_month(2026, 3, 31)
    assert clamped_mar == date(2026, 3, 31)


def test_quotation_to_subscription_full_flow(client, admin_headers, staff_headers):
    """
    Complete end-to-end flow:
    1. Admin creates Customer, Product + Variant, Plan.
    2. Staff creates Quotation with variant price snapshot.
    3. Staff confirms Quotation -> Subscription is created idempotently.
    4. Second confirmation returns same Subscription without duplicating.
    5. Staff activates Subscription -> next_billing_at is populated.
    6. Due billing contract returns active subscription.
    """
    today = date.today()

    # 1. Create Customer
    cust_res = client.post("/api/v1/customers", json={
        "name": "Nexus Enterprise Inc",
        "email": "nexus@example.com",
        "phone": "+919900112233",
        "country": "India"
    }, headers=admin_headers)
    assert cust_res.status_code == 201
    customer_id = cust_res.json()["id"]

    # 2. Create Product with Variant
    prod_res = client.post("/api/v1/products", json={
        "name": "Cloud Workspace",
        "type": "service",
        "sales_price": "2000.00",
        "cost_price": "750.00",
        "variants": [
            {"name": "Standard", "price_adjustment": "0.00"},
            {"name": "Odoo Pro", "price_adjustment": "560.00"}
        ]
    }, headers=admin_headers)
    assert prod_res.status_code == 201
    prod_data = prod_res.json()
    product_id = prod_data["id"]
    variant_id = prod_data["variants"][1]["id"]  # Odoo Pro (+560.00 -> 2560.00)

    # 3. Create Plan
    plan_res = client.post("/api/v1/plans", json={
        "name": "Enterprise Monthly",
        "billing_frequency": "monthly",
        "price": "5000.00",
        "min_quantity": 2,
        "available_from": today.isoformat(),
        "available_to": (today + timedelta(days=180)).isoformat(),
        "allow_pause": True,
        "allow_early_close": True,
        "allow_renewal": True,
        "status": "active"
    }, headers=admin_headers)
    assert plan_res.status_code == 201
    plan_id = plan_res.json()["id"]

    # 4. Staff creates Quotation with 2x Odoo Pro variant (Unit price 2560.00 -> 5120.00)
    quote_res = client.post("/api/v1/quotations", json={
        "customer_id": customer_id,
        "plan_id": plan_id,
        "payment_terms": "Net 30",
        "lines": [
            {
                "product_id": product_id,
                "variant_id": variant_id,
                "quantity": 2
            }
        ]
    }, headers=staff_headers)
    assert quote_res.status_code == 201
    quote_data = quote_res.json()
    quotation_id = quote_data["id"]
    assert quote_data["subtotal"] == "5120.00"
    assert quote_data["total"] == "5120.00"
    assert quote_data["lines"][0]["unit_price"] == "2560.00"

    # 5. Confirm Quotation -> Creates Subscription
    confirm_res1 = client.post(f"/api/v1/quotations/{quotation_id}/confirm", headers=staff_headers)
    assert confirm_res1.status_code == 200
    sub1 = confirm_res1.json()
    sub_id = sub1["id"]
    assert sub1["status"] == "confirmed"
    assert sub1["total_amount"] == "5120.00"

    # 6. Idempotency Check: Confirm second time returns exact same subscription
    confirm_res2 = client.post(f"/api/v1/quotations/{quotation_id}/confirm", headers=staff_headers)
    assert confirm_res2.status_code == 200
    assert confirm_res2.json()["id"] == sub_id

    # 7. Activate Subscription
    act_res = client.post(f"/api/v1/subscriptions/{sub_id}/activate", headers=staff_headers)
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "active"
    assert act_data["next_billing_at"] == today.isoformat()

    # 8. Verify Event Timeline has records
    events_res = client.get(f"/api/v1/subscriptions/{sub_id}/events", headers=staff_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 2  # confirmed + activated events

    # 9. Verify Person 2 Due Billing Endpoint
    due_res = client.get(
        f"/api/v1/internal/subscriptions/due?as_of={today.isoformat()}",
        headers={"X-Internal-Service-Key": "subscriptiq-internal-dev-key-2026"}
    )
    assert due_res.status_code == 200
    due_data = due_res.json()
    assert due_data["total_due"] >= 1
    assert any(item["subscription_id"] == sub_id for item in due_data["items"])


def test_subscription_state_machine_and_pause_resume(client, admin_headers, staff_headers):
    """Test state transitions: active -> paused -> active -> closed."""
    today = date.today()

    # Fast setup: Customer + Product + Plan
    cust_id = client.post("/api/v1/customers", json={
        "name": "Beta Corp", "email": "beta@example.com"
    }, headers=admin_headers).json()["id"]

    prod_id = client.post("/api/v1/products", json={
        "name": "Consulting Support", "sales_price": "1000.00"
    }, headers=admin_headers).json()["id"]

    plan_id = client.post("/api/v1/plans", json={
        "name": "Standard Plan", "billing_frequency": "monthly", "price": "1000.00",
        "available_from": today.isoformat(), "available_to": (today + timedelta(days=90)).isoformat(),
        "allow_pause": True, "allow_early_close": True, "allow_renewal": True
    }, headers=admin_headers).json()["id"]

    quote_id = client.post("/api/v1/quotations", json={
        "customer_id": cust_id, "plan_id": plan_id,
        "lines": [{"product_id": prod_id, "quantity": 1}]
    }, headers=staff_headers).json()["id"]

    sub_id = client.post(f"/api/v1/quotations/{quote_id}/confirm", headers=staff_headers).json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/activate", headers=staff_headers)

    # Pause
    pause_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/pause",
        json={"reason": "Customer seasonal break"},
        headers=staff_headers
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # Paused subscription must NOT appear in due billing list
    due_res = client.get(
        f"/api/v1/internal/subscriptions/due?as_of={today.isoformat()}",
        headers={"X-Internal-Service-Key": "subscriptiq-internal-dev-key-2026"}
    )
    assert not any(i["subscription_id"] == sub_id for i in due_res.json()["items"])

    # Resume
    resume_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/resume",
        json={"reason": "Customer resumed operations"},
        headers=staff_headers
    )
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "active"

    # Close
    close_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/close",
        json={"reason": "Customer requested cancellation"},
        headers=staff_headers
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"
    assert close_res.json()["next_billing_at"] is None

    # Invalid transition from closed -> active must raise 409 Conflict
    invalid_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/activate",
        headers=staff_headers
    )
    assert invalid_res.status_code == 409
    assert invalid_res.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
