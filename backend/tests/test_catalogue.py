import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.catalogue.models import Product, ProductVariant
from app.catalogue.service import effective_unit_price
from app.core.errors import ValidationException


def test_effective_unit_price_calculation():
    """Verify dynamic variant price calculations and negative price prevention."""
    product = Product(sales_price=Decimal("2000.00"))

    # Standard variant (0 adjustment)
    var_std = ProductVariant(price_adjustment=Decimal("0.00"))
    assert effective_unit_price(product, var_std) == Decimal("2000.00")

    # Premium/Odoo variant (+560.00 adjustment)
    var_odoo = ProductVariant(price_adjustment=Decimal("560.00"))
    assert effective_unit_price(product, var_odoo) == Decimal("2560.00")

    # Discounted variant (-300.00 adjustment)
    var_disc = ProductVariant(price_adjustment=Decimal("-300.00"))
    assert effective_unit_price(product, var_disc) == Decimal("1700.00")

    # Excessive negative adjustment must raise ValidationException
    var_invalid = ProductVariant(price_adjustment=Decimal("-2500.00"))
    with pytest.raises(ValidationException) as exc:
        effective_unit_price(product, var_invalid)
    assert "cannot be negative" in str(exc.value)


def test_product_and_variant_api_flow(client, admin_headers, staff_headers):
    """Admin creates product with variants; staff reads; variant pricing is reflected."""
    payload = {
        "name": "Cloud ERP Suite",
        "type": "service",
        "sales_price": "2000.00",
        "cost_price": "800.00",
        "notes": "Core ERP subscription package",
        "currency": "INR",
        "variants": [
            {"name": "Standard Edition", "price_adjustment": "0.00"},
            {"name": "Odoo Pro Edition", "price_adjustment": "560.00"}
        ]
    }

    # Admin creates product
    res = client.post("/api/v1/products", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    product_id = data["id"]
    assert len(data["variants"]) == 2

    # Staff reads products
    res_list = client.get("/api/v1/products", headers=staff_headers)
    assert res_list.status_code == 200
    assert any(p["id"] == product_id for p in res_list.json())

    # Add a custom variant
    res_var = client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"name": "Enterprise Addon", "price_adjustment": "1200.00"},
        headers=admin_headers
    )
    assert res_var.status_code == 201
    assert res_var.json()["price_adjustment"] == "1200.00"


def test_plan_lifecycle_and_price_versioning(client, admin_headers):
    """Plan creation with dates and immutable price versioning."""
    today = date.today()
    plan_payload = {
        "name": "SaaS Growth Monthly",
        "billing_frequency": "monthly",
        "price": "4999.00",
        "min_quantity": 2,
        "available_from": today.isoformat(),
        "available_to": (today + timedelta(days=365)).isoformat(),
        "allow_pause": True,
        "allow_early_close": True,
        "allow_renewal": True,
        "status": "active"
    }

    # Create plan
    res = client.post("/api/v1/plans", json=plan_payload, headers=admin_headers)
    assert res.status_code == 201
    plan_data = res.json()
    plan_id = plan_data["id"]
    assert plan_data["current_price"] == "4999.00"
    assert plan_data["current_version_no"] == 1

    # Update price to 5999.00 (creates Version 2)
    res_price = client.post(
        f"/api/v1/plans/{plan_id}/price",
        json={"new_price": "5999.00"},
        headers=admin_headers
    )
    assert res_price.status_code == 201
    assert res_price.json()["version_no"] == 2
    assert res_price.json()["price"] == "5999.00"

    # Version history must have both versions intact
    res_versions = client.get(f"/api/v1/plans/{plan_id}/versions", headers=admin_headers)
    assert res_versions.status_code == 200
    vers = res_versions.json()
    assert len(vers) == 2
    assert vers[0]["version_no"] == 2 and vers[0]["price"] == "5999.00"
    assert vers[1]["version_no"] == 1 and vers[1]["price"] == "4999.00"

    # Test invalid date range (available_to < available_from)
    bad_dates = plan_payload.copy()
    bad_dates["name"] = "Bad Date Plan"
    bad_dates["available_from"] = (today + timedelta(days=30)).isoformat()
    bad_dates["available_to"] = today.isoformat()
    res_bad = client.post("/api/v1/plans", json=bad_dates, headers=admin_headers)
    assert res_bad.status_code == 422


def test_customer_isolation_and_idor(client, admin_headers, customer_headers, customer_user, db):
    """Verify Customer A cannot view Customer B's profile."""
    # Create Customer B directly as admin
    cust_b_payload = {
        "name": "Customer B Corp",
        "email": "cust_b@example.com",
        "phone": "+918888888888",
        "country": "India"
    }
    res_b = client.post("/api/v1/customers", json=cust_b_payload, headers=admin_headers)
    assert res_b.status_code == 201
    cust_b_id = res_b.json()["id"]

    # Customer A calls /customers/{cust_b_id} -> 403 Forbidden (IDOR prevented)
    res_idor = client.get(f"/api/v1/customers/{cust_b_id}", headers=customer_headers)
    assert res_idor.status_code == 403
    assert res_idor.json()["error"]["code"] == "IDOR_VIOLATION"

    # Customer A calls /customers/me -> succeeds with Customer A's own profile
    res_me = client.get("/api/v1/customers/me", headers=customer_headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == customer_user.email
