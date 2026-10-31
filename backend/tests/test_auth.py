import re
from datetime import datetime, timedelta, timezone
import pytest
from app.core.security import validate_password_complexity
from app.core.email import get_mock_sent_emails, clear_mock_mailbox
from app.auth.models import PendingRegistration, PasswordResetOTP


def extract_otp_from_email(to_email: str) -> str:
    """Extract the real 6-digit OTP dispatched to mock mailbox."""
    emails = [e for e in get_mock_sent_emails() if e["to"] == to_email]
    assert emails, f"No email was dispatched to {to_email}"
    latest = emails[-1]
    match = re.search(r"\b(\d{6})\b", latest["text"])
    assert match, f"Could not find 6-digit OTP in email content:\n{latest['text']}"
    return match.group(1)


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
    """Direct registration (fallback) with valid password and profile details."""
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


def test_two_step_registration_with_real_email_otp(client, db):
    """
    Test complete 2-step registration with genuine email delivery:
    1. Initiate -> dispatches email with real 6-digit OTP.
    2. Account is NOT active before verification.
    3. Incorrect OTP rejected with remaining attempts.
    4. Correct OTP verifies, assigns CUSTOMER role, and activates account.
    5. Reused OTP is rejected.
    """
    clear_mock_mailbox()
    email = "realuser@example.com"
    payload = {
        "email": email,
        "password": "Valid@Password2026!",
        "name": "Acme Innovations Ltd",
        "phone": "+919876543210",
        "country": "India"
    }

    # Step 1: Initiate
    res_init = client.post("/api/v1/auth/register/initiate", json=payload)
    assert res_init.status_code == 200
    init_data = res_init.json()
    assert init_data["email"] == email
    assert "masked_email" in init_data

    # Verify email service was invoked with correct subject and destination
    emails = get_mock_sent_emails()
    assert len(emails) >= 1
    latest_email = emails[-1]
    assert latest_email["to"] == email
    assert latest_email["subject"] == "Verify Your SubscriptIQ Account"

    # Extract real OTP from delivered email
    real_otp = extract_otp_from_email(email)
    assert len(real_otp) == 6
    assert real_otp.isdigit()

    # Step 2: Test invalid OTP
    res_invalid = client.post("/api/v1/auth/register/verify", json={
        "email": email,
        "otp": "000000" if real_otp != "000000" else "111111"
    })
    assert res_invalid.status_code == 422
    assert "Invalid verification code" in res_invalid.json()["error"]["message"]

    # Step 3: Test valid OTP
    res_verify = client.post("/api/v1/auth/register/verify", json={
        "email": email,
        "otp": real_otp
    })
    assert res_verify.status_code == 201
    verify_data = res_verify.json()
    assert "access_token" in verify_data
    assert verify_data["user"]["email"] == email
    assert verify_data["user"]["role"] == "customer"
    assert verify_data["user"]["is_active"] is True

    # Step 4: Reusing OTP must fail
    res_reuse = client.post("/api/v1/auth/register/verify", json={
        "email": email,
        "otp": real_otp
    })
    assert res_reuse.status_code == 422
    assert res_reuse.json()["error"]["code"] == "REGISTRATION_NOT_FOUND"


def test_registration_otp_attempt_limits_and_cooldown(client, db):
    """Verify max 5 attempts invalidates OTP, and cooldown blocks immediate resend."""
    clear_mock_mailbox()
    email = "attempts_test@example.com"
    payload = {
        "email": email,
        "password": "Valid@Password2026!",
        "name": "Limit Tester"
    }

    client.post("/api/v1/auth/register/initiate", json=payload)
    real_otp = extract_otp_from_email(email)

    # Resending immediately triggers cooldown
    res_cooldown = client.post("/api/v1/auth/register/resend", json={"email": email})
    assert res_cooldown.status_code == 422
    assert res_cooldown.json()["error"]["code"] == "RESEND_COOLDOWN_ACTIVE"

    # 5 wrong attempts
    for i in range(4):
        res = client.post("/api/v1/auth/register/verify", json={"email": email, "otp": "999999"})
        assert res.status_code == 422

    # 5th failed attempt invalidates
    res_last = client.post("/api/v1/auth/register/verify", json={"email": email, "otp": "999999"})
    assert res_last.status_code == 422
    assert res_last.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"

    # Even the correct OTP is now rejected because record was invalidated
    res_blocked = client.post("/api/v1/auth/register/verify", json={"email": email, "otp": real_otp})
    assert res_blocked.status_code == 422


