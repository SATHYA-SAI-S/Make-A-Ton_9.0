import pytest
from app.core.security import validate_password_complexity


def test_password_policy_requirements():
    """Verify password policy: >8 chars (min 9), uppercase, lowercase, special char."""
    # Valid passwords
    assert validate_password_complexity("Strong@Pass1")[0] is True
    assert validate_password_complexity("Valid#Password99")[0] is True

    # Too short (8 chars)
    valid, msg = validate_password_complexity("Short@1a")
    assert valid is False
    assert "minimum 9" in msg

    # Missing uppercase
    valid, msg = validate_password_complexity("lowercase@123")
    assert valid is False
    assert "uppercase" in msg

    # Missing lowercase
    valid, msg = validate_password_complexity("UPPERCASE@123")
    assert valid is False
    assert "lowercase" in msg

    # Missing special character
    valid, msg = validate_password_complexity("NoSpecialChar123")
    assert valid is False
    assert "special character" in msg


def test_customer_registration_success(client):
    """Register customer with valid password and profile details."""
    payload = {
        "email": "newcustomer@example.com",
        "password": "SecurePassword123!",
        "name": "Global Tech Ltd",
        "phone": "+919988776655",
        "country": "India"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newcustomer@example.com"
    assert data["user"]["role"] == "customer"


def test_customer_registration_duplicate_email(client):
    """Case-insensitive duplicate email must be rejected."""
    payload1 = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "name": "Company One"
    }
    res1 = client.post("/api/v1/auth/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "email": "DUPLICATE@EXAMPLE.COM",
        "password": "SecurePassword123!",
        "name": "Company Two"
    }
    res2 = client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_success_and_failure(client, customer_user):
    """Verify correct credentials succeed and incorrect fail."""
    # Wrong password
    res_wrong = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "WrongPassword123!"
    })
    assert res_wrong.status_code == 401
    assert res_wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Correct password
    res_correct = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "Cust@Pass1234"
    })
    assert res_correct.status_code == 200
    data = res_correct.json()
    assert data["user"]["id"] == str(customer_user.id)


def test_forgot_and_reset_password_lifecycle(client, customer_user):
    """Verify forgot password generates reset token and reset password updates credential."""
    # Forgot password call
    res_forgot = client.post("/api/v1/auth/forgot-password", json={
        "email": customer_user.email
    })
    assert res_forgot.status_code == 200
    token = res_forgot.json().get("reset_token")
    assert token is not None

    # Reset password with new password
    res_reset = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "NewSecretPassword123!"
    })
    assert res_reset.status_code == 200

    # Old password must fail
    res_old = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "Cust@Pass1234"
    })
    assert res_old.status_code == 401

    # New password must succeed
    res_new = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "NewSecretPassword123!"
    })
    assert res_new.status_code == 200

    # Reusing reset token must fail
    res_reuse = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "AnotherPassword123!"
    })
    assert res_reuse.status_code == 422


def test_staff_management_rbac(client, admin_headers, staff_headers, customer_headers):
    """Verify Admin can create staff, but Staff and Customers cannot."""
    new_staff_payload = {
        "email": "new_operations@example.com",
        "password": "StaffPassword123!",
        "name": "Jane Staff",
        "role": "staff"
    }

    # 1. Customer cannot create staff -> 403 Forbidden
    res_cust = client.post("/api/v1/staff", json=new_staff_payload, headers=customer_headers)
    assert res_cust.status_code == 403

    # 2. Staff cannot create staff -> 403 Forbidden
    res_staff = client.post("/api/v1/staff", json=new_staff_payload, headers=staff_headers)
    assert res_staff.status_code == 403

    # 3. Unauthenticated cannot create staff -> 401 Unauthorized
    res_unauth = client.post("/api/v1/staff", json=new_staff_payload)
    assert res_unauth.status_code == 401

    # 4. Admin CAN create staff -> 201 Created
    res_admin = client.post("/api/v1/staff", json=new_staff_payload, headers=admin_headers)
    assert res_admin.status_code == 201
    staff_id = res_admin.json()["id"]

    # 5. Admin can list staff
    res_list = client.get("/api/v1/staff", headers=admin_headers)
    assert res_list.status_code == 200
    assert any(s["id"] == staff_id for s in res_list.json())

    # 6. Admin can deactivate staff
    res_patch = client.patch(f"/api/v1/staff/{staff_id}", json={"is_active": False}, headers=admin_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["is_active"] is False