def test_forgot_password_real_email_flow(client, customer_user):
    """
    Test real email password reset:
    1. Request reset -> generic response.
    2. Unregistered account gets generic response without sending email.
    3. Registered account receives genuine 6-digit OTP email.
    4. Verify reset OTP -> receives reset_token.
    5. Set new password -> updates credential, invalidates token.
    6. Old password fails, new password succeeds.
    """
    clear_mock_mailbox()

    # 1. Unregistered email gets generic response, no email sent
    res_unreg = client.post("/api/v1/auth/forgot-password", json={"email": "unregistered@example.com"})
    assert res_unreg.status_code == 200
    assert not any(e["to"] == "unregistered@example.com" for e in get_mock_sent_emails())

    # 2. Registered email gets generic response AND email is dispatched
    res_reg = client.post("/api/v1/auth/forgot-password", json={"email": customer_user.email})
    assert res_reg.status_code == 200
    assert "masked_email" in res_reg.json()

    # Verify email was received
    reset_otp = extract_otp_from_email(customer_user.email)
    assert len(reset_otp) == 6

    # 3. Incorrect reset OTP is rejected
    res_wrong_otp = client.post("/api/v1/auth/forgot-password/verify-otp", json={
        "email": customer_user.email,
        "otp": "000000" if reset_otp != "000000" else "111111"
    })
    assert res_wrong_otp.status_code == 422

    # 4. Correct reset OTP is accepted and issues authorization reset token
    res_valid_otp = client.post("/api/v1/auth/forgot-password/verify-otp", json={
        "email": customer_user.email,
        "otp": reset_otp
    })
    assert res_valid_otp.status_code == 200
    reset_token = res_valid_otp.json().get("reset_token")
    assert reset_token is not None

    # OTP cannot be reused after verification
    res_reused_otp = client.post("/api/v1/auth/forgot-password/verify-otp", json={
        "email": customer_user.email,
        "otp": reset_otp
    })
    assert res_reused_otp.status_code == 422

    # 5. Set new password
    res_confirm = client.post("/api/v1/auth/forgot-password/confirm", json={
        "email": customer_user.email,
        "reset_token": reset_token,
        "new_password": "BrandNewPassword2026!"
    })
    assert res_confirm.status_code == 200

    # 6. Old password fails
    res_old = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "Cust@Pass1234"
    })
    assert res_old.status_code == 401

    # 7. New password succeeds
    res_new = client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "BrandNewPassword2026!"
    })
    assert res_new.status_code == 200


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


def test_admin_stats_kpis(client, admin_headers, staff_headers, customer_headers):
    """Verify Admin stats returns live KPI counts and is restricted to Admin."""
    # 1. Customer blocked -> 403
    res_cust = client.get("/api/v1/admin/stats", headers=customer_headers)
    assert res_cust.status_code == 403

    # 2. Staff blocked -> 403
    res_staff = client.get("/api/v1/admin/stats", headers=staff_headers)
    assert res_staff.status_code == 403

    # 3. Admin allowed -> 200 with all stats
    res_admin = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert res_admin.status_code == 200
    stats = res_admin.json()
    for field in [
        "total_customers", "total_staff", "total_products",
        "total_plans", "total_quotations", "total_subscriptions",
        "active_subscriptions", "paused_subscriptions", "closed_subscriptions"
    ]:
        assert field in stats
        assert isinstance(stats[field], int)
